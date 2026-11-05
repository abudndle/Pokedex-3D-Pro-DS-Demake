#ifndef P3D_MODEL_VIEW_H
#define P3D_MODEL_VIEW_H
#define P3D_ZOOM_DEFAULT 12
#define P3D_ZOOM_NEAR 8
#define P3D_ZOOM_FAR 24
#define P3D_ZOOM_ROW_TOP 112
typedef struct { int distance_quarters; } P3DModelView;
void p3dModelViewReset(P3DModelView *view);
/* Text-entry controls only: out/reset/in. No gesture guesses on source art. */
int p3dModelZoomTouch(P3DModelView *view,int model_available,int controls_visible,int x,int y);
int p3dModelViewDistance(const P3DModelView *view);
#endif
