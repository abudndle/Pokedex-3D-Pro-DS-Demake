#ifndef P3D_DEX_TEXT_H
#define P3D_DEX_TEXT_H
#define P3D_NATIONAL_SPECIES_COUNT 649
typedef struct { char name[32], description[192], height[16], weight[16]; } P3DDexText;
int p3dDexTextInit(const char *path);
int p3dDexTextRead(int national_index,P3DDexText *out);
void p3dDexTextClose(void);
#endif
