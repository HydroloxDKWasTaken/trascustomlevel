from dataclasses import dataclass
import io
import os
import shutil
import struct
import sys

@dataclass
class Section:
    typ: str
    id_: str
    file: str
    cdrm: bytes
    is_primary: bool
    no_reloc: bool
    offset: int

def write_u8(f, u): f.write(struct.pack('B', u))
def read_u8(f): return struct.unpack('B', f.read(1))[0]
def write_u32(f, u): f.write(struct.pack('<I', u))
def read_u32(f): return struct.unpack('<I', f.read(4))[0]

def build_error(msg):
    print("BUILD ERROR!:")
    print(msg)
    sys.exit(1)

def get_reloc_size(fname):
    with open(fname, "rb") as f:
        intern = read_u32(f)
        extern = read_u32(f)
        id16 = read_u32(f)
        id_ = read_u32(f)
        ptr = read_u32(f)
        return 0x14 + intern * 8 + extern * 8  + id16 * 8 + id_ * 4 + ptr * 4
    print("Failed to open file '{}'".format(fname))

def next_valid_offset(offset, align):
    return (offset + align - 1) & ~(align - 1)

def get_extension(section):
    if section.typ == "dtp":
        return ".tr9dtp"
    print("Unknown section type '{}'".format(section.typ))

def make_cdrm(buf, dont_write_next = False):
    instr = io.BytesIO(buf)
    outstr = io.BytesIO(bytes())
    # header
    write_u32(outstr, 0x4D524443) # 'CDRM' magic
    write_u32(outstr, 0x0) # version
    write_u32(outstr, 0x1) # numBlocks
    write_u32(outstr, 0x0) # numPadding
    # first block
    write_u32(outstr, len(buf) << 8 | 0x1) # uncompressedSize and type 'uncompressed'
    write_u32(outstr, len(buf)) # compressedSize
    # padding
    write_u32(outstr, 0)
    write_u32(outstr, 0)
    # data
    outstr.write(buf)
    if not dont_write_next:
        while len(outstr.getbuffer()) % 16 != 0:
            write_u8(outstr, 0)
        write_u32(outstr, 0x5458454E) # 'NEXT' marker
        next_cdrm = next_valid_offset(len(outstr.getbuffer()) + 4, 0x800)
        # plus size of this offset
        write_u32(outstr, next_cdrm + 4 - len(outstr.getbuffer()))
        # write_u32(outstr, next_valid_offset(len(buf), 0x800) - len(buf))
    return outstr.getvalue()

drmname = sys.argv[1]

if len(sys.argv) > 2:
    drmoutname = sys.argv[2]
elif ".txtdrm" in drmname:
    drmoutname = drmname.replace(".txtdrm", ".drm")
else:
    drmoutname = drmname + ".drm"

print("Building drm '{}'...".format(drmname))

sections = []
primary_section = -1

with open(drmname, "r") as f:
    for i, line in enumerate(f):
        s = line.split()
        typ = s[0]
        id_ = int(s[1])
        file = s[2]
        flags = s[3:]
        is_primary = "primary" in flags
        no_reloc = "no_reloc" in flags
        sections.append(Section(typ, id_, file, None, is_primary, no_reloc, 0))
        ext = get_extension(sections[-1])
        shutil.copyfile(file, "customlevel_bin/" + str(id_) + ext)
        print(" Copied '{}' to '{}{}'".format(file, id_, ext))
        if is_primary:
            if primary_section != -1:
                print("Multiple primary sections in drm")
            primary_section = i

k_dlc_index = 69 << 4
tigername = "/mnt/d/SteamLibrary/steamapps/common/Tomb Raider/patch3.000.tiger"
origtigername = "/mnt/d/SteamLibrary/steamapps/common/Tomb Raider/patch3.000.orig.tiger"
cur_offset = next_valid_offset(os.path.getsize(origtigername) + 0x800, 0x800)
cur_decompressed_offset = 0x0
prev_total_uncompressed_size = 0
with open(drmoutname, "wb") as f:
    write_u32(f, 0x16) # DRMHeader.versionNumber
    write_u32(f, 0x0) # DRMHeader.drmIncludeLength
    write_u32(f, 0x0) # DRMHeader.drmDepLength
    write_u32(f, 0x0) # DRMHeader.paddingLength
    write_u32(f, 0x0) # DRMHeader.projectedDRMSize
    write_u32(f, 0x0) # DRMHeader.flags
    write_u32(f, len(sections)) # DRMHeader.numSections
    write_u32(f, primary_section) # DRMHeader.primarySection

    for s in sections:
        reloc_size = get_reloc_size(s.file) if not s.no_reloc else 0
        size = os.path.getsize(s.file) - reloc_size
        write_u32(f, size) # SectionInfo.size
        if s.typ == "dtp":
            write_u8(f, 0x7) # SectionInfo.type
        write_u8(f, 0x0) # misc flags...
        write_u8(f, 0x0)
        write_u8(f, 0x0)
        packed = reloc_size << 8
        write_u32(f, packed) # SectionInfo.packed
        write_u32(f, s.id_) # Section.id
        write_u32(f, 0xffffffff) # Section.specMask
    for i, s in enumerate(sections):
        unique_id = s.id_ | 7 << 25 # TODO: hardcode 'dtp' type
        write_u32(f, unique_id) # SectionExtraInfo.uniqueId
        # luckily, arc MM will take care of these for us for custom sections
        # NOPE NEVERMIND^
        # We're going this alone...
        s.offset = cur_offset
        print("  {:08x} {:08x} {}".format(s.offset, cur_decompressed_offset, s.file))
        write_u32(f, cur_offset | k_dlc_index) # SectionExtraInfo.packedOffset
        with open(s.file, "rb") as sf:
            s.cdrm = make_cdrm(sf.read(), i == len(sections) - 1)
        cur_offset = next_valid_offset(cur_offset + len(s.cdrm), 0x800)
        write_u32(f, len(s.cdrm)) # SectionExtraInfo.compressedSize
        write_u32(f, cur_decompressed_offset) # SectionExtraInfo.decompressedOffset
        cur_decompressed_offset += next_valid_offset(os.path.getsize(s.file), 0x10)



print(" Built drm '{}'".format(drmoutname))
print(" Writing to '{}'...".format(tigername))

def stream_copy(src, dest, start, end):
    if src.tell() != start:
        build_error("src.tell() [{}] != start [{}]".format(src.tell(), start))
    if dest.tell() != start:
        build_error("dest.tell() [{}] != start [{}]".format(dest.tell(), start))
    if start >= end:
        build_error("start [{}] >= end [{}]".format(start, end))
    dest.write(src.read(end - start))

def pad_to(f, target):
    if f.tell() >= target:
        build_error("f.tell() [{:08x}] >= target [{:08x}]".format(f.tell(), target))
    while f.tell() != target:
        write_u8(f, 0x0)

def read_records(f, count):
    records = []
    for i in range(count):
        hash = read_u32(f)
        specMask = read_u32(f)
        size = read_u32(f)
        packedOffset = read_u32(f)
        records.append((hash, specMask, size, packedOffset))
    return records

def insert_record(records, record):
    records.append(record)
    records.sort(key=lambda x: x[0])

with open(tigername, "wb") as f:
    with open(origtigername, "rb") as o:
        stream_copy(o, f, 0x0, 0x0c)
        o.seek(0x0c)
        record_count = read_u32(o)
        o.seek(o.tell() + 0x24) # skip past dlcIndex + configName
        records = read_records(o, record_count)
        target_offset = cur_offset
        insert_record(records, (0x5C668E56, 0xffffffff, os.path.getsize(drmoutname), target_offset | k_dlc_index))
        write_u32(f, record_count + 1)
        o.seek(0x10)
        stream_copy(o, f, 0x10, 0x34) # copy dlcIndex + configName
        for record in records:
            write_u32(f, record[0])
            write_u32(f, record[1])
            write_u32(f, record[2])
            write_u32(f, record[3])
        start_copy_offset = 0x34 + (record_count + 1) * 0x10
        o.seek(start_copy_offset)
        stream_copy(o, f, start_copy_offset, os.path.getsize(origtigername))
    for i, s in enumerate(sections):
        pad_to(f, s.offset)
        f.write(s.cdrm)
    with open(drmoutname, "rb") as g:
        pad_to(f, target_offset)
        f.write(g.read())
    # write_u32(f, 0xCAFEBABE)
print(" Wrote to '{}'".format(tigername))
