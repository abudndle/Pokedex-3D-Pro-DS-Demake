#!/usr/bin/env python3
"""C333 strict real melonDS second-screen detail-tab appearance and reboot."""
import sys
from c254_melonds_nav_gate import frame


def check_dex_detail(before, detail, resumed):
    frames=[frame(path) for path in (before,detail,resumed)]
    if any(a[:4] != frames[0][:4] for a in frames):
        raise ValueError('C333 emulator captures have inconsistent geometry')
    width,height,row,stride=frames[0][:4]
    if (width,height)!=(256,403):
        raise ValueError('C333 unsupported DS-mode geometry')
    def delta(a,b):
        pa,pb=frames[a][4],frames[b][4]
        return sum(pa[y*row+x*stride:y*row+x*stride+3] !=
                   pb[y*row+x*stride:y*row+x*stride+3]
                   for y in range(265,391,2) for x in range(15,240,2))
    opened=delta(0,1)
    restored=delta(1,2)
    if opened<30:
        raise ValueError(f'C333 detail screen did not open: {opened} samples')
    if restored>15:
        raise ValueError(f'C333 selected detail changed across boot: {restored} samples')
    return {'detail_opened_lower_samples':opened,
            'reboot_lower_changed_samples':restored,
            'asset_free_detail_view_verified':True,
            'private_original_detail_values_verified':False,
            'dsi_hardware_verified':False}


if __name__=='__main__':
    if len(sys.argv)!=4:
        raise SystemExit('usage: c333_melonds_detail_frame_gate.py ENTRY DETAIL RESUMED')
    print('C333 real melonDS source-detail navigation:',check_dex_detail(*sys.argv[1:]))
