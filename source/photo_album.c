#ifndef __NDS__
#define _POSIX_C_SOURCE 200809L
#endif
#include "photo_album.h"
#include <dirent.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
/* Never follow a host symlink for the album directory. FAT has no symlinks,
 * but this also protects desktop tooling using the same album code. */
#ifndef __NDS__
/* Inspect every existing ancestor, not just the immediate parent. */
static int host_path_has_no_symlinks(const char *path){
 char prefix[P3D_PHOTO_PATH_MAX];size_t n=strlen(path);
 struct stat st;
 if(n==0||n>=sizeof(prefix))return 0;
 for(size_t i=0;i<=n;i++){
  if(path[i]!='/'&&path[i]!='\0')continue;
  if(i==0)continue; /* absolute filesystem root */
  memcpy(prefix,path,i);prefix[i]='\0';
  if(lstat(prefix,&st)==0){
   if(!S_ISDIR(st.st_mode))return 0;
  }else if(errno!=ENOENT)return 0;
 }
 return 1;
}
#endif
static int ensure_dir(const char *path){
 struct stat st;
#ifndef __NDS__
 if(!host_path_has_no_symlinks(path))return 0;
#endif
 if(mkdir(path,0777)==0)return 1;
 if(errno!=EEXIST)return 0;
#ifdef __NDS__
 return stat(path,&st)==0&&S_ISDIR(st.st_mode);
#else
 return lstat(path,&st)==0&&S_ISDIR(st.st_mode);
#endif
}
/* Reject relative traversal components before any mkdir or deletion. */
static int safe_album_path(const char *path){
 const char *p=path;
 if(!p||!*p)return 0;
 while(*p){
  const char *begin=p;
  while(*p&&*p!='/')p++;
  size_t n=(size_t)(p-begin);
  if((n==1&&begin[0]=='.')||(n==2&&begin[0]=='.'&&begin[1]=='.'))return 0;
  if(*p)p++;
 }
 return 1;
}
static int valid_name(const char *s){
 if(!s||strlen(s)!=11||strncmp(s,"AR_",3)||strcmp(s+7,".png"))return 0;
 for(int i=3;i<7;i++)if(s[i]<'0'||s[i]>'9')return 0;
 return 1;
}
/* FAT has no symlink support; host tests use lstat to reject symlinked
 * candidates rather than counting them as genuine saved AR photos. */
static int regular_photo(const char *folder,const char *name){
 char path[P3D_PHOTO_PATH_MAX+16];struct stat st;
 int n=snprintf(path,sizeof(path),"%s/%s",folder,name);
 if(n<=0||(size_t)n>=sizeof(path))return 0;
#ifdef __NDS__
 if(stat(path,&st)!=0)return 0;
#else
 if(lstat(path,&st)!=0)return 0;
#endif
 return S_ISREG(st.st_mode);
}
int p3dPhotoAlbumOpen(P3DPhotoAlbum *a,const char *folder){
 char parent[P3D_PHOTO_PATH_MAX],*slash;size_t n;
 if(!a)return 0;
 /* Copy first, so a caller may safely reopen using its own folder field.
  * A failed mount/path must never leave the previous SD folder deletable. */
 if(!folder||(n=strlen(folder))==0||n>=sizeof(a->folder)||!safe_album_path(folder)){
   a->folder[0]=0;return 0;
 }
 memcpy(parent,folder,n+1);
 a->folder[0]=0;
 slash=strrchr(parent,'/');
 if(!slash||slash==parent||!slash[1])return 0;
 *slash=0;
 if(!ensure_dir(parent))return 0;
 *slash='/';
 if(!ensure_dir(parent))return 0;
 memcpy(a->folder,parent,n+1);return 1;
}
/* AR_0000.png..AR_9999.png are a finite namespace. Index one FAT
 * directory pass in 1250 bytes rather than repeatedly rewinding the
 * directory for each skipped photo (quadratic for deep pages). */
size_t p3dPhotoAlbumPage(const P3DPhotoAlbum *a,char names[][32],size_t limit,size_t offset,size_t *total){
 unsigned char present[1250]={0};
 DIR *d;struct dirent *e;size_t count=0,filled=0,rank=0;
 if(total)*total=0;
 if(limit>P3D_ALBUM_PAGE_MAX)limit=P3D_ALBUM_PAGE_MAX;
 if(!a||!a->folder[0]||(limit&&!names)||(d=opendir(a->folder))==NULL)return 0;
 while((e=readdir(d))!=NULL){
  int id;
  if(!valid_name(e->d_name)||!regular_photo(a->folder,e->d_name))continue;
  id=(e->d_name[3]-'0')*1000+(e->d_name[4]-'0')*100+
     (e->d_name[5]-'0')*10+(e->d_name[6]-'0');
  if(!(present[id>>3]&(1u<<(id&7)))){
   present[id>>3]|=(unsigned char)(1u<<(id&7));
   count++;
  }
 }
 closedir(d);
 if(total)*total=count;
 if(!limit||offset>=count)return 0;
 for(int id=9999;id>=0&&filled<limit;id--){
  if(!(present[id>>3]&(1u<<(id&7))))continue;
  if(rank++<offset)continue;
  (void)snprintf(names[filled++],32,"AR_%04d.png",id);
 }
 return filled;
}
int p3dPhotoAlbumDelete(P3DPhotoAlbum *a,const char *name){
 char path[P3D_PHOTO_PATH_MAX+16];int n;
 if(!a||!a->folder[0]||!valid_name(name)||!regular_photo(a->folder,name))return 0;
 n=snprintf(path,sizeof(path),"%s/%s",a->folder,name);
 return n>0&&(size_t)n<sizeof(path)&&remove(path)==0;
}
