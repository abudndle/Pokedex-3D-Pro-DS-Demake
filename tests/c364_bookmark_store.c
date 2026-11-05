#include "bookmark_store.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv){
 P3DBookmarkList p={0},m={0},q={0},n={0};char file[256];FILE *f;
 assert(argc==2);
 assert(!p3dBookmarkLoad(argv[1],&q,&n));
 assert(p3dBookmarkAdd(&p,648,649)&&p3dBookmarkAdd(&m,558,559));
 assert(p3dBookmarkStore(argv[1],&p,&m));
 assert(p3dBookmarkLoad(argv[1],&q,&n)&&q.count==1&&q.ids[0]==648&&n.ids[0]==558);
 p3dBookmarkSetEditing(&p,1);assert(p3dBookmarkEditTap(&p,0));
 assert(p3dBookmarkStore(argv[1],&p,&m));
 assert(p3dBookmarkLoad(argv[1],&q,&n)&&q.count==0&&n.count==1);
 assert(snprintf(file,sizeof(file),"%s_bookmarks_B.sav",argv[1])<(int)sizeof(file));
 f=fopen(file,"r+b");assert(f);assert(fputc('X',f)!=EOF);assert(fclose(f)==0);
 assert(p3dBookmarkLoad(argv[1],&q,&n)&&q.count==1&&q.ids[0]==648);
 assert(p3dBookmarkStore(argv[1],&p,&m));
 assert(p3dBookmarkLoad(argv[1],&q,&n)&&q.count==0&&n.ids[0]==558);
 remove(file);assert(snprintf(file,sizeof(file),"%s_bookmarks_A.sav",argv[1])<(int)sizeof(file));remove(file);
 return 0;
}
