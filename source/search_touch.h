#ifndef P3D_SEARCH_TOUCH_H
#define P3D_SEARCH_TOUCH_H
/* C83 text-only search touchscreen. Source artwork hitboxes are still unknown.
 * Returns an ASCII capital A-Z, a negative action, or zero for no hit. */
#define P3D_SEARCH_TOUCH_BACKSPACE -1
#define P3D_SEARCH_TOUCH_NEXT -2
#define P3D_SEARCH_TOUCH_PREVIOUS -3
#define P3D_SEARCH_TOUCH_REGION -4
#define P3D_SEARCH_TOUCH_SCOPE -5
#define P3D_SEARCH_TOUCH_FIELD -6
/* One-based console rows shared by native rendering and touch mapping. */
#define P3D_SEARCH_REGION_ROW 12
#define P3D_SEARCH_FIELD_ROW 14
#define P3D_SEARCH_RESULT_ROW 16
#define P3D_SEARCH_KEYBOARD_ROW 19
#define P3D_SEARCH_ACTIONS_ROW 23
int p3dSearchTouchAction(int x,int y);
#endif
