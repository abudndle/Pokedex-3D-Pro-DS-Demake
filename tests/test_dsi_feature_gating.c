#include "dsi_features.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 for(int dsi=0;dsi<2;dsi++)for(int sd=0;sd<2;sd++)for(int cam=0;cam<2;cam++){
  P3DCapabilities caps=p3dCapabilities(dsi,sd,cam);
  assert(p3dCanEnterFeature(caps,P3D_FEATURE_POKEDEX));
  assert(p3dCanEnterFeature(caps,P3D_FEATURE_PHOTO_ALBUM));
  assert(p3dCanEnterFeature(caps,P3D_FEATURE_AR)==(dsi&&cam));
  assert(!p3dCanEnterFeature(caps,(P3DFeature)999));
 }
 puts("DS/DSi camera-only feature gating: PASS");
 return 0;
}
