/* Host-compiled exact native C P3SK loader regression; NO original assets. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "original_skeleton.h"
static P3DOriginalSkeleton s;
static int test_single(const char *path,unsigned model,int expected){
    int ok=p3dOriginalSkeletonLoad(&s,path,model);
    if(ok!=expected){fprintf(stderr,"unexpected skeleton load status for %s expected=%d got=%d\n",path,expected,ok);return 1;}
    if(!ok){if(s.ready||s.node_count||s.root_count)return 1;return 0;}
    if(!s.ready||s.model_id!=model||!s.node_count||!s.root_count)return 1;
    for(unsigned i=0;i<s.node_count;i++){
        const char *name=p3dOriginalSkeletonName(&s,i);
        int parent=p3dOriginalSkeletonParent(&s,i);
        if(!name||!name[0]||!p3dOriginalSkeletonMatrixBytes(&s,i))return 1;
        if(parent>=0 && parent>=(int)i)return 1;
    }
    return 0;
}
int main(int argc,char **argv){
    if(argc==5 && strcmp(argv[1],"--single")==0){
        unsigned model=(unsigned)strtoul(argv[3],NULL,0);
        int expected=atoi(argv[4]);
        if(test_single(argv[2],model,expected))return 1;
        puts("C149 native single skeleton: PASS");return 0;
    }
    if(argc!=5||strcmp(argv[1],"--all")!=0){
        fprintf(stderr,"usage: %s --all SKELETON_DIR NODES ROOTS | --single P3SK MODEL OK\n",argv[0]);
        return 2;
    }
    unsigned expected_nodes=(unsigned)strtoul(argv[3],NULL,0);
    unsigned expected_roots=(unsigned)strtoul(argv[4],NULL,0);
    unsigned nodes=0,roots=0,loaded=0;
    for(unsigned id=0;id<=733;id++){
        if(id>=721&&id<=724)continue;
        char path[512];
        int n=snprintf(path,sizeof(path),"%s/p%03u.p3sk",argv[2],id);
        if(n<0||(unsigned)n>=sizeof(path))return 1;
        if(test_single(path,id,1))return 1;
        nodes+=s.node_count;roots+=s.root_count;loaded++;
    }
    if(loaded!=730||nodes!=expected_nodes||roots!=expected_roots){
        fprintf(stderr,"unexpected original source skeleton coverage loaded=%u nodes=%u roots=%u\n",loaded,nodes,roots);
        return 1;
    }
    printf("C149 native original P3SK loader: PASS models=%u nodes=%u roots=%u\n",loaded,nodes,roots);
    return 0;
}