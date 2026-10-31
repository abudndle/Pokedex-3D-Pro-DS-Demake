#include "species_model_map.h"
#include <stdio.h>
#include <string.h>
/* P3SM v1: magic(4), version LE16(1), count LE16(649), 649 LE16 resource IDs.
   0xffff indicates genuinely unavailable; every other ID must be <738. */
int p3dModelMapLoad(P3DModelMap *map, const char *path){
    unsigned char head[8], pair[2];
    FILE *f;
    uint16_t parsed[P3D_SPECIES_COUNT];
    if(!map)return 0;
    map->ready=0;
    if(!path)return 0;
    f=fopen(path,"rb");
    if(!f)return 0;
    if(fread(head,1,8,f)!=8 || memcmp(head,"P3SM",4)!=0 ||
       head[4]!=1 || head[5]!=0 || head[6]!=(P3D_SPECIES_COUNT&255) ||
       head[7]!=(P3D_SPECIES_COUNT>>8)){fclose(f);return 0;}
    for(int i=0;i<P3D_SPECIES_COUNT;i++){
        if(fread(pair,1,2,f)!=2){fclose(f);return 0;}
        parsed[i]=(uint16_t)(pair[0]|((unsigned)pair[1]<<8));
        if(parsed[i]>=P3D_RESOURCE_COUNT && parsed[i]!=P3D_MODEL_UNAVAILABLE){
            fclose(f);return 0;
        }
    }
    if(fgetc(f)!=EOF){fclose(f);return 0;}
    fclose(f);
    memcpy(map->resource,parsed,sizeof(parsed));
    map->ready=1;
    return 1;
}
int p3dModelMapResolve(const P3DModelMap *map,int species_index){
    if(!map||!map->ready||species_index<0||species_index>=P3D_SPECIES_COUNT)return -1;
    return map->resource[species_index]==P3D_MODEL_UNAVAILABLE?-1:map->resource[species_index];
}
