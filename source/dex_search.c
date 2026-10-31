#include "dex_search.h"
#include "dex_text.h"
#include <string.h>
static int up(int c){return c>='a'&&c<='z'?c-'a'+'A':c;}
int p3dDexPrefixMatches(const char *name,const char *prefix){
 if(!name||!prefix||!*prefix)return 0;
 while(*prefix){if(!*name||up((unsigned char)*name++)!=up((unsigned char)*prefix++))return 0;}
 return 1;
}
int p3dDexFindPrefix(const char *query,int start,int direction){
 P3DDexText t;
 if(!query||!*query||!direction)return -1;
 start%=P3D_NATIONAL_SPECIES_COUNT;
 if(start<0)start+=P3D_NATIONAL_SPECIES_COUNT;
 for(int n=0;n<P3D_NATIONAL_SPECIES_COUNT;n++){
  int i=(start+(direction>0?n+1:-(n+1))+P3D_NATIONAL_SPECIES_COUNT*3)%P3D_NATIONAL_SPECIES_COUNT;
  if(p3dDexTextRead(i,&t)&&p3dDexPrefixMatches(t.name,query))return i;
 }
 return -1;
}
int p3dDexQueryAppend(char query[13],char ch){
 size_t n;if(!query||ch<'A'||ch>'Z')return 0;
 for(n=0;n<13 && query[n];n++){}
 if(n>=12)return 0;
 query[n]=ch;query[n+1]=0;return 1;
}
void p3dDexQueryBackspace(char query[13]){size_t n;if(!query)return;for(n=0;n<13 && query[n];n++){}
 if(n&&n<13)query[n-1]=0;}

/* 8 columns of 32px keys, four 16px rows, starting at y=104.
 * Last row includes backspace and clear; zero denotes no key. */
int p3dDexSearchTouchKey(int x,int y){
 static const char keys[]="ABCDEFGH" "IJKLMNOP" "QRSTUVWX" "YZ";
 int key;
 if(x<0||x>=256||y<104||y>=168)return 0;
 key=((y-104)/16)*8+x/32;
 if(key<26)return keys[key];
 if(key==26)return 8;
 if(key==27)return 127;
 return 0;
}
