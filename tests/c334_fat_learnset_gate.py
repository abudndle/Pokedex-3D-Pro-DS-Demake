"""Independent real FAT learnset checkpoint check, synthetic fixtures only."""
import struct
import sys
from pathlib import Path
from c260_fat_slot_gate import valid_resume_slots
from c334_synthetic_learnset import payload


def check(root, page=1):
    data = valid_resume_slots(Path(root))
    expected = struct.unpack_from('<I', payload(), 12)[0]
    if (data[4] != 6 or data[12:14] != bytes((0, 1))
            or data[76:78] != bytes((4, page))
            or struct.unpack_from('<H', data, 16)[0] != 0
            or struct.unpack_from('<H', data, 24)[0] != 0
            or struct.unpack_from('<I', data, 80)[0] != expected):
        raise ValueError('wrong exact learnset species/form/page/source checkpoint')
    return {'version': 6, 'page': page, 'synthetic_source_bound': True}


def check_navigation(root):
    data = valid_resume_slots(Path(root))
    if (data[4] != 3 or data[12:14] != bytes((0, 1))
            or struct.unpack_from('<H', data, 16)[0] != 1
            or struct.unpack_from('<H', data, 20)[0] != 1):
        raise ValueError('Right input did not synchronize active and saved species')
    return {'active_species': 1, 'saved_species': 1}


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[2] == '--navigation':
        print('C334 real Right input/save synchronization:', check_navigation(sys.argv[1]))
    else:
        print('C334 real FAT learnset resume:', check(sys.argv[1]))
