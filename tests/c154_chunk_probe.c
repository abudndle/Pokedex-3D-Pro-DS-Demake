/* C154: exact real native P3CS loader/probe, original files are LOCAL only.
 * No copyrighted model data or assumptions about texture bindings in source.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "preview_chunk_stream.h"

static int16_t xyz[P3D_CHUNK_TRIANGLES*9];
static int16_t uv[P3D_CHUNK_TRIANGLES*6];
static unsigned char rgb[P3D_CHUNK_TRIANGLES*3];
static uint16_t rd16(const unsigned char *p){return (uint16_t)((unsigned)p[0]|(unsigned)p[1]<<8);}
static uint32_t rd32(const unsigned char *p){return (uint32_t)rd16(p)|((uint32_t)rd16(p+2)<<16);}

static int verify(const char *path,unsigned model,unsigned *nchunks,unsigned *nfaces){
    P3DChunkStream stream={0};
    FILE *source=NULL;
    unsigned char header[24];
    if(!p3dChunkOpen(&stream,path,model)){
        fprintf(stderr,"C154: source native chunk loader rejected model %u path=%s\n",model,path);
        return 0;
    }
    source=fopen(path,"rb");
    if(!source || fread(header,1,sizeof(header),source)!=sizeof(header) ||
       memcmp(header,"P3CS",4)!=0 || rd16(header+6)!=model ||
       stream.chunk_count!=rd16(header+8) ||
       stream.total_triangles!=rd32(header+12) ||
       stream.original_triangles!=rd32(header+16))goto fail;
    for(unsigned chunk=0;chunk<stream.chunk_count;chunk++){
        const P3DChunkInfo *info=&stream.chunks[chunk];
        if(!p3dChunkRead(&stream,chunk,xyz,uv,rgb))goto fail;
        if(fseek(source,(long)info->offset,SEEK_SET)!=0)goto fail;
        for(unsigned t=0;t<info->triangles;t++){
            unsigned char b[P3D_CHUNK_RECORD_BYTES];
            if(fread(b,1,sizeof(b),source)!=sizeof(b))goto fail;
            for(unsigned j=0;j<9;j++)
                if(xyz[t*9+j]!=(int16_t)rd16(b+j*2))goto fail;
            for(unsigned j=0;j<6;j++)
                if(uv[t*6+j]!=(int16_t)rd16(b+18+j*2))goto fail;
            for(unsigned j=0;j<3;j++)
                if(rgb[t*3+j]!=b[30+j])goto fail;
        }
    }
    *nchunks+=stream.chunk_count;
    *nfaces+=stream.total_triangles;
    fclose(source);
    p3dChunkClose(&stream);
    return 1;
fail:
    fprintf(stderr,"C154: decoded XYZ/UV/RGB mismatch or invalid source chunk p%03u\n",model);
    if(source)fclose(source);
    p3dChunkClose(&stream);
    return 0;
}
int main(int argc,char **argv){
    if(argc!=6 || strcmp(argv[1],"--all")){
        fprintf(stderr,"usage: %s --all DIRECTORY EXPECTED_MODELS EXPECTED_CHUNKS EXPECTED_FACES\n",argv[0]);
        return 2;
    }
    char *end=NULL;
    unsigned long want_models=strtoul(argv[3],&end,10);
    if(!end || *end) return 2;
    unsigned long want_chunks=strtoul(argv[4],&end,10);
    if(!end || *end) return 2;
    unsigned long want_faces=strtoul(argv[5],&end,10);
    if(!end || *end) return 2;
    unsigned models=0,chunks=0,triangles=0;
    for(unsigned model=0;model<738;model++){
        char path[1024];
        int n=snprintf(path,sizeof(path),"%s/p%03u.p3cs",argv[2],model);
        if(n<0 || (size_t)n>=sizeof(path))return 2;
        FILE *probe=fopen(path,"rb");
        if(!probe)continue;
        fclose(probe);
        if(!verify(path,model,&chunks,&triangles))return 1;
        models++;
    }
    if(models!=want_models || chunks!=want_chunks || triangles!=want_faces){
        fprintf(stderr,"C154: coverage differs: models=%u/%lu chunks=%u/%lu triangles=%u/%lu\n",
                models,want_models,chunks,want_chunks,triangles,want_faces);
        return 1;
    }
    printf("C154 original P3CS native loader PASS models=%u chunks=%u triangles=%u XYZ/UV/RGB exact\n",
           models,chunks,triangles);
    return 0;
}