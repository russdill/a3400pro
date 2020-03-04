#!/usr/bin/python3

import sys
import struct
import collections
import operator

# GPCD9T
# 16MHz (no effect)
# offset 0
# base 1
# 1 group
# 00000000  47 50 5f 53 50 49 46 49  01 01 01 00 00 00 00 00  |GP_SPIFI........|
# 00000010  00 00 00 00 00 00 01 00  a2 05 00 00 00 00 00 00  |................|
#                             ^---| base
# 00000040  01 00 00 00 48 00 00 00  01 00 00 00 54 00 00 00  |....H.......T...|
# 00000050  a2 05 00 00 31 0d 21 00  77 2b 00 00 02 00 00 00  |....1.!.w+......|
#                       ^---| freq

# val = 0x1000 - freq / 22255
# freq = (0x1000 - val) * 22255



def unpack(t, data):
    return t[1](*struct.unpack(t[0], data))

class rom(object):
    def __init__(self, f):
        self.f = f

        self.offset = self.f.tell()
        data = self.f.read(struct.calcsize(ROMHeader[0]))
        self.hdr = unpack(ROMHeader, data)
        self.user_data = self.hdr.data
        if self.hdr.gp_spifi != b'GP_SPIFI':
            raise Exception('Mark not present %08x' % self.hdr.gp_spifi)


        group_offsets = struct.unpack('<%dI' % self.hdr.group_cnt, f.read(self.hdr.group_cnt * 4))
        self.group_cnt = self.hdr.group_cnt
        self.f.seek(self.hdr.group_types)
        data = self.f.read(self.hdr.group_cnt * 4)
        self.group_types = [struct.unpack('<B3x', data[i*4:(i+1)*4])[0] for i in range(0, self.hdr.group_cnt)]
        self.group_files = []
        self.group_strs = []
        for t, offset in zip(self.group_types, group_offsets):
            self.group_strs.append(group_ids[t] if t in group_ids else '0x%02x' % t)
            self.f.seek(offset)
            file_cnt = struct.unpack('<I', self.f.read(4))[0]
            data = f.read((file_cnt + 1) * 4)
            file_offsets = struct.unpack('<%dI' % (file_cnt + 1), data)
            file_sizes = map(operator.sub, file_offsets[1:], file_offsets[:-1])
            self.group_files.append([(a, b) for a, b in zip(file_offsets[:-1], file_sizes)])


if __name__ == "__main__":
    with open(sys.argv[1], 'rb') as f:
        m = rom(f)
        if len(sys.argv) <= 2:
            for i in range(0, m.group_cnt):
                print('Group %d - type %s, files %u' % (i, m.group_strs[i], len(m.group_files[i])))
                for n, file in enumerate(m.group_files[i]):
                    o, s = file
                    print('File %d - offset 0x%04x, size 0x%04x' % (n, o, s))
        else:
            group, file = sys.argv[2].split(':')
            group = int(group)
            file = int(file)
            offset, sz = m.group_files[group][file]
            f.seek(offset)
            data = f.read(sz)
            sys.stdout.buffer.write(data)

