#ifndef P3D_TITLE_AUDIO_H
#define P3D_TITLE_AUDIO_H
#include <stdint.h>
#define P3D_TITLE_AUDIO_MAX_FRAMES 16u
#define P3D_TITLE_AUDIO_MAX_SAMPLES 16384u
/* Private source-observed cue positions, never synthesized title audio. */
typedef struct {
    uint8_t cue[P3D_TITLE_AUDIO_MAX_FRAMES];
    uint8_t frames,ready;
} P3DTitleCues;
typedef struct {
    /* Aligned signed PCM16 samples stay resident while ARM7 plays them. */
    uint32_t sample_count;
    uint16_t rate;
    uint8_t ready;
    int16_t pcm[P3D_TITLE_AUDIO_MAX_SAMPLES];
} P3DTitleAudio;
int p3dTitleCuesLoad(P3DTitleCues *out,const char *path,
                     unsigned expected_frames);
unsigned p3dTitleCueForFrame(const P3DTitleCues *cues,unsigned frame);
int p3dTitleAudioLoad(P3DTitleAudio *out,const char *path);
#endif
