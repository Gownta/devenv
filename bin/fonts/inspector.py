#!/usr/bin/env python3
"""Inspect font glyphs and assess their widths using macOS CoreText.

This reproduces the analysis used to explain why a Nerd Font "Mono" (NFM)
variant renders an icon small (single cell) while the non-Mono variant renders
it large (overflowing the cell): the distinguishing signal is the glyph's ink
bounding box relative to its advance width.

No third-party dependencies -- CoreText is bound directly via ctypes, so this
runs on any Mac with the system Python.

Examples:
    # Inspect one codepoint in one font (by family name):
    inspector.py -f "NotoMono Nerd Font Mono" U+F408

    # Compare several fonts (by name and/or file path) for the same glyph:
    inspector.py -f "NotoMono Nerd Font Mono" \\
                 -f ~/Library/Fonts/Noto/NotoSansNerdFont-Regular.ttf \\
                 U+F408

    # Several glyphs at a specific point size, custom reference cell char:
    inspector.py -f Menlo -s 16 -r M U+F408 0xE0B0 A

Glyph arguments accept:  U+F408 | 0xF408 | f408 (bare hex) | a single literal
character (e.g. A, ⚡).
"""

import argparse
import ctypes
import os
import sys
from ctypes import c_bool, c_char_p, c_double, c_long, c_uint16, c_uint32, c_void_p, POINTER

# --- CoreText / CoreGraphics / CoreFoundation via ctypes ---------------------

CGFloat = c_double  # 64-bit only, which is all modern macOS


class CGPoint(ctypes.Structure):
    _fields_ = [("x", CGFloat), ("y", CGFloat)]


class CGSize(ctypes.Structure):
    _fields_ = [("width", CGFloat), ("height", CGFloat)]


class CGRect(ctypes.Structure):
    _fields_ = [("origin", CGPoint), ("size", CGSize)]


# CTFontOrientation
kCTFontOrientationHorizontal = 1
# CFStringEncoding
kCFStringEncodingUTF8 = 0x08000100


def _load(name, path):
    try:
        return ctypes.CDLL(name)
    except OSError:
        return ctypes.CDLL(path)


def _load_frameworks():
    if sys.platform != "darwin":
        sys.exit("error: this tool requires macOS (CoreText).")
    fw = "/System/Library/Frameworks/{0}.framework/{0}"
    cf = _load("CoreFoundation", fw.format("CoreFoundation"))
    cg = _load("CoreGraphics", fw.format("CoreGraphics"))
    ct = _load("CoreText", fw.format("CoreText"))

    cf.CFStringCreateWithCString.restype = c_void_p
    cf.CFStringCreateWithCString.argtypes = [c_void_p, c_char_p, c_uint32]
    cf.CFStringGetCString.restype = c_bool
    cf.CFStringGetCString.argtypes = [c_void_p, c_char_p, c_long, c_uint32]
    cf.CFRelease.restype = None
    cf.CFRelease.argtypes = [c_void_p]

    cg.CGDataProviderCreateWithFilename.restype = c_void_p
    cg.CGDataProviderCreateWithFilename.argtypes = [c_char_p]
    cg.CGFontCreateWithDataProvider.restype = c_void_p
    cg.CGFontCreateWithDataProvider.argtypes = [c_void_p]
    cg.CGDataProviderRelease.restype = None
    cg.CGDataProviderRelease.argtypes = [c_void_p]

    ct.CTFontCreateWithName.restype = c_void_p
    ct.CTFontCreateWithName.argtypes = [c_void_p, CGFloat, c_void_p]
    ct.CTFontCreateWithGraphicsFont.restype = c_void_p
    ct.CTFontCreateWithGraphicsFont.argtypes = [c_void_p, CGFloat, c_void_p, c_void_p]
    ct.CTFontCopyFamilyName.restype = c_void_p
    ct.CTFontCopyFamilyName.argtypes = [c_void_p]
    ct.CTFontGetUnitsPerEm.restype = c_uint32
    ct.CTFontGetUnitsPerEm.argtypes = [c_void_p]
    ct.CTFontGetGlyphsForCharacters.restype = c_bool
    ct.CTFontGetGlyphsForCharacters.argtypes = [c_void_p, POINTER(c_uint16), POINTER(c_uint16), c_long]
    ct.CTFontGetAdvancesForGlyphs.restype = CGFloat
    ct.CTFontGetAdvancesForGlyphs.argtypes = [c_void_p, c_uint32, POINTER(c_uint16), POINTER(CGSize), c_long]
    ct.CTFontGetBoundingRectsForGlyphs.restype = CGRect
    ct.CTFontGetBoundingRectsForGlyphs.argtypes = [c_void_p, c_uint32, POINTER(c_uint16), POINTER(CGRect), c_long]

    return cf, cg, ct


CF, CG, CT = _load_frameworks()


def cfstr_to_py(ref):
    if not ref:
        return None
    buf = ctypes.create_string_buffer(1024)
    if CF.CFStringGetCString(ref, buf, len(buf), kCFStringEncodingUTF8):
        return buf.value.decode("utf-8")
    return None


# --- font + glyph model ------------------------------------------------------


class Font:
    def __init__(self, spec, size):
        self.spec = spec
        self.size = size
        self.from_file = os.path.exists(os.path.expanduser(spec))
        self._ref = self._create()
        self.family = cfstr_to_py(_owned(CT.CTFontCopyFamilyName(self._ref)))
        self.units_per_em = CT.CTFontGetUnitsPerEm(self._ref)

    def _create(self):
        if self.from_file:
            path = os.path.expanduser(self.spec).encode("utf-8")
            provider = CG.CGDataProviderCreateWithFilename(path)
            if not provider:
                sys.exit(f"error: could not read font file: {self.spec}")
            cgfont = CG.CGFontCreateWithDataProvider(provider)
            CG.CGDataProviderRelease(provider)
            if not cgfont:
                sys.exit(f"error: not a usable font file: {self.spec}")
            ref = CT.CTFontCreateWithGraphicsFont(cgfont, self.size, None, None)
            CF.CFRelease(cgfont)
            return ref
        name = CF.CFStringCreateWithCString(None, self.spec.encode("utf-8"), kCFStringEncodingUTF8)
        ref = CT.CTFontCreateWithName(name, self.size, None)
        CF.CFRelease(name)
        return ref

    def glyph_for_codepoint(self, cp):
        """Return CGGlyph id (0 == absent), handling astral via surrogate pair."""
        units = list(chr(cp).encode("utf-16-le"))
        # pack bytes -> uint16 code units
        u16 = [units[i] | (units[i + 1] << 8) for i in range(0, len(units), 2)]
        n = len(u16)
        chars = (c_uint16 * n)(*u16)
        glyphs = (c_uint16 * n)()
        CT.CTFontGetGlyphsForCharacters(self._ref, chars, glyphs, n)
        return glyphs[0]

    def measure(self, glyph):
        g = (c_uint16 * 1)(glyph)
        adv = (CGSize * 1)()
        CT.CTFontGetAdvancesForGlyphs(self._ref, kCTFontOrientationHorizontal, g, adv, 1)
        rects = (CGRect * 1)()
        CT.CTFontGetBoundingRectsForGlyphs(self._ref, kCTFontOrientationHorizontal, g, rects, 1)
        r = rects[0]
        return adv[0].width, r.size.width, r.size.height


def _owned(ref):
    # Helper marker for readability: caller is responsible; we release below.
    return ref


# --- CLI ---------------------------------------------------------------------


def parse_codepoint(token):
    t = token.strip()
    low = t.lower()
    if low.startswith("u+"):
        return int(low[2:], 16)
    if low.startswith("0x"):
        return int(low[2:], 16)
    if len(t) == 1:
        return ord(t)
    # bare token: hex if it is all hex digits, else treat first char literally
    try:
        return int(t, 16)
    except ValueError:
        return ord(t[0])


def verdict(present, adv, ink_w, cell):
    if not present:
        return "MISSING - font lacks this glyph; a fallback font supplies it"
    if adv <= 0:
        return "zero advance (combining/format char)"
    ink_over_adv = ink_w / adv
    parts = []
    if ink_over_adv > 1.05:
        parts.append(f"ink overflows its advance box by {ink_over_adv:.2f}x -> spills into neighbor cell (renders LARGE)")
    else:
        parts.append("ink fits within its advance box (renders inside one cell)")
    if cell:
        parts.append(f"advance = {adv / cell:.2f} cells")
    return "; ".join(parts)


def inspect_font(spec, codepoints, size, reference):
    font = Font(spec, size)
    print("=" * 78)
    origin = f"file: {os.path.expanduser(spec)}" if font.from_file else f"name: {spec}"
    print(f"Font   {origin}")
    resolved = font.family or "?"
    note = ""
    if not font.from_file and font.family and spec.lower() not in font.family.lower():
        note = "   <-- NOTE: requested name not found; CoreText fell back to this family"
    print(f"       resolved family: {resolved}{note}")
    print(f"       size: {size:g} pt   unitsPerEm: {font.units_per_em}")

    cell = None
    ref_cp = parse_codepoint(reference)
    ref_glyph = font.glyph_for_codepoint(ref_cp)
    if ref_glyph:
        cell, _, _ = font.measure(ref_glyph)
        print(f"       reference cell '{reference}' (U+{ref_cp:04X}) advance: {cell:.2f} pt")
    else:
        print(f"       reference cell '{reference}' not in font; cell ratios omitted")
    print("-" * 78)
    print(f"{'codepoint':<11}{'char':<6}{'glyph':>7}{'adv':>8}{'adv/em':>8}{'inkW':>8}{'inkH':>8}   assessment")

    for cp in codepoints:
        glyph = font.glyph_for_codepoint(cp)
        present = glyph != 0
        try:
            char = chr(cp)
            if not char.isprintable():
                char = "."
        except ValueError:
            char = "?"
        if present:
            adv, ink_w, ink_h = font.measure(glyph)
            adv_em = adv / size if size else 0
            print(f"U+{cp:04X}{'':<5}{char:<6}{glyph:>7}{adv:>8.2f}{adv_em:>8.2f}{ink_w:>8.2f}{ink_h:>8.2f}   "
                  f"{verdict(present, adv, ink_w, cell)}")
        else:
            print(f"U+{cp:04X}{'':<5}{char:<6}{'-':>7}{'-':>8}{'-':>8}{'-':>8}{'-':>8}   "
                  f"{verdict(present, 0, 0, cell)}")
    print()


def main():
    p = argparse.ArgumentParser(
        description="Inspect font glyphs and assess their widths (macOS CoreText).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("-f", "--font", action="append", required=True, metavar="FONT",
                   help="Font to inspect: a family/PostScript name, or a path to a .ttf/.otf file. "
                        "Repeat -f to compare multiple fonts.")
    p.add_argument("glyphs", nargs="+", metavar="GLYPH",
                   help="Glyphs to inspect: U+F408 | 0xF408 | bare hex | single literal char.")
    p.add_argument("-s", "--size", type=float, default=16.0,
                   help="Point size to measure at (default: 16).")
    p.add_argument("-r", "--reference", default="M", metavar="CHAR",
                   help="Reference character whose advance defines one cell (default: M). "
                        "Accepts the same forms as GLYPH.")
    args = p.parse_args()

    codepoints = [parse_codepoint(g) for g in args.glyphs]
    for spec in args.font:
        inspect_font(spec, codepoints, args.size, args.reference)


if __name__ == "__main__":
    main()
