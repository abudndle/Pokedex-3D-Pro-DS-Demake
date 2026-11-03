#include "species_details.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint32_t crc(const unsigned char *b,unsigned n){
 uint32_t c=0xffffffffu;
 for(unsigned i=0;i<n;i++){c^=b[i];for(int j=0;j<8;j++)c=(c>>1)^((c&1u)?0xedb88320u:0);}
 return ~c;
}
static void u16(unsigned char *b,unsigned n){b[0]=(unsigned char)n;b[1]=(unsigned char)(n>>8);}
static void u32(unsigned char *b,uint32_t n){u16(b,n);u16(b+2,n>>16);}
static void put(const char *path,const unsigned char *b,unsigned n){
 FILE *f=fopen(path,"wb");assert(f);assert(fwrite(b,1,n,f)==n);assert(fclose(f)==0);
}
static void fixture(unsigned char b[64]){
 memset(b,0,64);memcpy(b,"P3SD",4);b[4]=1;b[5]=15;
 u16(b+6,25);u16(b+8,0);b[10]=2;b[11]=2;b[12]=3;
 const unsigned stats[6]={35,55,40,50,50,90};
 for(int i=0;i<6;i++)b[14+i]=(unsigned char)stats[i];
 u16(b+20,31);u16(b+22,79);
 u16(b+26,26);u16(b+28,27);
 u16(b+30,1);u16(b+32,3);u16(b+34,558);
 u32(b+60,crc(b,60));
}
static void strict_test(const char *path){
 unsigned char b[65],raw[64];P3DSpeciesDetails details;
 fixture(b);put(path,b,64);
 assert(p3dSpeciesDetailsLoad(path,25,0,&details));
 assert(details.species==25&&details.form==0);
 assert(details.fields==15&&details.stats[5]==90);
 assert(details.abilities_count==2&&details.ability_ids[1]==79);
 assert(details.evolutions_count==2&&details.evolutions[1]==27);
 assert(details.moves_count==3&&details.move_indices[2]==558);
 assert(!p3dSpeciesDetailsLoad(path,24,0,&details));
 assert(!details.fields);
 assert(!p3dSpeciesDetailsLoad(path,25,1,&details));
 assert(!details.fields);
 /* Success never leaks from a prior record into failed loads. */
 assert(!p3dSpeciesDetailsLoad("missing-c333-originals.p3sd",25,0,&details));
 assert(!details.fields);
 memcpy(raw,b,64);
 put(path,b,63);assert(!p3dSpeciesDetailsLoad(path,25,0,&details));
 put(path,b,65);assert(!p3dSpeciesDetailsLoad(path,25,0,&details));
 b[14]^=1;put(path,b,64);assert(!p3dSpeciesDetailsLoad(path,25,0,&details));b[14]^=1;
 #define INVALID(stmt) do{stmt;u32(b+60,crc(b,60));put(path,b,64);assert(!p3dSpeciesDetailsLoad(path,25,0,&details));memcpy(b,raw,64);}while(0)
 INVALID(b[5]=16); /* unknown source field bits */
 INVALID(b[13]=1); /* reserved */
 INVALID(b[37]=1); /* unpopulated move must be zero */
 INVALID(b[59]=1); /* reserved */
 INVALID(b[14]=0); /* impossible stat */
 INVALID(b[10]=4); /* more than 3 abilities */
 INVALID(b[11]=3); /* more than 2 evolutions */
 INVALID(b[12]=5); /* more than 4 moves */
 INVALID(u16(b+20,0)); /* empty ability ID */
 INVALID(u16(b+26,649)); /* invalid target species */
 INVALID(u16(b+30,559)); /* invalid move index */
 INVALID(u16(b+32,1)); /* duplicate move */
 INVALID(u16(b+28,26)); /* duplicate evolution */
 INVALID(u16(b+26,25)); /* self evolution */
 INVALID(u16(b+8,1000)); /* invalid form identity */
 INVALID(u16(b+6,649)); /* invalid national species */
 INVALID(b[5]=0); /* missing fields must have canonical zero payload */
 b[5]=1;b[10]=b[11]=b[12]=0;
 memset(b+20,0,18);u32(b+60,crc(b,60));put(path,b,64);
 assert(p3dSpeciesDetailsLoad(path,25,0,&details));
 assert(details.fields==1&&details.abilities_count==0&&details.moves_count==0);
 fixture(b);u16(b+8,2);u32(b+60,crc(b,60));put(path,b,64);
 assert(p3dSpeciesDetailsLoad(path,25,2,&details));
 assert(!p3dSpeciesDetailsLoad(path,25,0,&details));
 assert(!p3dSpeciesDetailsLoad(path,-1,2,&details));
 assert(!p3dSpeciesDetailsLoad(path,25,1000,&details));
}
int main(int argc,char **argv){
 assert(argc==2);
 strict_test(argv[1]);
 assert(strcmp(p3dSpeciesDetailTabName(1),"STATS")==0);
 assert(strcmp(p3dSpeciesDetailTabName(4),"LEARNSET")==0);
 puts("C333: bounded original-source species/form stats, ability ID, evolutions and 559 Move Dex references: PASS (synthetic)");
 return 0;
}
