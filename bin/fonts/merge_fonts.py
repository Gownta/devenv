#!/usr/bin/env python3
"""Build a hybrid font by transplanting specific glyphs from a donor into a base.

Motivation: a Nerd Font "Mono" variant scales every icon down to a single cell.
Its non-Mono sibling (same base typeface) keeps the icons at natural size. This
tool copies the natural-size glyphs for a chosen set of code points from the
donor into the Mono base -- effectively "undoing --mono" for just those ranges,
while everything else stays single-cell.

It assumes base and donor are the *same family* (e.g. both NotoMono Nerd Font),
so they share unitsPerEm and the copy is lossless -- no outline scaling. Both
must be TrueType (glyf) fonts.

Examples:
    # Enlarge a handful of icons, using the built-in NotoMono defaults:
    merge_fonts.py U+F408 0xE0B0 U+E0B2

    # A whole range, explicit fonts and output path:
    merge_fonts.py -b MyMono.ttf -d MyMonoWide.ttf \\
        -o ~/Library/Fonts/NotoMonoNicholas-Regular.ttf  U+E000..U+E0FF

Glyph arguments accept:  U+F408 | 0xF408 | bare hex | a single literal char,
and ranges written START-END or START..END (e.g. U+E000-U+E0FF).
"""

import argparse
import copy
import os
import sys

try:
    from fontTools.ttLib import TTFont
except ImportError:
    sys.exit("error: this tool needs fontTools.  Install it with:\n"
             "    python3 -m pip install --user fonttools")

HOME = os.path.expanduser("~")
DEFAULT_BASE = os.path.join(HOME, "Library/Fonts/Noto/NotoMonoNerdFontMono-Regular.ttf")
DEFAULT_DONOR = os.path.join(HOME, "Library/Fonts/Noto/NotoMonoNerdFont-Regular.ttf")
IMPORT_PREFIX = "nm_"  # namespace for transplanted donor glyphs


# --- code point parsing (matches inspector.py) ------------------------------


def parse_codepoint(token):
    t = token.strip()
    low = t.lower()
    if low.startswith("u+"):
        return int(low[2:], 16)
    if low.startswith("0x"):
        return int(low[2:], 16)
    if len(t) == 1:
        return ord(t)
    try:
        return int(t, 16)
    except ValueError:
        return ord(t[0])


def parse_targets(token):
    """A single code point, or an inclusive range 'A-B' / 'A..B'."""
    for sep in ("..", "-"):
        if sep in token:
            parts = token.split(sep)
            if len(parts) == 2 and parts[0] and parts[1]:
                try:
                    a, b = parse_codepoint(parts[0]), parse_codepoint(parts[1])
                    if a <= b:
                        return list(range(a, b + 1))
                except ValueError:
                    pass
    return [parse_codepoint(token)]


# --- glyph transplant --------------------------------------------------------


def component_closure(donor, glyph_name, acc):
    """Collect glyph_name plus every glyph it references (recursively)."""
    if glyph_name in acc:
        return
    acc.append(glyph_name)
    glyph = donor["glyf"][glyph_name]
    if glyph.isComposite():
        for comp in glyph.components:
            component_closure(donor, comp.glyphName, acc)


def import_glyph(base, donor, donor_name, imported, order):
    """Copy one donor glyph (and deps) into base; return the new base name."""
    if donor_name in imported:
        return imported[donor_name]

    # Reserve names for the whole dependency closure first so composite
    # component references can be remapped consistently.
    base_glyphs = base["glyf"].glyphs
    closure = []
    component_closure(donor, donor_name, closure)
    for dname in closure:
        if dname not in imported:
            newname = IMPORT_PREFIX + dname
            while newname in base_glyphs or newname in imported.values():
                newname += "_"
            imported[dname] = newname

    for dname in closure:
        newname = imported[dname]
        if newname in base_glyphs:
            continue  # already added on a previous target
        glyph = copy.deepcopy(donor["glyf"][dname])
        if glyph.isComposite():
            for comp in glyph.components:
                comp.glyphName = imported[comp.glyphName]
        # Insert into the dicts directly; going through __setitem__ would also
        # mutate glyf.glyphOrder, double-counting against our own bookkeeping.
        base_glyphs[newname] = glyph
        base["hmtx"].metrics[newname] = donor["hmtx"][dname]
        order.append(newname)

    return imported[donor_name]


def repoint_cmap(base, codepoint, glyph_name):
    """Map codepoint -> glyph_name in every applicable unicode cmap subtable."""
    hit = False
    for sub in base["cmap"].tables:
        if not sub.isUnicode():
            continue
        fmt = getattr(sub, "format", 4)
        if codepoint > 0xFFFF and fmt not in (12, 13):
            continue  # astral won't fit a BMP subtable
        sub.cmap[codepoint] = glyph_name
        hit = True
    return hit


# --- name table --------------------------------------------------------------


def set_name(base, name_id, value):
    base["name"].setName(value, name_id, 3, 1, 0x409)  # Windows
    base["name"].setName(value, name_id, 1, 0, 0)      # Mac


def rebrand(base, family):
    ps = "".join(ch for ch in family if ch.isalnum()) + "-Regular"
    set_name(base, 1, family)               # Family
    set_name(base, 2, "Regular")            # Subfamily
    set_name(base, 4, f"{family} Regular")  # Full name
    set_name(base, 6, ps)                   # PostScript name
    set_name(base, 16, family)              # Typographic family
    set_name(base, 17, "Regular")           # Typographic subfamily
    # Unique ID
    set_name(base, 3, f"{family}; hybrid via merge_fonts.py")


# --- main --------------------------------------------------------------------


def build(base_path, donor_path, codepoints, family, output):
    if not os.path.exists(base_path):
        sys.exit(f"error: base font not found: {base_path}")
    if not os.path.exists(donor_path):
        sys.exit(f"error: donor font not found: {donor_path}")

    base = TTFont(base_path)
    donor = TTFont(donor_path)

    for tag, font, path in (("base", base, base_path), ("donor", donor, donor_path)):
        if "glyf" not in font:
            sys.exit(f"error: {tag} font is not TrueType (no glyf table): {path}")

    ube, udo = base["head"].unitsPerEm, donor["head"].unitsPerEm
    if ube != udo:
        sys.exit(f"error: unitsPerEm mismatch (base={ube}, donor={udo}). This "
                 f"tool assumes same-family fonts; use a donor from the same family.")

    donor_cmap = donor.getBestCmap()
    imported = {}                       # donor glyph name -> new base glyph name
    order = list(base.getGlyphOrder())  # own copy; extended by import_glyph
    moved, skipped = [], []

    for cp in codepoints:
        dname = donor_cmap.get(cp)
        if dname is None:
            skipped.append(cp)
            continue
        newname = import_glyph(base, donor, dname, imported, order)
        if repoint_cmap(base, cp, newname):
            moved.append(cp)
        else:
            skipped.append(cp)

    if not moved:
        sys.exit("error: no glyphs were transplanted (none of the requested code "
                 "points exist in the donor). Nothing written.")

    base.setGlyphOrder(order)
    base["glyf"].glyphOrder = order  # the glyf table caches its own order
    base["maxp"].numGlyphs = len(order)
    rebrand(base, family)

    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    base.save(output)

    print(f"Base   : {base_path}")
    print(f"Donor  : {donor_path}")
    print(f"Family : {family}")
    print(f"Output : {output}")
    print(f"Transplanted {len(moved)} glyph(s): "
          f"{', '.join('U+%04X' % c for c in moved)}")
    if skipped:
        print(f"Skipped {len(skipped)} (not in donor): "
              f"{', '.join('U+%04X' % c for c in skipped)}")


def main():
    p = argparse.ArgumentParser(
        description="Build a hybrid font by transplanting glyphs from a same-family donor.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("glyphs", nargs="+", metavar="GLYPH",
                   help="Code points / ranges to take from the donor "
                        "(U+F408, 0xF408, bare hex, literal char, or A-B / A..B).")
    p.add_argument("-b", "--base", default=DEFAULT_BASE,
                   help="Base font (single-cell). Default: NotoMono Nerd Font Mono.")
    p.add_argument("-d", "--donor", default=DEFAULT_DONOR,
                   help="Donor font (natural-size glyphs). Default: NotoMono Nerd Font.")
    p.add_argument("-n", "--family-name", default="NotoMono Nicholas",
                   help='Family name for the output font (default: "NotoMono Nicholas").')
    p.add_argument("-o", "--output", default="NotoMonoNicholas-Regular.ttf",
                   help="Output .ttf path (default: ./NotoMonoNicholas-Regular.ttf).")
    args = p.parse_args()

    codepoints = []
    for tok in args.glyphs:
        codepoints.extend(parse_targets(tok))
    # de-dupe, keep order
    seen = set()
    codepoints = [c for c in codepoints if not (c in seen or seen.add(c))]

    build(os.path.expanduser(args.base),
          os.path.expanduser(args.donor),
          codepoints,
          args.family_name,
          os.path.expanduser(args.output))


if __name__ == "__main__":
    main()
