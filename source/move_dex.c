/* Seekable original-ROM-derived Move Dex, designed for DS memory limits. */
#include "move_dex.h"
#include <stdio.h>
#include <string.h>
static char s_path[176];static int s_count;static uint32_t s_index[P3D_MOVE_COUNT+1];static uint32_t s_file_size;
static uint16_t le16(const unsigned char *p){return (uint16_t)((unsigned)p[0]|((unsigned)p[1]<<8));}
static uint32_t le32(const unsigned char *p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
int p3dMoveDexInit(const char *path){
 FILE *f;unsigned char hdr[8],u32[4];size_t i;long n;
 s_count=0;s_path[0]=0;s_file_size=0;
 if(!path||strlen(path)>=sizeof(s_path))return 0;
 f=fopen(path,"rb");if(!f)return 0;
 if(fread(hdr,1,8,f)!=8||memcmp(hdr,"P3DM",4)!=0||le16(hdr+4)!=1||le16(hdr+6)!=P3D_MOVE_COUNT){fclose(f);return 0;}
 for(i=0;i<P3D_MOVE_COUNT+1;i++){if(fread(u32,1,4,f)!=4){fclose(f);return 0;}s_index[i]=le32(u32);}
 if(fseek(f,0,SEEK_END)!=0||(n=ftell(f))<0){fclose(f);return 0;}
 fclose(f);
 if(s_index[0]!=8+4*(P3D_MOVE_COUNT+1)||s_index[P3D_MOVE_COUNT]!=(uint32_t)n)return 0;
 for(i=0;i<P3D_MOVE_COUNT;i++)if(s_index[i+1]<=s_index[i]+6||s_index[i+1]-s_index[i]>2048)return 0;
 strcpy(s_path,path);s_file_size=(uint32_t)n;s_count=P3D_MOVE_COUNT;return 1;
}
int p3dMoveDexCount(void){return s_count;}
int p3dMoveDexRead(int index,P3DMove *out){
 FILE *f;unsigned char buf[2048];unsigned int a,b,c,size;
 if(!out||s_count!=P3D_MOVE_COUNT||index<0||index>=s_count)return 0;
 size=s_index[index+1]-s_index[index];
 if(size>sizeof(buf)||s_index[index+1]>s_file_size)return 0;
 f=fopen(s_path,"rb");if(!f)return 0;
 if(fseek(f,(long)s_index[index],SEEK_SET)!=0||fread(buf,1,size,f)!=size){fclose(f);return 0;}
 fclose(f);a=le16(buf);b=le16(buf+2);c=le16(buf+4);
 if(a==0||a>=sizeof(out->name)||b>=sizeof(out->description)||c>=sizeof(out->effect)||(unsigned)(a+b+c+6)!=size)return 0;
 memset(out,0,sizeof(*out));out->id=(uint16_t)(index+1);
 memcpy(out->name,buf+6,a);memcpy(out->description,buf+6+a,b);memcpy(out->effect,buf+6+a+b,c);return 1;
}
int p3dMoveDexFindInitial(int start,char initial,int direction){
 P3DMove m;int i,idx;
 if(s_count!=P3D_MOVE_COUNT||(direction!=1&&direction!=-1))return -1;
 if(initial>='a'&&initial<='z')initial=(char)(initial-32);
 for(i=1;i<=s_count;i++){idx=(start+direction*i+s_count*(i+2))%s_count;
 if(p3dMoveDexRead(idx,&m)){char c=m.name[0];if(c>='a'&&c<='z')c=(char)(c-32);if(c==initial)return idx;}}
 return -1;
}
