#ifndef TEST_NEMAIN_H
#define TEST_NEMAIN_H
#include <stdint.h>
typedef enum { NE_Static, NE_Animated } NE_ModelType;
typedef enum { NE_ANIM_LOOP } NE_AnimationType;
typedef enum { NE_DL_CPU } NE_DisplayListFunction;
typedef struct NE_Model NE_Model;
typedef struct NE_Animation NE_Animation;
int NE_ModelSystemReset(int count);
int NE_AnimationSystemReset(int count);
void NE_ModelSystemEnd(void);
void NE_DisplayListSetDefaultFunction(NE_DisplayListFunction function);
NE_Model *NE_ModelCreate(NE_ModelType type);
void NE_ModelDelete(NE_Model *model);
int NE_ModelLoadStaticMeshFAT(NE_Model *model,const char *path);
int NE_ModelLoadDSMFAT(NE_Model *model,const char *path);
int NE_ModelLoadStaticMesh(NE_Model *model,const void *bytes);
int NE_ModelLoadDSM(NE_Model *model,const void *bytes);
NE_Animation *NE_AnimationCreate(void);
void NE_AnimationDelete(NE_Animation *animation);
int NE_AnimationLoadFAT(NE_Animation *animation,const char *path);
int NE_AnimationLoad(NE_Animation *animation,const void *bytes);
void NE_ModelSetAnimation(NE_Model *model,NE_Animation *animation);
void NE_ModelAnimStart(NE_Model *model,NE_AnimationType mode,int32_t speed);
void NE_ModelDraw(const NE_Model *model);
void NE_ModelAnimateAll(void);
#endif
