#include "bookmark_store.h"
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#define SLOT_BYTES 80
static void put16(unsigned char *p,unsigned v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);}
static unsigned get16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
static void put32(unsigned char *p,uint32_t v){for(int i=0;i<4;i++)p[i]=(unsigned char)(v>>(i*8));}
static uint32_t get32(const unsigned char *p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static uint32_t crc(const unsigned char *p,unsigned n){uint32_t c=~0u;for(unsigned i=0;i<n;i++){c^=p[i];for(int j=0;j<8;j++)c=(c>>1)^((c&1u)?0xedb88320u:0u);}return ~c;}
static int path(char p[256],const char *base,int slot){int n;if(!base||!*base)return 0;n=snprintf(p,256,"%s_bookmarks_%c.sav",base,slot?'B':'A');return n>0&&n<256;}
static int decode(const unsigned char b[SLOT_BYTES],P3DBookmarkList *p,P3DBookmarkList *m,uint32_t *seq){
 if(memcmp(b,"P3BK",4)||b[4]!=1||b[5]!=0||b[6]>16||b[7]>16||get32(b+76)!=crc(b,76))return 0;
 P3DBookmarkList a={0},z={0};a.count=b[6];z.count=b[7];
 for(unsigned i=0;i<16;i++){a.ids[i]=(uint16_t)get16(b+12+i*2);z.ids[i]=(uint16_t)get16(b+44+i*2);if((i>=a.count&&a.ids[i])||(i>=z.count&&z.ids[i]))return 0;}
 if(!p3dBookmarkValid(&a,649)||!p3dBookmarkValid(&z,559))return 0;
 *seq=get32(b+8);*p=a;*m=z;return 1;
}
static int readslot(const char *base,int slot,P3DBookmarkList *p,P3DBookmarkList *m,uint32_t *seq){
 char name[256];unsigned char b[SLOT_BYTES];FILE *f;int ok;
 if(!path(name,base,slot)||(f=fopen(name,"rb"))==NULL)return 0;
 ok=fread(b,1,sizeof(b),f)==sizeof(b)&&fgetc(f)==EOF&&!ferror(f);
 if(fclose(f)!=0)ok=0;
 return ok&&decode(b,p,m,seq);
}
static int newer(uint32_t a,uint32_t b){uint32_t d=a-b;return d!=0&&d<0x80000000u;}
int p3dBookmarkLoad(const char *base,P3DBookmarkList *p,P3DBookmarkList *m){
 P3DBookmarkList a,b,c,d;uint32_t sa=0,sb=0;int va,vb;
 if(!p||!m||p==m)return 0;
 va=readslot(base,0,&a,&b,&sa);vb=readslot(base,1,&c,&d,&sb);
 if(!va&&!vb)return 0;
 if(va&&(!vb||!newer(sb,sa))){*p=a;*m=b;}else{*p=c;*m=d;}return 1;
}
int p3dBookmarkStore(const char *base,const P3DBookmarkList *p,const P3DBookmarkList *m){
 P3DBookmarkList a,b,c,d;uint32_t sa=0,sb=0,seq=1;int va,vb,slot;
 unsigned char bytes[SLOT_BYTES]={0};char name[256];FILE *f;
 if(!p3dBookmarkValid(p,649)||!p3dBookmarkValid(m,559))return 0;
 va=readslot(base,0,&a,&b,&sa);vb=readslot(base,1,&c,&d,&sb);
 if(va&&vb){int newest=newer(sb,sa)?1:0;slot=1-newest;seq=(newest?sb:sa)+1;}
 else if(va){slot=1;seq=sa+1;}else if(vb){slot=0;seq=sb+1;}else slot=0;
 if(!path(name,base,slot))return 0;
 memcpy(bytes,"P3BK",4);bytes[4]=1;bytes[6]=p->count;bytes[7]=m->count;put32(bytes+8,seq);
 for(unsigned i=0;i<p->count;i++)put16(bytes+12+i*2,p->ids[i]);
 for(unsigned i=0;i<m->count;i++)put16(bytes+44+i*2,m->ids[i]);
 put32(bytes+76,crc(bytes,76));
 f=fopen(name,"wb");if(!f)return 0;
 if(fwrite(bytes,1,sizeof(bytes),f)!=sizeof(bytes)){fclose(f);return 0;}
 if(fflush(f)!=0){fclose(f);return 0;}return fclose(f)==0;
}
