#ifndef P3D_MOVE_DEX_H
#define P3D_MOVE_DEX_H
#include <stdint.h>
#define P3D_MOVE_COUNT 559
#define P3D_MOVE_NAME_MAX 48
#define P3D_MOVE_TEXT_MAX 540
typedef struct {uint16_t id;char name[P3D_MOVE_NAME_MAX];char description[P3D_MOVE_TEXT_MAX];char effect[P3D_MOVE_TEXT_MAX];} P3DMove;
int p3dMoveDexInit(const char *path);
int p3dMoveDexCount(void);
int p3dMoveDexRead(int zero_based_index,P3DMove *out);
int p3dMoveDexFindInitial(int start,char initial,int direction);
#endif
