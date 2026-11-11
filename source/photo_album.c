#ifndef __NDS__
#define _POSIX_C_SOURCE 200809L
#endif
#include "photo_album.h"
#include <dirent.h>
#include <errno.h>
#ifndef __NDS__
#include <fcntl.h>
#include <unistd.h>
#endif
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
#define ALBUM_INDEX_BYTES ((P3D_PHOTO_ID_COUNT+7u)/8u)
static int album_index(const P3DPhotoAlbum *a,unsigned char present[ALBUM_INDEX_BYTES],size_t *total){
 DIR *d;struct dirent *e;size_t count=0;int ok=1;
 memset(present,0,ALBUM_INDEX_BYTES);*total=0;
 if(!a||!a->folder[0])return 0;
#ifndef __NDS__
 /* The album directory can change after Open; never enumerate a replaced
  * symlink or one of its ancestors in host-side album tooling. */
 if(!host_path_has_no_symlinks(a->folder))return 0;
#endif
 if((d=opendir(a->folder))==NULL)return 0;
 for(;;){
  errno=0;e=readdir(d);
  if(!e){if(errno)ok=0;break;}
  int id;
  if(!valid_name(e->d_name)||!regular_photo(a->folder,e->d_name))continue;
  id=(e->d_name[3]-'0')*1000+(e->d_name[4]-'0')*100+
     (e->d_name[5]-'0')*10+(e->d_name[6]-'0');
  if(!(present[id>>3]&(1u<<(id&7)))){
   present[id>>3]|=(unsigned char)(1u<<(id&7));
   count++;
  }
 }
 if(closedir(d)!=0)ok=0;
 if(!ok)return 0;
 *total=count;return 1;
}
size_t p3dPhotoAlbumPage(const P3DPhotoAlbum *a,char names[][32],size_t limit,size_t offset,size_t *total){
 unsigned char present[ALBUM_INDEX_BYTES];size_t count=0,filled=0,rank=0;
 if(total)*total=0;
 if(limit>P3D_ALBUM_PAGE_MAX)limit=P3D_ALBUM_PAGE_MAX;
 if((limit&&!names)||!album_index(a,present,&count))return 0;
 if(total)*total=count;
 if(!limit||offset>=count)return 0;
 for(int id=9999;id>=0&&filled<limit;id--){
  if(!(present[id>>3]&(1u<<(id&7))))continue;
  if(rank++<offset)continue;
  (void)snprintf(names[filled++],32,"AR_%04d.png",id);
 }
 return filled;
}
int p3dPhotoAlbumLocate(const P3DPhotoAlbum *a,unsigned photo_id,size_t *offset,size_t *selected){
 unsigned char present[ALBUM_INDEX_BYTES];size_t total=0,rank=0;
 if(!offset||!selected||photo_id>=P3D_PHOTO_ID_COUNT||
    !album_index(a,present,&total)||!(present[photo_id>>3]&(1u<<(photo_id&7))))return 0;
 for(unsigned id=photo_id+1;id<P3D_PHOTO_ID_COUNT;id++)
  if(present[id>>3]&(1u<<(id&7)))rank++;
 *offset=(rank/P3D_ALBUM_PAGE_MAX)*P3D_ALBUM_PAGE_MAX;
 *selected=rank%P3D_ALBUM_PAGE_MAX;
 return 1;
}
FILE *p3dPhotoAlbumRead(const P3DPhotoAlbum *a,const char *name){
 if(!a||!a->folder[0]||!valid_name(name))return NULL;
#ifndef __NDS__
 if(!host_path_has_no_symlinks(a->folder))return NULL;
 int dir=open(a->folder,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
 if(dir<0)return NULL;
 int fd=openat(dir,name,O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
 close(dir);
 if(fd<0)return NULL;
 struct stat st;
 if(fstat(fd,&st)!=0||!S_ISREG(st.st_mode)){close(fd);return NULL;}
 FILE *f=fdopen(fd,"rb");
 if(!f)close(fd);
 return f;
#else
 char path[P3D_PHOTO_PATH_MAX+16];
 if(!regular_photo(a->folder,name))return NULL;
 int n=snprintf(path,sizeof(path),"%s/%s",a->folder,name);
 return n>0&&(size_t)n<sizeof(path)?fopen(path,"rb"):NULL;
#endif
}
int p3dPhotoAlbumDelete(P3DPhotoAlbum *a,const char *name){
#ifdef __NDS__
 char path[P3D_PHOTO_PATH_MAX+16];int n;
#endif
 if(!a||!a->folder[0]||!valid_name(name))return 0;
#ifndef __NDS__
 /* Reject a directory replaced with a symlink after album open. */
 if(!host_path_has_no_symlinks(a->folder))return 0;
#endif
#ifndef __NDS__
 /* Pin the checked directory while inspecting and removing the entry.
  * A swapped filename cannot redirect unlinkat outside this directory.
  * This does not make the earlier ancestor check race-free: a full
  * component-by-component openat walk is still required for that. */
 int fd=open(a->folder,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
 struct stat st;
 int ok=0;
 if(fd<0)return 0;
 if(fstatat(fd,name,&st,AT_SYMLINK_NOFOLLOW)==0&&S_ISREG(st.st_mode))
  ok=unlinkat(fd,name,0)==0;
 close(fd);
 return ok;
#else
 if(!regular_photo(a->folder,name))return 0;
 n=snprintf(path,sizeof(path),"%s/%s",a->folder,name);
 return n>0&&(size_t)n<sizeof(path)&&remove(path)==0;
#endif
}
int p3dPhotoAlbumConfirmDelete(P3DPhotoAlbum *album,const char *requested,const char *selected){
 if(!valid_name(requested)||!selected||strcmp(requested,selected)!=0)return 0;
 return p3dPhotoAlbumDelete(album,requested);
}
void p3dPhotoAlbumClampSelection(size_t total,size_t *offset,size_t *selected){
 if(!offset||!selected||offset==selected)return;
 if(!total){
  *offset=0;
  *selected=0;
  return;
 }
 if(*offset>=total){
  size_t last=total-1;
  *offset=last/P3D_ALBUM_PAGE_MAX*P3D_ALBUM_PAGE_MAX;
  *selected=last%P3D_ALBUM_PAGE_MAX;
  return;
 }
 size_t shown=total-*offset;
 if(shown>P3D_ALBUM_PAGE_MAX)shown=P3D_ALBUM_PAGE_MAX;
 if(*selected>=shown)*selected=shown-1;
}
