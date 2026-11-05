#include "page_footer.h"
int p3dPageFooterRow(P3DPage page){
 if((unsigned)page>=P3D_PAGE_COUNT)return 0;
 switch(page){
 case P3D_PAGE_HOME:case P3D_PAGE_DEX:case P3D_PAGE_SEARCH:case P3D_PAGE_ALBUM:return 0;
 case P3D_PAGE_MOVES:case P3D_PAGE_RECORDS:case P3D_PAGE_CHALLENGE:return 22;
 case P3D_PAGE_TYPES:return 23;
 case P3D_PAGE_SETTINGS:return 12;
 default:return 17;
 }
}
int p3dRecordScoreRow(unsigned mode){return mode<P3D_RECORD_CHALLENGES?13+(int)mode:0;}
