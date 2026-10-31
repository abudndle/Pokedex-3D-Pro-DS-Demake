#ifndef NDS_STUB_H
#define NDS_STUB_H
#include <stdint.h>
typedef int16_t v16;
#define GL_TRIANGLES 1
void glColor3b(unsigned char, unsigned char, unsigned char);
void glBegin(int);
void glVertex3v16(v16,v16,v16);
void glEnd(void);
#endif
