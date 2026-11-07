#include "dex_description.h"
#include <string.h>
void p3dDescriptionClear(P3DDescription *d){if(d)memset(d,0,sizeof(*d));}
static uint32_t source_crc(const char *source,unsigned length){
 uint32_t crc=0xffffffffu;
 for(unsigned i=0;i<length;i++){
  crc^=(unsigned char)source[i];
  for(unsigned bit=0;bit<8;bit++)crc=(crc>>1)^((crc&1u)?0xedb88320u:0);
 }
 return ~crc;
}
int p3dDescriptionSet(P3DDescription *d,const char *source){
 P3DDescription next;unsigned length=0,used=0,start=0;
 if(!d)return 0;
 if(!source){p3dDescriptionClear(d);return 0;}
 while(length<P3D_DESCRIPTION_BYTES&&source[length])length++;
 if(!length||length>=P3D_DESCRIPTION_BYTES){p3dDescriptionClear(d);return 0;}
 p3dDescriptionClear(&next);next.checksum=source_crc(source,length);
 for(unsigned i=0;i<length;i++){
  unsigned char ch=(unsigned char)source[i];
  if(ch<=32||ch==127){
   if(used&&next.text[used-1]!=' ')next.text[used++]=' ';
  }else next.text[used++]=(char)ch;
 }
 if(used&&next.text[used-1]==' ')next.text[--used]=0;
 if(!used){p3dDescriptionClear(d);return 0;}
 while(start<used){
  unsigned end=start+P3D_DESCRIPTION_LINE_WIDTH;
  if(end>used)end=used;
  if(end<used&&next.text[end]!=' '){
   unsigned split=end;
   while(split>start&&next.text[split]!=' ')split--;
   if(split>start)end=split;
  }
  next.offsets[next.count]=(uint8_t)start;
  next.lengths[next.count++]=(uint8_t)(end-start);
  start=end;
  while(start<used&&next.text[start]==' ')start++;
 }
 next.ready=1;*d=next;return 1;
}
unsigned p3dDescriptionPages(const P3DDescription *d){
 return d&&d->ready&&d->count&&d->count<P3D_DESCRIPTION_BYTES?
  (d->count+P3D_DESCRIPTION_LINES_PER_PAGE-1)/P3D_DESCRIPTION_LINES_PER_PAGE:0;
}
int p3dDescriptionLine(const P3DDescription *d,unsigned relative_line,char out[29]){
 unsigned index,offset,length;
 if(!out)return 0;
 out[0]=0;
 if(!p3dDescriptionPages(d)||d->page>=p3dDescriptionPages(d)||
    relative_line>=P3D_DESCRIPTION_LINES_PER_PAGE)return 0;
 index=d->page*P3D_DESCRIPTION_LINES_PER_PAGE+relative_line;
 if(index>=d->count)return 0;
 offset=d->offsets[index];length=d->lengths[index];
 if(!length||length>P3D_DESCRIPTION_LINE_WIDTH||offset+length>=P3D_DESCRIPTION_BYTES)return 0;
 memcpy(out,d->text+offset,length);out[length]=0;return 1;
}
int p3dDescriptionStep(P3DDescription *d,int direction){
 unsigned pages=p3dDescriptionPages(d);
 if(!pages)return 0;
 if(direction<0&&d->page){d->page--;return 1;}
 if(direction>0&&(unsigned)d->page+1<pages){d->page++;return 1;}
 return 0;
}
int p3dDescriptionTouch(P3DDescription *d,int visible,int x,int y){
 if(!p3dDescriptionPages(d)||!visible||x<8||x>=248||
    y<P3D_DESCRIPTION_CONTROL_ROW*8||y>=(P3D_DESCRIPTION_CONTROL_ROW+1)*8)return 0;
 (void)p3dDescriptionStep(d,x<128?-1:1);return 1;
}
int p3dDescriptionRestore(P3DDescription *d,int valid,unsigned page,uint32_t checksum){
 if(!d)return 0;
 d->page=0;
 if(valid!=1||!p3dDescriptionPages(d)||checksum!=d->checksum||page>=p3dDescriptionPages(d))return 0;
 d->page=(uint8_t)page;return 1;
}
