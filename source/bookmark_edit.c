#include "bookmark_edit.h"
int p3dBookmarkValid(const P3DBookmarkList *list,uint16_t limit){
 if(!list||!limit||list->count>P3D_BOOKMARK_CAPACITY||list->editing>1)return 0;
 for(unsigned i=0;i<list->count;i++){
  if(list->ids[i]>=limit)return 0;
  for(unsigned j=0;j<i;j++)if(list->ids[i]==list->ids[j])return 0;
 }
 return 1;
}
int p3dBookmarkAdd(P3DBookmarkList *list,uint16_t id,uint16_t limit){
 if(!p3dBookmarkValid(list,limit)||id>=limit||list->count==P3D_BOOKMARK_CAPACITY)return 0;
 for(unsigned i=0;i<list->count;i++)if(list->ids[i]==id)return 0;
 list->ids[list->count++]=id;return 1;
}
int p3dBookmarkRemoveAt(P3DBookmarkList *list,unsigned index){
 if(!list||list->count>P3D_BOOKMARK_CAPACITY||index>=list->count)return 0;
 for(unsigned i=index+1;i<list->count;i++)list->ids[i-1]=list->ids[i];
 list->ids[--list->count]=0;return 1;
}
int p3dBookmarkEditTap(P3DBookmarkList *list,unsigned index){
 return list&&list->editing==1?p3dBookmarkRemoveAt(list,index):0;
}
void p3dBookmarkSetEditing(P3DBookmarkList *list,int enabled){
 if(list)list->editing=enabled?1:0;
}
