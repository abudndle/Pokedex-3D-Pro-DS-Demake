#ifndef P3D_FORM_NAMES_H
#define P3D_FORM_NAMES_H
#include <stdint.h>
#define P3D_FORM_LABELS_MAX 256
#define P3D_FORM_NAME_BYTES 24
typedef struct { uint16_t species, form; char label[P3D_FORM_NAME_BYTES]; } P3DFormLabel;
typedef struct { P3DFormLabel entries[P3D_FORM_LABELS_MAX]; unsigned count; int ready; } P3DFormNames;
/* P3FN v1: magic, u16 version=1, u16 count; sorted records of
 * u16 zero-based species, u16 positive form, 24-byte zero-padded ASCII label.
 * Names are only displayed when explicitly supplied and verified. */
int p3dFormNamesLoad(P3DFormNames *names,const char *path);
const char *p3dFormName(const P3DFormNames *names,int species,int form);
#endif
