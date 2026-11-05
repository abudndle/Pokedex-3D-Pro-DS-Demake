#include "bookmark_session.h"
#include "bookmark_store.h"
void p3dBookmarkSessionLoadReset(P3DBookmarkSettings *s);
int p3dBookmarkSessionLoad(P3DBookmarkSettings *s,const char *base){
 if(!s)return 0;
 p3dBookmarkSettingsInit(s);
 return p3dBookmarkLoad(base,&s->pokemon,&s->moves);
}
int p3dBookmarkSessionFlush(P3DBookmarkSettings *s,const char *base){
 if(!s)return 0;
 if(!s->dirty)return 1;
 if(!p3dBookmarkStore(base,&s->pokemon,&s->moves))return 0;
 s->dirty=0;return 1;
}
int p3dBookmarkSessionAdd(P3DBookmarkSettings *s,const char *base,
                          unsigned list,unsigned id){
 P3DBookmarkList *target;
 if(!s||list>1)return 0;
 target=list?&s->moves:&s->pokemon;
 if(id>65535u||!p3dBookmarkAdd(target,(uint16_t)id,list?559:649))return 0;
 s->dirty=1;
 return p3dBookmarkSessionFlush(s,base);
}
int p3dBookmarkSessionSelect(P3DBookmarkSettings *s,P3DMenu *menu,
                             const char *base,unsigned slot){
 int result=p3dBookmarkSettingsSelect(s,menu,slot);
 if(result==2&&!p3dBookmarkSessionFlush(s,base))return -1;
 return result;
}
