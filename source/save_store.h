#ifndef P3D_SAVE_STORE_H
#define P3D_SAVE_STORE_H
#include <stdint.h>
#define P3D_SAVE_FAVORITES 6
#define P3D_SAVE_MODEL_LIMIT 738
typedef struct {uint16_t selected_model,move_index,favorites[P3D_SAVE_FAVORITES];uint8_t favorite_count,backdrop,rotate,reserved;uint32_t challenge_correct,challenge_total;} P3DSaveState;
int p3dSaveLoad(const char *base_path,P3DSaveState *out);
int p3dSaveStore(const char *base_path,const P3DSaveState *value);
int p3dSaveStateValid(const P3DSaveState *state);
#endif
