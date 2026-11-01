#include "original_track_binding.h"
#include <string.h>
int p3dOriginalTrackBind(const P3DOriginalSkeleton *rig,
                         const P3DOriginalTrackOwner *owners,
                         unsigned count,uint16_t *resolved){
    unsigned char seen[P3D_SKELETON_MAX_NODES]={0};
    /* Reject impossible counts before touching an unknown caller buffer.
     * For all valid bounded counts, failure leaves every slot unbound. */
    if(count>P3D_SKELETON_MAX_NODES)return 0;
    if(resolved){
        for(unsigned i=0;i<count;i++)resolved[i]=0xffffu;
    }
    if(!rig||!rig->ready||rig->node_count==0||
       rig->node_count>P3D_SKELETON_MAX_NODES||
       count>rig->node_count||(!owners&&count)||(!resolved&&count))return 0;
    /* First pass validates all source references without publishing any
     * partial binding. C148/C150 establish exact source node identity. */
    for(unsigned i=0;i<count;i++){
        unsigned id=owners[i].source_node_index;
        const char *name=owners[i].source_node_name;
        if(id>=rig->node_count||seen[id]||!name||
           p3dOriginalSkeletonFindNode(rig,name)!=(int)id)return 0;
        seen[id]=1;
    }
    for(unsigned i=0;i<count;i++)resolved[i]=owners[i].source_node_index;
    return 1;
}
