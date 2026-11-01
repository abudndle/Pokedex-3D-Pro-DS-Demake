#include "dsi_features.h"
P3DCapabilities p3dCapabilities(int dsi_mode,int sd_ready,int camera_ready){
 P3DCapabilities caps;
 caps.dsi_mode=dsi_mode?1:0;
 caps.sd_ready=caps.dsi_mode&&sd_ready?1:0;
 caps.camera_ready=caps.dsi_mode&&camera_ready?1:0;
 return caps;
}
int p3dFeatureVisible(P3DCapabilities caps,P3DFeature feature){
 switch(feature){
 case P3D_FEATURE_POKEDEX:return 1;
 case P3D_FEATURE_AR:return 1; /* Visible, greyed out when unavailable. */
 case P3D_FEATURE_PHOTO_ALBUM:return 1;
 default:return 0;
 }
}
int p3dCanEnterFeature(P3DCapabilities caps,P3DFeature feature){
 if(feature==P3D_FEATURE_AR)return caps.dsi_mode&&caps.camera_ready;
 return p3dFeatureVisible(caps,feature);
}
