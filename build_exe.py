#!/usr/bin/env python3
"""Build 'SciFigure Studio.exe' — a tiny x64 Windows GUI launcher (hand-built PE).

Behavior: ShellExecuteA(NULL,"open","SciFigureStudio.html",...) -> opens the app
in the default browser. If that fails (file missing), shows a MessageBox.
Embeds app.ico so Explorer shows the logo.
"""
import struct, os

IMAGE_BASE = 0x140000000
SEC_ALIGN, FILE_ALIGN = 0x1000, 0x200
RVA_TEXT, RVA_IDATA, RVA_RSRC = 0x1000, 0x2000, 0x3000

def align(v, a): return (v + a - 1) & ~(a - 1)

# ============================ .idata ============================
I = RVA_IDATA
# 4 descriptors (kernel32, shell32, user32, null) = 80 bytes
OFF_DESC   = 0x00
OFF_ILT_K  = 0x58; OFF_ILT_S = 0x68; OFF_ILT_U = 0x78
OFF_IAT_K  = 0x88; OFF_IAT_S = 0x98; OFF_IAT_U = 0xA8
OFF_HN_EXIT = 0xC0; OFF_HN_SHELL = 0xD0; OFF_HN_MSG = 0xE0
OFF_N_K32 = 0xF0; OFF_N_S32 = 0x100; OFF_N_U32 = 0x110
IDATA_SIZE = 0x120

idata = bytearray(IDATA_SIZE)
def desc(oft, name, ft): return struct.pack("<IIIII", oft, 0, 0, name, ft)
d  = desc(I+OFF_ILT_K, I+OFF_N_K32, I+OFF_IAT_K)
d += desc(I+OFF_ILT_S, I+OFF_N_S32, I+OFF_IAT_S)
d += desc(I+OFF_ILT_U, I+OFF_N_U32, I+OFF_IAT_U)
d += b"\0" * 20
idata[OFF_DESC:OFF_DESC+len(d)] = d
for ilt, iat, hn in ((OFF_ILT_K, OFF_IAT_K, OFF_HN_EXIT),
                     (OFF_ILT_S, OFF_IAT_S, OFF_HN_SHELL),
                     (OFF_ILT_U, OFF_IAT_U, OFF_HN_MSG)):
    entry = struct.pack("<Q", I + hn)
    idata[ilt:ilt+8] = entry; idata[iat:iat+8] = entry
def hint_name(off, name):
    b = b"\0\0" + name + b"\0"
    idata[off:off+len(b)] = b
hint_name(OFF_HN_EXIT,  b"ExitProcess")
hint_name(OFF_HN_SHELL, b"ShellExecuteA")
hint_name(OFF_HN_MSG,   b"MessageBoxA")
idata[OFF_N_K32:OFF_N_K32+13] = b"KERNEL32.dll\0"
idata[OFF_N_S32:OFF_N_S32+12] = b"SHELL32.dll\0"
idata[OFF_N_U32:OFF_N_U32+11] = b"USER32.dll\0"

IAT_EXIT  = I + OFF_IAT_K
IAT_SHELL = I + OFF_IAT_S
IAT_MSG   = I + OFF_IAT_U

# ============================ .text ============================
STR_OPEN  = b"open\0"
STR_FILE  = b"SciFigureStudio.html\0"
STR_MSG   = b"SciFigureStudio.html was not found.\nKeep the .exe and the .html file in the same folder.\0"
STR_TITLE = b"SciFigure Studio\0"

def assemble(code_len_guess):
    """Two-pass: strings placed right after code."""
    str_base = RVA_TEXT + align(code_len_guess, 16)
    rva_open  = str_base
    rva_file  = rva_open + len(STR_OPEN)
    rva_msg   = align(rva_file + len(STR_FILE), 8)
    rva_title = rva_msg + len(STR_MSG)

    code = bytearray(); pos = lambda: RVA_TEXT + len(code)
    def emit(b): code.extend(b)
    def rel32(target):  # displacement from end of a 4-byte field that ends the instruction
        return struct.pack("<i", target - (pos() + 4))

    emit(b"\x48\x83\xEC\x38")                     # sub rsp,0x38
    emit(b"\x31\xC9")                             # xor ecx,ecx
    emit(b"\x48\x8D\x15"); emit(rel32(rva_open))  # lea rdx,[rip+open]
    emit(b"\x4C\x8D\x05"); emit(rel32(rva_file))  # lea r8,[rip+file]
    emit(b"\x45\x31\xC9")                         # xor r9d,r9d
    emit(b"\x48\xC7\x44\x24\x20\x00\x00\x00\x00") # mov qword[rsp+0x20],0
    emit(b"\x48\xC7\x44\x24\x28\x01\x00\x00\x00") # mov qword[rsp+0x28],1  (SW_SHOWNORMAL)
    emit(b"\xFF\x15"); emit(rel32(IAT_SHELL))     # call [rip+ShellExecuteA]
    emit(b"\x48\x83\xF8\x20")                     # cmp rax,32
    ja_at = len(code); emit(b"\x77\x00")          # ja Lexit (patched)
    emit(b"\x31\xC9")                             # xor ecx,ecx
    emit(b"\x48\x8D\x15"); emit(rel32(rva_msg))   # lea rdx,[rip+msg]
    emit(b"\x4C\x8D\x05"); emit(rel32(rva_title)) # lea r8,[rip+title]
    emit(b"\x41\xB9\x10\x00\x00\x00")             # mov r9d,0x10 (MB_ICONERROR)
    emit(b"\xFF\x15"); emit(rel32(IAT_MSG))       # call [rip+MessageBoxA]
    lexit = len(code)
    code[ja_at+1] = lexit - (ja_at + 2)           # patch ja rel8
    emit(b"\x31\xC9")                             # xor ecx,ecx
    emit(b"\xFF\x15"); emit(rel32(IAT_EXIT))      # call [rip+ExitProcess]
    emit(b"\xCC")                                 # int3

    # append strings at planned offsets
    text = bytearray(code)
    text += b"\xCC" * ((str_base - RVA_TEXT) - len(text))
    text += STR_OPEN + STR_FILE
    text += b"\0" * ((rva_msg - RVA_TEXT) - len(text))
    text += STR_MSG + STR_TITLE
    return bytes(text), len(code)

text, clen = assemble(0x80)
assert clen <= 0x80, clen
TEXT_SIZE = len(text)

# ============================ .rsrc (icon) ============================
ico = open("app.ico", "rb").read()
rsv, typ, cnt = struct.unpack("<HHH", ico[:6])
assert typ == 1
images = []
for i in range(cnt):
    w, h, colors, r0, planes, bpp, size, off = struct.unpack("<BBBBHHII", ico[6+16*i:6+16*i+16])
    images.append(dict(w=w, h=h, colors=colors, planes=planes, bpp=bpp, data=ico[off:off+size]))

# group icon data
grp = struct.pack("<HHH", 0, 1, cnt)
for i, im in enumerate(images):
    grp += struct.pack("<BBBBHHIH", im["w"], im["h"], im["colors"], 0,
                       im["planes"], im["bpp"], len(im["data"]), i + 1)

# resource tree:  root{3:{1..n:{lang}},14:{1:{lang}}}
def build_rsrc():
    LANG = 0x0409
    dirs = []   # list of (bytes) placed sequentially; offsets patched via two-pass
    # We lay out: root, dir3, dir14, langdirs(n+1), dataentries(n+1), rawdata
    n = len(images)
    hdr = lambda cnt: struct.pack("<IIHHHH", 0, 0, 0, 0, 0, cnt)
    sz_root = 16 + 2*8
    sz_d3   = 16 + n*8
    sz_d14  = 16 + 1*8
    sz_lang = 16 + 1*8
    off_root = 0
    off_d3   = off_root + sz_root
    off_d14  = off_d3 + sz_d3
    off_lang0 = off_d14 + sz_d14              # n lang dirs for icons, then 1 for group
    off_data0 = off_lang0 + (n+1)*sz_lang     # data entries, 16 bytes each
    off_raw   = align(off_data0 + (n+1)*16, 8)

    raws, raw_offs = [], []
    cur = off_raw
    for im in images:
        raw_offs.append(cur); raws.append(im["data"]); cur = align(cur + len(im["data"]), 8)
    grp_off = cur; cur += len(grp)
    total = cur

    out = bytearray(total)
    def put(off, b): out[off:off+len(b)] = b
    # root
    put(off_root, hdr(2))
    put(off_root+16, struct.pack("<II", 3,  0x80000000 | off_d3))
    put(off_root+24, struct.pack("<II", 14, 0x80000000 | off_d14))
    # type 3
    put(off_d3, hdr(n))
    for i in range(n):
        put(off_d3+16+8*i, struct.pack("<II", i+1, 0x80000000 | (off_lang0 + i*sz_lang)))
    # type 14
    put(off_d14, hdr(1))
    put(off_d14+16, struct.pack("<II", 1, 0x80000000 | (off_lang0 + n*sz_lang)))
    # lang dirs -> data entries
    for i in range(n+1):
        lo = off_lang0 + i*sz_lang
        put(lo, hdr(1))
        put(lo+16, struct.pack("<II", LANG, off_data0 + i*16))
    # data entries
    for i in range(n):
        put(off_data0+16*i, struct.pack("<IIII", RVA_RSRC + raw_offs[i], len(raws[i]), 0, 0))
    put(off_data0+16*n, struct.pack("<IIII", RVA_RSRC + grp_off, len(grp), 0, 0))
    # raw
    for i in range(n):
        put(raw_offs[i], raws[i])
    put(grp_off, grp)
    return bytes(out)

rsrc = build_rsrc()
RSRC_SIZE = len(rsrc)

# ============================ headers ============================
sections = [
    (b".text",  RVA_TEXT,  TEXT_SIZE,  0x60000020),  # code|exec|read
    (b".idata", RVA_IDATA, IDATA_SIZE, 0xC0000040),  # data|read|write (IAT written by loader)
    (b".rsrc",  RVA_RSRC,  RSRC_SIZE,  0x40000040),  # data|read
]
SIZE_HEADERS = 0x400
file_pos = SIZE_HEADERS
sec_hdrs, sec_data = b"", []
for name, rva, size, flags in sections:
    raw = align(size, FILE_ALIGN)
    sec_hdrs += struct.pack("<8sIIIIIIHHI", name.ljust(8, b"\0"), size, rva,
                            raw, file_pos, 0, 0, 0, 0, flags)
    sec_data.append(file_pos)
    file_pos += raw
SIZE_IMAGE = align(RVA_RSRC + RSRC_SIZE, SEC_ALIGN)

dos = struct.pack("<2s58xI", b"MZ", 0x80).ljust(0x80, b"\0")

coff = struct.pack("<IHHIIIHH", 0x00004550, 0x8664, len(sections), 0, 0, 0, 0xF0,
                   0x0022)  # PE\0\0, x64, EXECUTABLE|LARGE_ADDRESS_AWARE

ddirs = [(0,0)] * 16
ddirs[1]  = (RVA_IDATA, 80)             # import table
ddirs[2]  = (RVA_RSRC, RSRC_SIZE)       # resources
ddirs[12] = (I + OFF_IAT_K, 0x30)       # IAT
ddir_bytes = b"".join(struct.pack("<II", r, s) for r, s in ddirs)

opt = struct.pack("<HBBIIIII", 0x20B, 14, 0, align(TEXT_SIZE, FILE_ALIGN),
                  align(IDATA_SIZE + RSRC_SIZE, FILE_ALIGN), 0, RVA_TEXT, RVA_TEXT)
opt += struct.pack("<QIIHHHHHHIIIIHHQQQQII", IMAGE_BASE, SEC_ALIGN, FILE_ALIGN,
                   6, 0, 0, 0, 6, 0, 0, SIZE_IMAGE, SIZE_HEADERS, 0,
                   2,       # Subsystem: WINDOWS_GUI (no console)
                   0x8100,  # DllCharacteristics: NX_COMPAT | TERMINAL_SERVER_AWARE
                   0x100000, 0x1000, 0x100000, 0x1000, 0, 16)
opt += ddir_bytes
assert len(opt) == 0xF0, len(opt)

hdrs = dos + coff + opt + sec_hdrs
assert len(hdrs) <= SIZE_HEADERS
pe = bytearray(file_pos)              # full file, zero-filled
pe[0:len(hdrs)] = hdrs
for (name, rva, size, flags), fp, blob in zip(sections, sec_data, [text, bytes(idata), rsrc]):
    pe[fp:fp+len(blob)] = blob
pe = bytes(pe)

out = "SciFigure Studio.exe"
open(out, "wb").write(pe)
print(f"{out}: {len(pe)} bytes, code {clen}B, rsrc {RSRC_SIZE}B")
