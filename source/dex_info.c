#include "dex_info.h"
#include <string.h>
int p3dDexInfoLoad(P3DDexInfo *info,int index){
 size_t length;
 if(!info)return 0;
 memset(info,0,sizeof(*info));info->index=index;info->pages=1;
 if(!p3dDexTextRead(index,&info->text))return 0;
 length=strlen(info->text.description);
 info->pages=length?(int)((length+55)/56):1;
 info->ready=1;return 1;
}
int p3dDexInfoStep(P3DDexInfo *info,int direction){
 int next;
 if(!info||!info->ready||(direction!=1&&direction!=-1))return 0;
 next=info->page+direction;
 if(next<0||next>=info->pages)return 0;
 info->page=next;return 1;
}
void p3dDexInfoLines(const P3DDexInfo *info,char first[29],char second[29]){
 size_t start,length,n;
 if(!first||!second)return;
 first[0]=second[0]=0;
 if(!info||!info->ready||info->page<0||info->page>=info->pages)return;
 start=(size_t)info->page*56;length=strlen(info->text.description);
 if(start>=length)return;
 n=length-start;if(n>28)n=28;
 memcpy(first,info->text.description+start,n);first[n]=0;
 start+=n;if(start>=length)return;
 n=length-start;if(n>28)n=28;
 memcpy(second,info->text.description+start,n);second[n]=0;
}
int p3dDexInfoTouchToggle(int x,int y){return x>=64&&x<192&&y>=160&&y<176;}
