"""Actual synthetic red-mesh framebuffer acceptance, never private data."""
import sys
from c306_synthetic_texture_frame_gate import frame_rgb,safe_png
def count_model(path):
    w,h,rgb=frame_rgb(path)
    if w!=256 or h not in (384,403):raise ValueError('unsupported DS capture geometry')
    top=19 if h==403 else 0
    return sum((c:=rgb(x,y))[0]>=75 and c[0]>=c[1]+35 and c[0]>=c[2]+35
               for y in range(top,top+192,2) for x in range(0,256,2))


def verify(*paths):
    if len(paths)!=5:raise ValueError('five frames required')
    counts=[count_model(p) for p in paths]
    default,near,reset,far,reset_again=counts
    if default<50:raise ValueError('no rendered synthetic model')
    if near<default*1.3:raise ValueError('zoom in did not enlarge actual model')
    if far>default*0.8 or far<10:raise ValueError('zoom out failed or model disappeared')
    if any(abs(n-default)>max(5,default*.03) for n in (reset,reset_again)):
        raise ValueError('reset did not restore default model size')
    return {'red_model_samples':counts,'native_zoom_reset_verified':True,
            'original_model_fidelity_verified':False,'hardware_verified':False}


if __name__=='__main__':
    paths=sys.argv[1:]
    for p in paths:safe_png(p,p.replace('.xwd','.png'))
    print('C359 rendered red model samples:',[count_model(p) for p in paths])
    print('C359 actual synthetic camera zoom:',verify(*paths))
