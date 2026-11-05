#ifndef P3D_BOOKMARK_EDIT_H
#define P3D_BOOKMARK_EDIT_H
#include <stdint.h>
#define P3D_BOOKMARK_CAPACITY 16
typedef struct {
 uint16_t ids[P3D_BOOKMARK_CAPACITY];
 uint8_t count;
 uint8_t editing;
} P3DBookmarkList;
/* Returns 1 for mutation, 0 for no-op/invalid input. */
int p3dBookmarkAdd(P3DBookmarkList *list,uint16_t id,uint16_t limit);
int p3dBookmarkRemoveAt(P3DBookmarkList *list,unsigned index);
int p3dBookmarkEditTap(P3DBookmarkList *list,unsigned index);
int p3dBookmarkValid(const P3DBookmarkList *list,uint16_t limit);
void p3dBookmarkSetEditing(P3DBookmarkList *list,int enabled);
#endif
