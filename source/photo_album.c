#include "photo_album.h"
#include <dirent.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
static int ensure_dir(const char *path){struct stat st;if(mkdir(path,0777)==0)return 1;return errno==EEXIST&&stat(path,&st)==0&&S_ISDIR(st.st_mode);}
static int valid_name(const char *s){
 if(!s||strlen(s)!=11||strncmp(s,"AR_",3)||strcmp(s+7,".png"))return 0;
 for(int i=3;i<7;i++)if(s[i]<'0'||s[i]>'9')return 0;
 return 1;
}
int p3dPhotoAlbumOpen(P3DPhotoAlbum *a,const char *folder){
 char parent[P3D_PHOTO_PATH_MAX],*slash;size_t n;
 if(!a)return 0;
 /* Copy first, so a caller may safely reopen using its own folder field.
  * A failed mount/path must never leave the previous SD folder deletable. */
 if(!folder||(n=strlen(folder))==0||n>=sizeof(a->folder)){
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
size_t p3dPhotoAlbumPage(const P3DPhotoAlbum *a,char names[][32],size_t limit,size_t offset,size_t *total){
 DIR *d;struct dirent *e;size_t count=0,filled=0;
 if(total)*total=0;
 /* Bound the output to the actual seven visible DS album slots. */
 if(limit>P3D_ALBUM_PAGE_MAX)limit=P3D_ALBUM_PAGE_MAX;
 if(!a||!a->folder[0]||(limit&&!names)||(d=opendir(a->folder))==NULL)return 0;
 while((e=readdir(d))!=NULL)if(valid_name(e->d_name))count++;
 if(total)*total=count;
 if(!limit||offset>=count){closedir(d);return 0;}
 /* Avoid offset+limit wraparound when an invalid save supplies SIZE_MAX. */
 size_t end=limit>count-offset?count:offset+limit;
 char prev[32]="AR_9999.png";
 for(size_t index=0;index<end;index++){
  char best[32]="";
  rewinddir(d);
  while((e=readdir(d))!=NULL){
   if(valid_name(e->d_name)&&strcmp(e->d_name,prev)<0&&strcmp(e->d_name,best)>0)
    memcpy(best,e->d_name,12);
  }
  if(!best[0])break;
  memcpy(prev,best,12);
  if(index>=offset&&filled<limit)memcpy(names[filled++],best,12);
 }
 closedir(d);return filled;
}
int p3dPhotoAlbumDelete(P3DPhotoAlbum *a,const char *name){
 char path[P3D_PHOTO_PATH_MAX+16];int n;
 if(!a||!a->folder[0]||!valid_name(name))return 0;
 n=snprintf(path,sizeof(path),"%s/%s",a->folder,name);
 return n>0&&(size_t)n<sizeof(path)&&remove(path)==0;
}
