"""C163: require explicit geometry-to-draw ranges before native pass rendering.

Original C5 draw records alone do not prove DS3M/P3CS triangle order.
Fail closed unless every source draw has a validated nonoverlapping range.
"""
from c162_manifest_render_gate import validate_manifest

def validate_geometry_binding(manifest, bindings, triangle_count):
    validate_manifest(manifest)
    if type(triangle_count) is not int or triangle_count < 1:
        raise ValueError("invalid geometry triangle count")
    if not isinstance(bindings, list) or len(bindings) != len(manifest["draws"]):
        raise ValueError("missing source draw-to-geometry evidence")
    used = set()
    for order, (draw, bind) in enumerate(zip(manifest["draws"], bindings)):
        if not isinstance(bind, dict) or bind.get("draw_order") != order:
            raise ValueError("geometry binding order mismatch")
        first, count = bind.get("first_triangle"), bind.get("triangle_count")
        if type(first) is not int or type(count) is not int or first < 0 or count != draw["triangles"]:
            raise ValueError("invalid original draw geometry range")
        if first > triangle_count - count:
            raise ValueError("geometry range out of bounds")
        if bind.get("source_order_verified") is not True:
            raise ValueError("geometry source order not independently verified")
        segment = set(range(first, first + count))
        if used.intersection(segment):
            raise ValueError("overlapping geometry draw ranges")
        used.update(segment)
    return {"draws_bound":len(bindings),"triangles_bound":len(used),
            "texture_sampler_roles_verified":False,"native_renderer_integrated":False}
