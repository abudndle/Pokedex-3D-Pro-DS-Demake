#!/usr/bin/env python3
"""C271: exact contiguous original C5 XYZ slot order gate (private-only inputs).

The source-derived OBJ face bytes may also be present in the C5, but this
cannot establish original GPU mesh ownership, UV seams, skinning or materials.
Converted model bytes and source offsets must remain private.
"""
import math
import struct

MAX_C5_BYTES = 64 * 1024 * 1024
MAX_VERTICES = 8192
MAX_ANCHORS = 4096


def contiguous_source_xyz_proof(c5, vertices):
    """Require one unique 28-byte-stride exact float32 XYZ sequence.

    Unlike a global XYZ multiset match, this preserves original source slot
    order. The result is *not* an independently captured original GPU binding.
    """
    if type(c5) is not bytes or not 12 <= len(c5) <= MAX_C5_BYTES:
        raise ValueError('invalid private C5 source budget')
    if not 3 <= len(vertices) <= MAX_VERTICES:
        raise ValueError('native source vertex count exceeded')
    words = []
    max_error = 0.0
    for row in vertices:
        if len(row) != 3 or any(type(v) not in (float, int) or not math.isfinite(v) for v in row):
            raise ValueError('invalid finite XYZ source reference')
        for value in row:
            q = round(value * 4096)
            if not -32768 <= q <= 32767:
                raise ValueError('source XYZ outside DS 4.12 range')
            max_error = max(max_error, abs(q / 4096 - value))
        words.append(struct.pack('<3f', *row))
    start = 0
    candidates = []
    attempts = 0
    last_offset = len(c5) - 28 * (len(words) - 1) - 12
    while (offset := c5.find(words[0], start)) >= 0:
        start = offset + 1
        attempts += 1
        if attempts > MAX_ANCHORS:
            raise ValueError('source XYZ anchor ambiguity budget exceeded')
        if offset % 4 or offset > last_offset:
            continue
        if all(c5[offset + 28 * i:offset + 28 * i + 12] == word
               for i, word in enumerate(words)):
            candidates.append(offset)
            if len(candidates) > 1:
                raise ValueError('ambiguous full contiguous source XYZ sequences')
    if len(candidates) != 1:
        raise ValueError('no unique full contiguous source XYZ sequence')
    return {'source_contiguous_xyz_order_exact_unique': True,
            'source_contiguous_xyz_count': len(words),
            'source_contiguous_xyz_stride': 28,
            'source_contiguous_xyz_offset_private': candidates[0],
            'maximum_ds_xyz_quantization_error': max_error,
            'original_renderer_vertex_binding_verified': False}


def candidate_pair_contiguous(c5, obj, model):
    """Produce a bounded native *candidate*, never an authentic GPU proof."""
    from c207_private_c5_xyz import obj_vertices
    from c247_private_global_xyz_candidate import candidate_pair
    proof = contiguous_source_xyz_proof(c5, obj_vertices(obj))
    vx, ix, report = candidate_pair(c5, obj, model)
    report.update(proof)
    report['schema'] = 'p3d-c271-private-contiguous-source-xyz-candidate-v1'
    report['original_3ds_vertex_slot_binding_verified'] = False
    report['original_uv_seam_material_skinning_verified'] = False
    report['asset_integrated_emulator_verified'] = False
    report['full_original_model_verified'] = False
    return vx, ix, report
