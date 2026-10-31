#ifndef P3D_DSI_FEATURES_H
#define P3D_DSI_FEATURES_H
typedef struct {int dsi_mode;int sd_ready;int camera_ready;} P3DCapabilities;
typedef enum {P3D_FEATURE_POKEDEX=0,P3D_FEATURE_AR,P3D_FEATURE_PHOTO_ALBUM} P3DFeature;
P3DCapabilities p3dCapabilities(int dsi_mode,int sd_ready,int camera_ready);
int p3dFeatureVisible(P3DCapabilities caps,P3DFeature feature);
int p3dCanEnterFeature(P3DCapabilities caps,P3DFeature feature);
#endif
