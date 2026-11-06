#include "species_details.h"
#include <stdio.h>
#include <string.h>

static uint16_t read16(const unsigned char *p){
 return (uint16_t)((unsigned)p[0]|((unsigned)p[1]<<8));
}
static uint32_t read32(const unsigned char *p){
 return (uint32_t)read16(p)|((uint32_t)read16(p+2)<<16);
}
static uint32_t crc32(const unsigned char *p,unsigned length){
 uint32_t c=0xffffffffu;
 for(unsigned i=0;i<length;i++){
   c^=p[i];
   for(int bit=0;bit<8;bit++)c=(c>>1)^((c&1u)?0xedb88320u:0);
 }
 return ~c;
}
void p3dSpeciesDetailsClear(P3DSpeciesDetails *d){if(d)memset(d,0,sizeof(*d));}
int p3dSpeciesDetailsValid(const P3DSpeciesDetails *d){
 if(!d||d->species>=P3D_DETAIL_NATIONAL_SPECIES ||
    d->form>P3D_DETAIL_MAX_FORM ||
    !d->fields || (d->fields & ~(P3D_DETAIL_STATS|P3D_DETAIL_ABILITIES|
                                  P3D_DETAIL_EVOLUTIONS|P3D_DETAIL_MOVES)) ||
    d->abilities_count>3||d->evolutions_count>2||d->moves_count>4)return 0;
 for(int i=0;i<6;i++)
   if(((d->fields&P3D_DETAIL_STATS)!=0)!=(d->stats[i]!=0))return 0;
 if(!(d->fields&P3D_DETAIL_ABILITIES)&&d->abilities_count)return 0;
 if(!(d->fields&P3D_DETAIL_EVOLUTIONS)&&d->evolutions_count)return 0;
 if(!(d->fields&P3D_DETAIL_MOVES)&&d->moves_count)return 0;
 for(int i=0;i<3;i++){
   if(i<d->abilities_count){
      if(d->ability_ids[i]==0)return 0;
      for(int j=0;j<i;j++)if(d->ability_ids[i]==d->ability_ids[j])return 0;
   }else if(d->ability_ids[i])return 0;
 }
 for(int i=0;i<2;i++){
   if(i<d->evolutions_count){
      if(d->evolutions[i]>=P3D_DETAIL_NATIONAL_SPECIES||
         d->evolutions[i]==d->species)return 0;
      for(int j=0;j<i;j++)if(d->evolutions[i]==d->evolutions[j])return 0;
   }else if(d->evolutions[i])return 0;
 }
 for(int i=0;i<4;i++){
   if(i<d->moves_count){
     if(d->move_indices[i]>=P3D_DETAIL_MOVE_INDEX_COUNT)return 0;
     for(int j=0;j<i;j++)if(d->move_indices[i]==d->move_indices[j])return 0;
   }else if(d->move_indices[i])return 0;
 }
 return 1;
}
int p3dSpeciesDetailPath(char path[80],int species,int form){
 int length;
 if(!path || species<0||species>=P3D_DETAIL_NATIONAL_SPECIES ||
    form<0||form>P3D_DETAIL_MAX_FORM)return 0;
 length=snprintf(path,80,"nitro:/details/s%03d-f%03d.p3sd",species,form);
 return length>0&&length<80;
}
int p3dSpeciesDetailsLoad(const char *path,int species,int form,P3DSpeciesDetails *out){
 unsigned char b[P3D_DETAIL_RECORD_SIZE];
 P3DSpeciesDetails candidate;
 FILE *f;
 int ok;
 if(!out)return 0;
 p3dSpeciesDetailsClear(out);
 if(!path||!*path||species<0||species>=P3D_DETAIL_NATIONAL_SPECIES||
    form<0||form>P3D_DETAIL_MAX_FORM)return 0;
 f=fopen(path,"rb");if(!f)return 0;
 ok=fread(b,1,sizeof(b),f)==sizeof(b) && fgetc(f)==EOF && !ferror(f);
 if(fclose(f)!=0)ok=0;
 if(!ok || memcmp(b,"P3SD",4)!=0 || b[4]!=1 ||
    read32(b+60)!=crc32(b,60) ||
    b[13]!=0 || b[38]!=0 || b[39]!=0)return 0;
 for(int i=40;i<60;i++)if(b[i]!=0)return 0;
 p3dSpeciesDetailsClear(&candidate);
 candidate.fields=b[5];candidate.species=read16(b+6);
 candidate.form=read16(b+8);
 candidate.abilities_count=b[10];candidate.evolutions_count=b[11];
 candidate.moves_count=b[12];
 memcpy(candidate.stats,b+14,6);
 for(int i=0;i<3;i++)candidate.ability_ids[i]=read16(b+20+i*2);
 for(int i=0;i<2;i++)candidate.evolutions[i]=read16(b+26+i*2);
 for(int i=0;i<4;i++)candidate.move_indices[i]=read16(b+30+i*2);
 if(candidate.species!=(uint16_t)species || candidate.form!=(uint16_t)form ||
    !p3dSpeciesDetailsValid(&candidate))return 0;
 *out=candidate;
 return 1;
}
const char *p3dSpeciesDetailTabName(int tab){
 switch(tab){
 case 1:return "STATS";
 case 2:return "ABILITIES";
 case 3:return "EVOLUTIONS";
 case 4:return "LEARNSET";
 default:return "ENTRY";
 }
}
int p3dSpeciesEvolutionTouch(const P3DSpeciesDetails *details,int x,int y,
                               int *species,int *selected_species,int *form){
 if(!species||!selected_species||!form||form==species||form==selected_species||
    !p3dSpeciesDetailsValid(details)||
    !(details->fields&P3D_DETAIL_EVOLUTIONS)||
    details->species!=*species||details->form!=*form||
    x<0||x>=256||y<P3D_EVOLUTION_ROW_TOP||
    y>=P3D_EVOLUTION_ROW_TOP+P3D_EVOLUTION_ROW_STEP*details->evolutions_count)
    return 0;
 unsigned row=(unsigned)(y-P3D_EVOLUTION_ROW_TOP)/P3D_EVOLUTION_ROW_STEP;
 int target=details->evolutions[row];
 *species=target;*selected_species=target;*form=0;
 return 1;
}
