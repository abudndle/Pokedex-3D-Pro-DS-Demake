#ifndef P3D_C107_NDS_HOST_GL_H
#define P3D_C107_NDS_HOST_GL_H
/* Exercise the real BlocksDS upload branch with capture-only GL functions. */
#define GL_RGBA 7
#define GL_RGB 8
#define TEXGEN_OFF 0
void glGenTextures(int count,int *ids);
void glBindTexture(int target,int texture_id);
int glTexImage2D(int target,int unused1,int format,int size_x,
                 int size_y,int unused2,int params,const void *pixels);
void glDeleteTextures(int count,const int *ids);
#endif
