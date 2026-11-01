#ifndef P3D_ORIGINAL_UI_PAGE_H
#define P3D_ORIGINAL_UI_PAGE_H
/* Original 3DS title is a distinct source screen on both displays.
 * Never replace it with the home page or synthesized typography. */
int p3dOriginalTitleFrameLoad(unsigned frame);
int p3dOriginalTitleLoad(void);
int p3dOriginalTitleReady(void);
void p3dOriginalTitleDraw(void);
/* Returns 0 if the private page file is unavailable or malformed. */
int p3dOriginalUiPageLoad(int page);
int p3dOriginalUiPageReady(void);
void p3dOriginalUiPageDraw(void);
/* Private 3DS top-screen art is loaded separately to DS main BG2. */
int p3dOriginalTopPageLoad(int page);
int p3dOriginalTopPageReady(void);
void p3dOriginalTopPageDraw(void);
/* Source-verified A1 RGB555 UI overlay (bit15 clear = 3D cutout). */
int p3dOriginalTopOverlayLoad(int page);
int p3dOriginalTopOverlayReady(void);
void p3dOriginalTopOverlayDraw(void);
#endif
