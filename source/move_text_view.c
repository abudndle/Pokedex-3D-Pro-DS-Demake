#include "move_text_view.h"
#include <stddef.h>
const char *p3dMoveTextField(const P3DMove *entry,int field){
    if(!entry)return 0;
    if(field==P3D_MOVE_FIELD_DESCRIPTION)return entry->description;
    if(field==P3D_MOVE_FIELD_EFFECT)return entry->effect;
    return 0;
}
int p3dMoveTextScroll(int current,const char *text,int direction){
    size_t length=0;
    int last;
    if(!text)return 0;
    /* Each P3DMove source field is fixed-size. Avoid reading beyond a
     * malformed, unterminated original record when scrolling. */
    while(length<P3D_MOVE_TEXT_MAX && text[length])++length;
    last=length>84u?(int)(length-84u):0;
    if(current<0)current=0;
    if(current>last)current=last;
    if(direction<0)return current>=28?current-28:0;
    if(direction>0)return current>last-28?last:current+28;
    return current;
}
/* Select a bounded Move Dex entry and reset its text viewport together.
 * Returns 1 only on a changed selection; rejected/no-change calls preserve both.
 * The two outputs must be distinct objects. */
int p3dMoveNavigateSelect(int *index,int *text_offset,int target){
    if(!index||!text_offset||index==text_offset||target<0||target>=P3D_MOVE_COUNT||*index==target)return 0;
    *index=target;
    *text_offset=0;
    return 1;
}
