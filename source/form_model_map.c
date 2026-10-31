#include "form_model_map.h"
#include <stdio.h>
#include <string.h>
static unsigned get16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
int p3dFormMapLoad(P3DFormMap *map,const char *path){
    unsigned char h[8],e[6];
    FILE *f;
    P3DFormMap tmp={0};
    if(!map)return 0;
    map->ready=0;
    if(!path)return 0;
    f=fopen(path,"rb");if(!f)return 0;
    if(fread(h,1,8,f)!=8||memcmp(h,"P3FM",4)!=0||get16(h+4)!=1||
       get16(h+6)>P3D_MAX_FORM_ENTRIES){fclose(f);return 0;}
    tmp.count=get16(h+6);
    for(unsigned i=0;i<tmp.count;i++){
        if(fread(e,1,6,f)!=6){fclose(f);return 0;}
        tmp.entries[i].species=(uint16_t)get16(e);
        tmp.entries[i].form=(uint16_t)get16(e+2);
        tmp.entries[i].resource=(uint16_t)get16(e+4);
        if(tmp.entries[i].species>=649||tmp.entries[i].form==0||
           tmp.entries[i].resource>=738){fclose(f);return 0;}
        if(i && (tmp.entries[i-1].species>tmp.entries[i].species||
           (tmp.entries[i-1].species==tmp.entries[i].species &&
            tmp.entries[i-1].form>=tmp.entries[i].form))){fclose(f);return 0;}
    }
    if(fgetc(f)!=EOF){fclose(f);return 0;}
    fclose(f);tmp.ready=1;*map=tmp;return 1;
}
int p3dFormResolve(const P3DFormMap *map,int species,int form){
    if(!map||!map->ready||species<0||species>=649||form<=0)return -1;
    for(unsigned i=0;i<map->count;i++){
        if(map->entries[i].species==species && map->entries[i].form==form)
            return map->entries[i].resource;
        if(map->entries[i].species>species)break;
    }
    return -1;
}
int p3dFormNext(const P3DFormMap *map,int species,int current_form){
    if(!map||!map->ready||species<0||species>=649)return 0;
    int first=0;
    for(unsigned i=0;i<map->count;i++){
        P3DFormEntry e=map->entries[i];
        if(e.species<species)continue;
        if(e.species>species)break;
        if(!first)first=e.form;
        if(e.form>current_form)return e.form;
    }
    return current_form>0?0:first;
}
