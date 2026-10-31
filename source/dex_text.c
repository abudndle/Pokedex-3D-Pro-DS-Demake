#include "dex_text.h"
#include <stdio.h>
#include <string.h>
#include <stdint.h>
static FILE *s_file;
static int s_count;
int p3dDexTextInit(const char *path){
 unsigned char hdr[8];
 p3dDexTextClose();
 if(!path || !(s_file=fopen(path,"rb"))) return 0;
 if(fread(hdr,1,8,s_file)!=8 || memcmp(hdr,"P3DX",4) ||
    hdr[4]!=1 || hdr[5]!=0 || hdr[6]!= (P3D_NATIONAL_SPECIES_COUNT & 255) ||
    hdr[7]!=(P3D_NATIONAL_SPECIES_COUNT>>8) ||
    fseek(s_file,0,SEEK_END)!=0 ||
    ftell(s_file)!=8L+(long)P3D_NATIONAL_SPECIES_COUNT*256L) {p3dDexTextClose();return 0;}
 s_count=P3D_NATIONAL_SPECIES_COUNT;return 1;
}
int p3dDexTextRead(int national_index,P3DDexText *out){
 if(!s_file||!out||national_index<0||national_index>=s_count)return 0;
 if(fseek(s_file,8L+(long)national_index*256L,SEEK_SET))return 0;
 if(fread(out,1,256,s_file)!=256)return 0;
 out->name[31]=0;out->description[191]=0;out->height[15]=0;out->weight[15]=0;
 return 1;
}
void p3dDexTextClose(void){if(s_file){fclose(s_file);s_file=0;}s_count=0;}
