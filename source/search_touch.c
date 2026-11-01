#include "search_touch.h"
int p3dSearchTouchAction(int x,int y){
    if(x<0||x>=256||y<0||y>=192)return 0;
    int region_y=(P3D_SEARCH_REGION_ROW-1)*8;
    int field_y=(P3D_SEARCH_FIELD_ROW-1)*8;
    int keyboard_y=(P3D_SEARCH_KEYBOARD_ROW-1)*8;
    int actions_y=(P3D_SEARCH_ACTIONS_ROW-1)*8;
    if(y>=region_y && y<region_y+16)return x<128?P3D_SEARCH_TOUCH_REGION:P3D_SEARCH_TOUCH_SCOPE;
    if(y>=field_y && y<field_y+16)return P3D_SEARCH_TOUCH_FIELD;
    if(y>=keyboard_y && y<keyboard_y+32 && x>=16 && x<224){
        int row=(y-keyboard_y)/16, col=(x-16)/16;
        if(col<13)return (int)'A'+row*13+col;
    }
    if(y>=actions_y && y<actions_y+16){
        if(x<72)return P3D_SEARCH_TOUCH_BACKSPACE;
        if(x<160)return P3D_SEARCH_TOUCH_NEXT;
        return P3D_SEARCH_TOUCH_PREVIOUS;
    }
    return 0;
}
