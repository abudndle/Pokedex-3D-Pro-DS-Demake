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
 /* A saved cursor may be any signed int, including INT_MIN. Normalize
  * before adding a step; never add to the untrusted cursor directly. */
 const int count=P3D_NATIONAL_SPECIES_COUNT;
 int cursor=start%count;
 if(cursor<0)cursor+=count;
 for(int n=0;n<count;n++){
  cursor=direction>0?(cursor+1==count?0:cursor+1):
                     (cursor==0?count-1:cursor-1);
  if(p3dDexTextRead(cursor,&t)&&p3dDexPrefixMatches(t.name,query))
   return cursor;
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

/* C231: a prior numeric selection is not necessarily in the currently
 * filtered original text catalog, especially after removing a favorite. */
int p3dDexSelectionMatches(const char *query,int index,int field,int region,
                           int scope,const P3DRecords *records,const P3DMenu *menu){
 int first,last;
 P3DDexText entry;
 if(!query||(field!=P3D_DEX_SEARCH_NAME&&field!=P3D_DEX_SEARCH_DESCRIPTION)||
    scope<0||scope>=P3D_DEX_SCOPE_COUNT||
    !p3dDexRegionBounds(region,&first,&last)||
    index<first||index>last)return 0;
 if(scope==P3D_DEX_SCOPE_VIEWED&&(!records||!p3dRecordsSeen(records,index)))return 0;
 if(scope==P3D_DEX_SCOPE_FAVORITES&&(!menu||!p3dFavoriteContains(menu,index)))return 0;
 if(!p3dDexTextRead(index,&entry))return 0;
 return !*query || (field==P3D_DEX_SEARCH_NAME?
        p3dDexPrefixMatches(entry.name,query):
        p3dDexContains(entry.description,query));
}
int p3dDexRefreshSelection(const char *query,int *selection,int field,
                           int region,int scope,const P3DRecords *records,
                           const P3DMenu *menu){
 int hit;
 if(!selection)return 0;
 if(p3dDexSelectionMatches(query,*selection,field,region,scope,records,menu))return 1;
 hit=p3dDexFindScoped(query,*selection,1,field,region,scope,records,menu);
 if(hit<0)return 0;
 *selection=hit;
 return 1;
}
int p3dDexKeypadSelection(const char *query,int selection,int delta,int field,int region,int scope,
                         const P3DRecords *records,const P3DMenu *menu){
 if(!query||!delta)return selection;
 if(!*query&&field==P3D_DEX_SEARCH_NAME&&region==0&&scope==P3D_DEX_SCOPE_ALL){
  int64_t next=(int64_t)selection+delta;
  if(next<0)return 0;
  if(next>=P3D_NATIONAL_SPECIES_COUNT)return P3D_NATIONAL_SPECIES_COUNT-1;
  return (int)next;
 }
 int hit=p3dDexFindScoped(query,selection,delta>0?1:-1,field,region,scope,records,menu);
 return hit<0?selection:hit;
}
