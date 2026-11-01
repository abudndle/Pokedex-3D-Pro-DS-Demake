#include "move_text_view.h"
#include <string.h>
const char *p3dMoveTextField(const P3DMove *entry,int field){
    if(!entry)return 0;
    if(field==P3D_MOVE_FIELD_DESCRIPTION)return entry->description;
    if(field==P3D_MOVE_FIELD_EFFECT)return entry->effect;
    return 0;
}
int p3dMoveTextScroll(int current,const char *text,int direction){
    size_t length;
    int last;
    if(!text)return 0;
    length=strlen(text);
    last=length>84u?(int)(length-84u):0;
    if(current<0)current=0;
    if(current>last)current=last;
    if(direction<0)return current>=28?current-28:0;
    if(direction>0)return current>last-28?last:current+28;
    return current;
}
