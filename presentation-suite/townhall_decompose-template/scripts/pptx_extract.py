#!/usr/bin/env python3
"""
pptx_extract.py — unpack a .pptx template into raw design material.

A .pptx (also .potx/.ppsx/.pptm) is a ZIP. This script does the deterministic
heavy lifting so the skill can spend its attention on *classification and taste*,
not plumbing. It writes ONE report — <out>/extract_report.json — plus the raw
media/font files. The skill reads that report and decides where each asset really
belongs. Every guess here is a HINT, not a verdict.

What it pulls (all stdlib, no Pillow/python-pptx — runs the same on Windows/macOS):
  * every embedded image → <out>/raw_media/, with px size + alpha + a bucket guess
  * where each image is USED (slideMaster / slideLayout / slideN + count) via rels —
    the strongest classification signal (master-wide image ≈ logo/background)
  * md5 dedup: repeated pastes flagged as dup_of
  * theme colour scheme + a flag if it's the stock Office default
  * a colour HISTOGRAM of every srgbClr across slides/layouts/masters (the REAL
    palette often lives in shapes, not the theme block)
  * a font-size HISTOGRAM (rPr sz) to reconstruct the type scale
  * theme font scheme + embedded font files
  * per-layout placeholder GEOMETRY (type + x/y/w/h in px) — the skeleton of layouts/
  * slide size (px), slide text grouped by placeholder type, layout names
  * a `warnings` list so the model never has to guess "broken script or thin deck?"

Usage:
    python pptx_extract.py "<path/to/template.pptx>" "<output/dir>"
"""

import sys
import os
import json
import zipfile
import shutil
import struct
import re
import hashlib
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"          # DrawingML
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"     # PresentationML
R = "{http://schemas.openxmlformats.org/package/2006/relationships}"   # package rels
EMU_PER_PX = 9525  # 914400 EMU/inch ÷ 96 px/inch

# Stock Office 2013+ theme accents — if these match, the deck never customised its theme
OFFICE_DEFAULT_ACCENTS = {"4472C4", "ED7D31", "A5A5A5", "FFC000", "5B9BD5", "70AD47"}


# --------------------------------------------------------------------------
# image dimensions + alpha from raw bytes (no Pillow)
# --------------------------------------------------------------------------
def image_meta(path):
    """Return (w, h, has_alpha). Unknown fields come back as None/False."""
    w = h = None
    alpha = False
    try:
        with open(path, "rb") as f:
            head = f.read(33)
            if len(head) >= 26 and head[:8] == b"\x89PNG\r\n\x1a\n":
                w, h = struct.unpack(">II", head[16:24])
                color_type = head[25]           # IHDR colour type byte
                alpha = color_type in (4, 6)    # grayscale+alpha / RGBA
                return (w, h, alpha)
            if len(head) >= 10 and head[:6] in (b"GIF87a", b"GIF89a"):
                w, h = struct.unpack("<HH", head[6:10])
                return (w, h, True)  # GIF supports index transparency
            if len(head) >= 26 and head[:2] == b"BM":
                w, h = struct.unpack("<ii", head[18:26])
                return (abs(w), abs(h), False)
            if head[:2] == b"\xff\xd8":  # JPEG — never has alpha
                f.seek(2)
                b = f.read(1)
                while b:
                    while b != b"\xff":
                        b = f.read(1)
                        if not b:
                            return (None, None, False)
                    marker = f.read(1)
                    while marker == b"\xff":
                        marker = f.read(1)
                    # SOF0..SOF15 except DHT/DAC/RST markers
                    if marker in (b"\xc0", b"\xc1", b"\xc2", b"\xc3", b"\xc5",
                                  b"\xc6", b"\xc7", b"\xc9", b"\xca", b"\xcb",
                                  b"\xcd", b"\xce", b"\xcf"):
                        f.read(3)
                        hh, ww = struct.unpack(">HH", f.read(4))
                        return (ww, hh, False)
                    seg = f.read(2)
                    if len(seg) < 2:
                        return (None, None, False)
                    f.seek(struct.unpack(">H", seg)[0] - 2, 1)
                    b = f.read(1)
    except Exception:
        pass
    return (w, h, alpha)


def guess_bucket(w, h, alpha, used_on, slide_w, slide_h, ext):
    """Heuristic first guess. The model confirms with its eyes; do not treat as final."""
    ext = ext.lower().lstrip(".")
    on_master = any(u.startswith("master") for u in used_on)
    on_layout = any(u.startswith("layout") for u in used_on)
    n_slides = sum(1 for u in used_on if u.startswith("slide"))

    if ext in ("emf", "wmf", "svg"):
        return "vector_icon_or_logo"          # size unknown / not raster
    if not w or not h:
        return "unknown"

    area = w * h
    aspect = w / h if h else 0

    # Usage context is the strongest signal — a master/layout-wide image is chrome
    if on_master or (on_layout and n_slides == 0):
        if slide_w and slide_h and w >= slide_w * 0.75 and h >= slide_h * 0.75:
            return "background"
        return "logo"

    if slide_w and slide_h:
        covers = (w >= slide_w * 0.75) and (h >= slide_h * 0.75)
        if covers and 1.2 <= aspect <= 2.2:
            return "background"

    # Icons ship @2x/@3x from design tools → allow up to ~512px, lean on alpha
    if area <= 512 * 512 and 0.6 <= aspect <= 1.7 and alpha:
        return "icon"
    if area <= 200 * 200 and 0.6 <= aspect <= 1.7:
        return "icon"
    if area <= 400 * 400 and (aspect >= 2.2 or aspect <= 0.45):
        return "logo_or_wordmark"
    if area >= 500 * 500:
        return "photo_or_illustration"
    return "graphic"


# --------------------------------------------------------------------------
# theme, rels, geometry, histograms
# --------------------------------------------------------------------------
def numsort(names):
    def key(s):
        m = re.search(r"(\d+)", os.path.basename(s))
        return int(m.group(1)) if m else 0
    return sorted(names, key=key)


def parse_theme(theme_xml_bytes):
    colors, fonts = {}, {}
    try:
        root = ET.fromstring(theme_xml_bytes)
    except Exception:
        return colors, fonts
    clr = root.find(f".//{A}clrScheme")
    if clr is not None:
        for child in clr:
            name = child.tag.replace(A, "")
            srgb = child.find(f"{A}srgbClr")
            sysc = child.find(f"{A}sysClr")
            if srgb is not None and srgb.get("val"):
                colors[name] = "#" + srgb.get("val").upper()
            elif sysc is not None and sysc.get("lastClr"):
                colors[name] = "#" + sysc.get("lastClr").upper()
    fs = root.find(f".//{A}fontScheme")
    if fs is not None:
        for slot in ("majorFont", "minorFont"):
            node = fs.find(f"{A}{slot}")
            if node is not None:
                latin = node.find(f"{A}latin")
                if latin is not None and latin.get("typeface"):
                    fonts[slot] = latin.get("typeface")
    return colors, fonts


def rels_for(z, part_name):
    """media basenames referenced by <part>'s .rels file."""
    d, base = os.path.split(part_name)
    rels = f"{d}/_rels/{base}.rels"
    out = []
    if rels in z.namelist():
        try:
            root = ET.fromstring(z.read(rels))
            for rel in root.findall(f"{R}Relationship"):
                tgt = rel.get("Target", "")
                if "media/" in tgt:
                    out.append(os.path.basename(tgt))
        except Exception:
            pass
    return out


def placeholder_geometry(xml_bytes):
    """List of {ph, idx, x, y, w, h} (px) for shapes carrying an explicit xfrm."""
    phs = []
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return phs
    for sp in root.iter(f"{P}sp"):
        ph = sp.find(f".//{P}ph")
        ph_type = ph.get("type") if ph is not None else "body"
        ph_idx = ph.get("idx") if ph is not None else None
        xfrm = sp.find(f".//{A}xfrm")
        if xfrm is None:
            continue
        off, ext = xfrm.find(f"{A}off"), xfrm.find(f"{A}ext")
        if off is None or ext is None:
            continue
        try:
            phs.append({
                "ph": ph_type, "idx": ph_idx,
                "x": round(int(off.get("x")) / EMU_PER_PX),
                "y": round(int(off.get("y")) / EMU_PER_PX),
                "w": round(int(ext.get("cx")) / EMU_PER_PX),
                "h": round(int(ext.get("cy")) / EMU_PER_PX),
            })
        except (TypeError, ValueError):
            continue
    return phs


def slide_text_by_ph(xml_bytes):
    """Text grouped by shape placeholder type — separates title / body / footer."""
    out = []
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return out
    for sp in root.iter(f"{P}sp"):
        ph = sp.find(f".//{P}ph")
        ph_type = ph.get("type") if ph is not None else "body"
        runs = [t.text for t in sp.iter(f"{A}t") if t.text]
        txt = "".join(runs).strip()
        if txt:
            out.append({"ph": ph_type, "text": txt})
    return out


def slide_size(pres_xml_bytes):
    try:
        root = ET.fromstring(pres_xml_bytes)
        sz = root.find(f"{P}sldSz")
        if sz is not None:
            return (round(int(sz.get("cx")) / EMU_PER_PX),
                    round(int(sz.get("cy")) / EMU_PER_PX))
    except Exception:
        pass
    return (None, None)


# --------------------------------------------------------------------------
def main():
    if len(sys.argv) < 3:
        print("usage: python pptx_extract.py <template.pptx> <output_dir>")
        sys.exit(1)
    pptx, out = sys.argv[1], sys.argv[2]
    if not os.path.isfile(pptx):
        print(f"not found: {pptx}")
        sys.exit(1)

    raw_media = os.path.join(out, "raw_media")
    raw_fonts = os.path.join(out, "raw_fonts")
    os.makedirs(raw_media, exist_ok=True)
    os.makedirs(raw_fonts, exist_ok=True)

    warnings = []
    report = {
        "source": os.path.basename(pptx),
        "slide_size_px": None,
        "theme_colors": {},
        "theme_is_office_default": False,
        "theme_fonts": {},
        "color_histogram": [],     # [[hex, count], ...] real palette signal
        "font_size_histogram": [], # [[pt, count], ...] type-scale signal
        "embedded_fonts": [],
        "layouts": [],
        "media": [],
        "slides": [],
        "warnings": warnings,
    }

    with zipfile.ZipFile(pptx) as z:
        names = z.namelist()

        # slide size
        if "ppt/presentation.xml" in names:
            sw, sh = slide_size(z.read("ppt/presentation.xml"))
            report["slide_size_px"] = {"w": sw, "h": sh}
        else:
            sw = sh = None
            warnings.append("no presentation.xml — slide size unknown")

        # theme
        theme_files = numsort([n for n in names if re.match(r"ppt/theme/theme\d+\.xml$", n)])
        if theme_files:
            colors, fonts = parse_theme(z.read(theme_files[0]))
            report["theme_colors"] = colors
            report["theme_fonts"] = fonts
            accents = {colors.get(f"accent{i}", "").lstrip("#").upper() for i in range(1, 7)}
            if OFFICE_DEFAULT_ACCENTS.issubset(accents):
                report["theme_is_office_default"] = True
                warnings.append("theme is the stock Office default — the REAL palette is "
                                "probably in shapes/backgrounds; trust color_histogram/pixels")
        else:
            warnings.append("no theme file found")

        # colour + font-size histograms across all slide/layout/master XML
        color_counter = Counter()
        size_counter = Counter()
        for n in names:
            if re.match(r"ppt/(slides|slideLayouts|slideMasters)/[^/]+\.xml$", n):
                try:
                    blob = z.read(n).decode("utf-8", "ignore")
                except Exception:
                    continue
                for hx in re.findall(r'srgbClr val="([0-9A-Fa-f]{6})"', blob):
                    color_counter["#" + hx.upper()] += 1
                for sz in re.findall(r'\bsz="(\d{3,5})"', blob):
                    size_counter[round(int(sz) / 100)] += 1  # hundredths of a pt → pt
        report["color_histogram"] = color_counter.most_common(25)
        report["font_size_histogram"] = sorted(size_counter.items(), key=lambda kv: -kv[1])[:12]

        # embedded fonts
        for n in names:
            if n.startswith("ppt/fonts/") and not n.endswith("/"):
                dest = os.path.join(raw_fonts, os.path.basename(n))
                with z.open(n) as src, open(dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                report["embedded_fonts"].append(os.path.basename(n))

        # where is each media used? (rels of every master/layout/slide)
        usage = defaultdict(list)  # media basename -> ["master1","layout3","slide2",...]

        def collect(part_glob, label):
            for n in numsort([x for x in names if re.match(part_glob, x)]):
                tag = label + re.search(r"(\d+)", os.path.basename(n)).group(1)
                for m in rels_for(z, n):
                    usage[m].append(tag)

        collect(r"ppt/slideMasters/slideMaster\d+\.xml$", "master")
        collect(r"ppt/slideLayouts/slideLayout\d+\.xml$", "layout")
        collect(r"ppt/slides/slide\d+\.xml$", "slide")

        # media — copy, size, alpha, usage, dedup
        seen_hash = {}
        for n in names:
            if n.startswith("ppt/media/") and not n.endswith("/"):
                base = os.path.basename(n)
                dest = os.path.join(raw_media, base)
                with z.open(n) as src, open(dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                ext = os.path.splitext(base)[1]
                w, h, alpha = image_meta(dest)
                with open(dest, "rb") as fh:
                    digest = hashlib.md5(fh.read()).hexdigest()
                used_on = usage.get(base, [])
                rec = {
                    "file": f"raw_media/{base}",
                    "w": w, "h": h, "alpha": alpha,
                    "ext": ext.lstrip(".").lower(),
                    "used_on": used_on,
                    "used_count": len(used_on),
                    "viewable": ext.lower().lstrip(".") not in ("emf", "wmf"),
                    "bucket_guess": guess_bucket(w, h, alpha, used_on, sw, sh, ext),
                }
                if digest in seen_hash:
                    rec["dup_of"] = seen_hash[digest]
                else:
                    seen_hash[digest] = f"raw_media/{base}"
                report["media"].append(rec)

        if not report["media"]:
            warnings.append("no media found — this deck may be colour/text-only; "
                            "backgrounds probably come from p:bg fills in the master")

        # layouts: name + placeholder geometry (the skeleton for layouts/)
        for n in numsort([x for x in names if re.match(r"ppt/slideLayouts/slideLayout\d+\.xml$", x)]):
            blob = z.read(n)
            try:
                root = ET.fromstring(blob)
                cSld = root.find(f"{P}cSld")
                name = cSld.get("name") if cSld is not None else None
            except Exception:
                name = None
            report["layouts"].append({
                "file": os.path.basename(n),
                "name": name,
                "placeholders": placeholder_geometry(blob),
            })

        # slide text grouped by placeholder type
        for n in numsort([x for x in names if re.match(r"ppt/slides/slide\d+\.xml$", x)]):
            report["slides"].append({
                "file": os.path.basename(n),
                "text": slide_text_by_ph(z.read(n)),
            })

    report_path = os.path.join(out, "extract_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"OK — wrote {report_path}")
    print(f"  slide size:     {report['slide_size_px']}")
    print(f"  theme colors:   {len(report['theme_colors'])}  office_default={report['theme_is_office_default']}")
    print(f"  color histogram:{len(report['color_histogram'])}  font sizes:{len(report['font_size_histogram'])}")
    print(f"  theme fonts:    {report['theme_fonts']}")
    print(f"  embedded fonts: {len(report['embedded_fonts'])}")
    print(f"  media files:    {len(report['media'])} -> {raw_media}")
    print(f"  slides:         {len(report['slides'])}   layouts: {len(report['layouts'])}")
    if warnings:
        print("  warnings:")
        for wmsg in warnings:
            print(f"    - {wmsg}")


if __name__ == "__main__":
    main()
