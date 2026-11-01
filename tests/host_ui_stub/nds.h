#ifndef P3D_C104_HOST_UI_NDS_H
#define P3D_C104_HOST_UI_NDS_H
/* Host-only substitute for the Nintendo DS bottom-screen bitmap RAM. */
extern unsigned short p3d_c104_bitmap[256u*192u];
#define BG_BMP_RAM_SUB(bank) (p3d_c104_bitmap)
extern unsigned short p3d_c105_top_bitmap[256u*192u];
#define BG_BMP_RAM(bank) (p3d_c105_top_bitmap)
#endif
