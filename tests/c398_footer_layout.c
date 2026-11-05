#include "page_footer.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 /* These are rendered information/control rows, not footer implementation. */
 const P3DPage pages[]={P3D_PAGE_MOVES,P3D_PAGE_TYPES,P3D_PAGE_SETTINGS,
                       P3D_PAGE_RECORDS,P3D_PAGE_DEX,P3D_PAGE_SEARCH};
 const int occupied[][12]={{11,13,14,15,17,19,21,23,0},
 {11,13,15,17,20,22,0},{13,14,15,16,17,18,19,20,21,22,23,0},
 {11,13,15,17,19,21,23,0},{11,12,13,14,15,17,19,21,23,24},
 {11,12,13,14,15,17,19,21,23,24}};
 for(unsigned p=0;p<sizeof(pages)/sizeof(pages[0]);p++){
  int row=p3dPageFooterRow(pages[p]);assert(row>=0&&row<24);
  for(unsigned i=0;i<12;i++)if(row&&occupied[p][i])assert(row!=occupied[p][i]);
 }
 assert(!p3dPageFooterRow(P3D_PAGE_ALBUM));
 assert(!p3dPageFooterRow(P3D_PAGE_HOME));
 assert(!p3dPageFooterRow((P3DPage)P3D_PAGE_COUNT));
 for(unsigned mode=0;mode<P3D_RECORD_CHALLENGES;mode++){
  int row=p3dRecordScoreRow(mode);
  assert(row>=11&&row<23&&row!=p3dPageFooterRow(P3D_PAGE_RECORDS));
  if(mode)assert(row>p3dRecordScoreRow(mode-1));
 }
 assert(!p3dRecordScoreRow(P3D_RECORD_CHALLENGES));
 puts("C398 generic Back footer preserves move text, types, form and bookmark rows: PASS");
 return 0;
}
