#include "save_store.h"
#include <stdio.h>
#include <string.h>
#define SAVE_SIZE 64
#define SAVE_VERSION 1
static void put16(unsigned char *b,unsigned v){b[0]=(unsigned char)v;b[1]=(unsigned char)(v>>8);}
static unsigned get16(const unsigned char *b){return (unsigned)b[0]|((unsigned)b[1]<<8);}
static void put32(unsigned char *b,uint32_t v){for(int i=0;i<4;i++)b[i]=(unsigned char)(v>>(8*i));}
static uint32_t get32(const unsigned char *b){return (uint32_t)b[0]|((uint32_t)b[1]<<8)|((uint32_t)b[2]<<16)|((uint32_t)b[3]<<24);}
static uint32_t crc32buf(const unsigned char *data,size_t size){uint32_t c=~0u;for(size_t i=0;i<size;i++){c^=data[i];for(int b=0;b<8;b++)c=(c>>1)^((c&1u)?0xEDB88320u:0u);}return ~c;}
int p3dSaveStateValid(const P3DSaveState *s){
 if(!s||s->selected_model>=P3D_SAVE_MODEL_LIMIT||s->move_index>=559||s->favorite_count>P3D_SAVE_FAVORITES||s->backdrop>3||s->rotate>1||s->challenge_correct>s->challenge_total||s->challenge_total>100000000u)return 0;
 for(unsigned i=0;i<s->favorite_count;i++){if(s->favorites[i]>=P3D_SAVE_MODEL_LIMIT)return 0;for(unsigned j=0;j<i;j++)if(s->favorites[i]==s->favorites[j])return 0;}return 1;
}
static void encode(unsigned char b[SAVE_SIZE],const P3DSaveState *s,uint32_t seq){
 memset(b,0,SAVE_SIZE);memcpy(b,"P3SV",4);b[4]=SAVE_VERSION;
 put32(b+8,seq);put16(b+12,s->selected_model);put16(b+14,s->move_index);b[16]=s->favorite_count;b[17]=s->backdrop;b[18]=s->rotate;
 for(int i=0;i<P3D_SAVE_FAVORITES;i++)put16(b+20+i*2,s->favorites[i]);
 put32(b+32,s->challenge_correct);put32(b+36,s->challenge_total);put32(b+60,crc32buf(b,60));
}
static int decode(const unsigned char b[SAVE_SIZE],P3DSaveState *s,uint32_t *seq){
 if(memcmp(b,"P3SV",4)||b[4]!=SAVE_VERSION||get32(b+60)!=crc32buf(b,60))return 0;
 memset(s,0,sizeof(*s));*seq=get32(b+8);s->selected_model=(uint16_t)get16(b+12);s->move_index=(uint16_t)get16(b+14);
 s->favorite_count=b[16];s->backdrop=b[17];s->rotate=b[18];for(int i=0;i<P3D_SAVE_FAVORITES;i++)s->favorites[i]=(uint16_t)get16(b+20+i*2);
 s->challenge_correct=get32(b+32);s->challenge_total=get32(b+36);return p3dSaveStateValid(s);
}
static int slotpath(char out[256],const char *base,int slot){if(!base||!*base)return 0;int n=snprintf(out,256,"%s_%c.sav",base,slot?'B':'A');return n>0&&n<256;}
static int readslot(const char *base,int slot,P3DSaveState *s,uint32_t *seq){
 char path[256];unsigned char b[SAVE_SIZE];FILE *f;int ok;
 if(!slotpath(path,base,slot)||(f=fopen(path,"rb"))==NULL)return 0;
 ok=fread(b,1,SAVE_SIZE,f)==SAVE_SIZE&&fgetc(f)==EOF;fclose(f);return ok&&decode(b,s,seq);
}
static int newer(uint32_t a,uint32_t b){return (int32_t)(a-b)>0;}
int p3dSaveLoad(const char *base,P3DSaveState *out){
 P3DSaveState a,b;uint32_t sa=0,sb=0;int va,vb;if(!out)return 0;
 va=readslot(base,0,&a,&sa);vb=readslot(base,1,&b,&sb);if(!va&&!vb)return 0;
 *out=va&&(!vb||!newer(sb,sa))?a:b;return 1;
}
int p3dSaveStore(const char *base,const P3DSaveState *s){
 P3DSaveState a,b;uint32_t sa=0,sb=0,next=1;int va,vb,slot;unsigned char buf[SAVE_SIZE];char path[256];FILE *f;
 if(!p3dSaveStateValid(s)) return 0;
 va=readslot(base,0,&a,&sa);
 vb=readslot(base,1,&b,&sb);
 if(va&&vb){int cur=newer(sb,sa)?1:0;slot=1-cur;next=(cur?sb:sa)+1;}
 else if(va){slot=1;next=sa+1;}else if(vb){slot=0;next=sb+1;}else slot=0;
 if(!slotpath(path,base,slot)) return 0;
 encode(buf,s,next);
 f=fopen(path,"wb");
 if(!f) return 0;
 if(fwrite(buf,1,SAVE_SIZE,f)!=SAVE_SIZE){fclose(f);return 0;}
 if(fflush(f)!=0){fclose(f);return 0;}return fclose(f)==0;
}
