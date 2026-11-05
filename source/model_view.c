#include "model_view.h"
void p3dModelViewReset(P3DModelView *view){if(view)view->distance_quarters=P3D_ZOOM_DEFAULT;}
int p3dModelViewDistance(const P3DModelView *view){
 return view&&view->distance_quarters>=P3D_ZOOM_NEAR&&view->distance_quarters<=P3D_ZOOM_FAR
        ?view->distance_quarters:P3D_ZOOM_DEFAULT;
}
int p3dModelZoomTouch(P3DModelView *view,int available,int visible,int x,int y){
 if(!view||!available||!visible||x<0||x>=256||
    y<P3D_ZOOM_ROW_TOP||y>=P3D_ZOOM_ROW_TOP+8)return 0;
 int distance=p3dModelViewDistance(view);
 if(x<96){if(distance<P3D_ZOOM_FAR)distance++;}
 else if(x>=160){if(distance>P3D_ZOOM_NEAR)distance--;}
 else distance=P3D_ZOOM_DEFAULT;
 view->distance_quarters=distance;return 1;
}
