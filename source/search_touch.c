#include "search_touch.h"
int p3dSearchTouchAction(int x,int y){
    if(x<0||x>=256||y<0||y>=192)return 0;
    if(y>=88 && y<104)return x<128?P3D_SEARCH_TOUCH_REGION:P3D_SEARCH_TOUCH_SCOPE;
    if(y>=104 && y<120)return P3D_SEARCH_TOUCH_FIELD;
    if(y>=144 && y<176 && x>=16 && x<224){
        int row=(y-144)/16, col=(x-16)/16;
        if(col<13)return (int)'A'+row*13+col;
    }
    if(y>=176 && y<192){
        if(x<72)return P3D_SEARCH_TOUCH_BACKSPACE;
        if(x<160)return P3D_SEARCH_TOUCH_NEXT;
        return P3D_SEARCH_TOUCH_PREVIOUS;
    }
    return 0;
}
