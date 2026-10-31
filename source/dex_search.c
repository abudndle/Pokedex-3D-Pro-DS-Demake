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

static const char *s_region_names[P3D_DEX_REGIONS]={"NATIONAL","KANTO","JOHTO","HOENN","SINNOH","UNOVA"};
static const int s_first[P3D_DEX_REGIONS]={0,0,151,251,386,493};
static const int s_last[P3D_DEX_REGIONS]={648,150,250,385,492,648};
const char *p3dDexRegionName(int region){
 return region>=0&&region<P3D_DEX_REGIONS?s_region_names[region]:"UNKNOWN";
}
const char *p3dDexScopeName(int scope){
 static const char *const names[]={"ALL","VIEWED","FAVORITES"};
 return scope>=0&&scope<P3D_DEX_SCOPE_COUNT?names[scope]:"UNKNOWN";
}
int p3dDexRegionBounds(int region,int *first,int *last){
 if(region<0||region>=P3D_DEX_REGIONS)return 0;
 if(first)*first=s_first[region];
 if(last)*last=s_last[region];
 return 1;
}
int p3dDexContains(const char *text,const char *query){
 size_t i,j,len;
 if(!text||!query||!*query)return 0;
 len=strlen(query);
 for(i=0;text[i];i++){
  for(j=0;j<len&&text[i+j]&&up((unsigned char)text[i+j])==up((unsigned char)query[j]);j++){}
  if(j==len)return 1;
 }
 return 0;
}
int p3dDexFindScoped(const char *query,int start,int direction,int field,int region,int scope,const P3DRecords *records,const P3DMenu *menu){
 int first,last,index,count,i;
 P3DDexText entry;
 if(!query||(direction!=1&&direction!=-1)||
    (field!=P3D_DEX_SEARCH_NAME&&field!=P3D_DEX_SEARCH_DESCRIPTION)||
    scope<0||scope>=P3D_DEX_SCOPE_COUNT||
    !p3dDexRegionBounds(region,&first,&last)||
    (scope==P3D_DEX_SCOPE_VIEWED&&!records)||
    (scope==P3D_DEX_SCOPE_FAVORITES&&!menu))return -1;
 count=last-first+1;
 index=start<first||start>last?(direction>0?last:first):start;
 for(i=0;i<count;i++){
  index+=direction;
  if(index>last)index=first;
  if(index<first)index=last;
  if(scope==P3D_DEX_SCOPE_VIEWED&&!p3dRecordsSeen(records,index))continue;
  if(scope==P3D_DEX_SCOPE_FAVORITES&&!p3dFavoriteContains(menu,index))continue;
  if(!p3dDexTextRead(index,&entry))return -1;
  if(!*query || (field==P3D_DEX_SEARCH_NAME?
      p3dDexPrefixMatches(entry.name,query):p3dDexContains(entry.description,query)))return index;
 }
 return -1;
}
int p3dDexFindFiltered(const char *query,int start,int direction,int field,int region){
 if(!query||!*query)return -1;
 return p3dDexFindScoped(query,start,direction,field,region,P3D_DEX_SCOPE_ALL,0,0);
}
