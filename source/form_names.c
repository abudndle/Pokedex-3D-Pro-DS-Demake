#include "form_names.h"
#include <stdio.h>
#include <string.h>
static unsigned rd16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
int p3dFormNamesLoad(P3DFormNames *names,const char *path){
    unsigned char h[8],raw[28];
    FILE *f;
    P3DFormNames tmp={0};
    if(!names)return 0;
    names->ready=0;
    if(!path)return 0;
    f=fopen(path,"rb");if(!f)return 0;
    if(fread(h,1,8,f)!=8||memcmp(h,"P3FN",4)!=0||rd16(h+4)!=1||
       rd16(h+6)>P3D_FORM_LABELS_MAX){fclose(f);return 0;}
    tmp.count=rd16(h+6);
    for(unsigned i=0;i<tmp.count;i++){
        if(fread(raw,1,28,f)!=28){fclose(f);return 0;}
        P3DFormLabel *e=&tmp.entries[i];
        e->species=(uint16_t)rd16(raw);
        e->form=(uint16_t)rd16(raw+2);
        memcpy(e->label,raw+4,P3D_FORM_NAME_BYTES);
        if(e->species>=649||!e->form||e->label[0]==0||
           !memchr(e->label,0,P3D_FORM_NAME_BYTES)){fclose(f);return 0;}
        for(unsigned j=0;e->label[j];j++)
            if((unsigned char)e->label[j]<32||(unsigned char)e->label[j]>126){
                fclose(f);return 0;
            }
        if(i && (tmp.entries[i-1].species>e->species||
           (tmp.entries[i-1].species==e->species&&tmp.entries[i-1].form>=e->form))){
            fclose(f);return 0;
        }
    }
    if(fgetc(f)!=EOF){fclose(f);return 0;}
    fclose(f);tmp.ready=1;*names=tmp;return 1;
}
const char *p3dFormName(const P3DFormNames *names,int species,int form){
    if(!names||!names->ready||species<0||species>=649||form<=0)return NULL;
    for(unsigned i=0;i<names->count;i++){
        if(names->entries[i].species==species&&names->entries[i].form==form)
            return names->entries[i].label;
        if(names->entries[i].species>species)break;
    }
    return NULL;
}
