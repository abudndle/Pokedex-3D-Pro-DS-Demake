#include "page_footer.h"
int p3dPageFooterRow(P3DPage page){
 if((unsigned)page>=P3D_PAGE_COUNT)return 0;
 switch(page){
 case P3D_PAGE_HOME:case P3D_PAGE_DEX:case P3D_PAGE_SEARCH:case P3D_PAGE_ALBUM:return 0;
 default:return 24;
 }
}
