#!/usr/bin/env python3
"""Generate a Chinese literal-meaning font using CC-CEDICT dictionary."""

import os
import re
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import newTable
from fontTools.ttLib.tables import otTables
from PIL import Image, ImageDraw, ImageFont

CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
CEDICT_FILE = Path("cedict.txt")
FREQUENCY_URL = "https://raw.githubusercontent.com/ruddfawcett/hanziDB.csv/master/hanzi_db.csv"
FREQUENCY_FILE = Path("hanzi_db.csv")

# Max glyphs must be under 65535 (OpenType limit)
MAX_GLYPHS = 60000

UNITS_PER_EM = 1000
ASCENDER = 800
DESCENDER = -200
CAP_HEIGHT = 700

_pil_font = None


def _get_font(font_size: int = 60):
    """Get or create cached PIL font for worker processes."""
    global _pil_font
    if _pil_font is not None:
        return _pil_font

    fonts_to_try = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]

    for font_path in fonts_to_try:
        try:
            _pil_font = ImageFont.truetype(font_path, font_size)
            return _pil_font
        except OSError:
            continue

    _pil_font = ImageFont.load_default()
    return _pil_font


def render_glyph(glyph_name: str, gloss: str) -> tuple[str, bytes, int]:
    """Render a single glyph (worker function). Returns (glyph_name, charstring, width)."""
    pil_font = _get_font()
    target_height = 600

    bbox = pil_font.getbbox(gloss)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    padding = 10
    img_width = text_width + padding * 2
    img_height = text_height + padding * 2

    img = Image.new("L", (img_width, img_height), 0)
    draw = ImageDraw.Draw(img)
    draw.text((padding - bbox[0], padding - bbox[1]), gloss, font=pil_font, fill=255)

    scale = target_height / img_height
    scaled_width = int(img_width * scale)

    threshold = 128
    contours = []

    for y in range(img.height):
        row_start = None
        for x in range(img.width + 1):
            pixel = img.getpixel((x, y)) if x < img.width else 0
            if pixel >= threshold and row_start is None:
                row_start = x
            elif pixel < threshold and row_start is not None:
                x1 = int(row_start * scale)
                x2 = int(x * scale)
                y1 = int((img.height - y - 1) * scale) + 100
                y2 = int((img.height - y) * scale) + 100
                contours.append((x1, y1, x2, y2))
                row_start = None

    pen = T2CharStringPen(scaled_width, None)
    for x1, y1, x2, y2 in contours:
        pen.moveTo((x1, y1))
        pen.lineTo((x2, y1))
        pen.lineTo((x2, y2))
        pen.lineTo((x1, y2))
        pen.closePath()

    return glyph_name, pen.getCharString(), scaled_width


def download_cedict():
    """Download CC-CEDICT if not present."""
    if CEDICT_FILE.exists():
        return
    print("Downloading CC-CEDICT...")
    subprocess.run(
        f'curl -sL "{CEDICT_URL}" | gunzip > {CEDICT_FILE}',
        shell=True,
        check=True,
    )


def download_frequency_data():
    """Download frequency data if not present."""
    if FREQUENCY_FILE.exists():
        return
    print("Downloading frequency data...")
    subprocess.run(
        f'curl -sL "{FREQUENCY_URL}" -o {FREQUENCY_FILE}',
        shell=True,
        check=True,
    )


def load_frequency_data() -> dict[str, int]:
    """Load character frequency ranks from hanzi_db.csv. Lower rank = more common."""
    download_frequency_data()

    freq = {}
    if not FREQUENCY_FILE.exists():
        print(f"Warning: {FREQUENCY_FILE} not found, skipping frequency filtering")
        return freq

    with open(FREQUENCY_FILE, encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                rank = int(parts[0])
                char = parts[1]
                freq[char] = rank
    return freq


def parse_cedict(
    freq_data: dict[str, int],
) -> tuple[dict[str, str], dict[tuple[str, ...], str]]:
    """Parse CC-CEDICT and return single-char glosses and multi-char ligatures.

    Characters are filtered and sorted by frequency if freq_data is provided.
    """
    single_chars: dict[str, str] = {}
    ligatures: dict[tuple[str, ...], str] = {}

    with open(CEDICT_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            match = re.match(r"^(\S+)\s+(\S+)\s+\[([^\]]+)\]\s+/(.+)/$", line)
            if not match:
                continue

            traditional, simplified, _pinyin, definitions = match.groups()

            defs = definitions.split("/")
            gloss = pick_best_gloss(defs)
            if not gloss:
                continue

            for chars in [simplified, traditional]:
                if len(chars) == 1:
                    # Only include characters in our frequency list (if we have one)
                    if freq_data and chars not in freq_data:
                        continue
                    if chars not in single_chars:
                        single_chars[chars] = gloss
                else:
                    # For ligatures, all component chars must be in frequency list
                    if freq_data and not all(c in freq_data for c in chars):
                        continue
                    key = tuple(chars)
                    if key not in ligatures:
                        ligatures[key] = gloss

    # Sort single chars by frequency (most common first)
    if freq_data:
        single_chars = dict(
            sorted(single_chars.items(), key=lambda x: freq_data.get(x[0], 999999))
        )
        # Sort ligatures by average frequency of component chars
        ligatures = dict(
            sorted(
                ligatures.items(),
                key=lambda x: sum(freq_data.get(c, 999999) for c in x[0]) / len(x[0]),
            )
        )

    return single_chars, ligatures


def pick_best_gloss(definitions: list[str]) -> str | None:
    """Pick the best (shortest, most meaningful) gloss from definitions."""
    candidates = []
    for d in definitions:
        d = d.strip()
        if not d:
            continue
        d = re.sub(r"\s*\([^)]*\)", "", d)
        d = re.sub(r"\s*\[[^\]]*\]", "", d)
        d = re.sub(r"\s*\{[^}]*\}", "", d)
        d = d.split(";")[0].split(",")[0].strip()
        d = re.sub(r"^(to|a|an|the)\s+", "", d, flags=re.IGNORECASE)
        if d and len(d) <= 25 and not d.startswith("variant of") and not d.startswith("see "):
            candidates.append(d)

    if not candidates:
        return None

    candidates.sort(key=lambda x: (len(x), x))
    return candidates[0]


def text_to_outline(text: str, font_size: int = 60) -> tuple[Image.Image, int, int]:
    """Convert text to outline paths using PIL and return image and dimensions."""
    fonts_to_try = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]

    pil_font = None
    for font_path in fonts_to_try:
        try:
            pil_font = ImageFont.truetype(font_path, font_size)
            break
        except OSError:
            continue

    if pil_font is None:
        pil_font = ImageFont.load_default()

    bbox = pil_font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    padding = 10
    img_width = text_width + padding * 2
    img_height = text_height + padding * 2

    img = Image.new("L", (img_width, img_height), 0)
    draw = ImageDraw.Draw(img)
    draw.text((padding - bbox[0], padding - bbox[1]), text, font=pil_font, fill=255)

    return img, img_width, img_height


def image_to_charstring(
    img: Image.Image, img_width: int, img_height: int, target_height: int = 600
) -> tuple[bytes, int]:
    """Convert a PIL image to a CFF CharString with proper scaling."""
    scale = target_height / img_height
    scaled_width = int(img_width * scale)

    threshold = 128
    contours = []

    for y in range(img.height):
        row_start = None
        for x in range(img.width + 1):
            pixel = img.getpixel((x, y)) if x < img.width else 0
            if pixel >= threshold and row_start is None:
                row_start = x
            elif pixel < threshold and row_start is not None:
                x1 = int(row_start * scale)
                x2 = int(x * scale)
                y1 = int((img.height - y - 1) * scale) + 100
                y2 = int((img.height - y) * scale) + 100
                contours.append((x1, y1, x2, y2))
                row_start = None

    pen = T2CharStringPen(scaled_width, None)

    for x1, y1, x2, y2 in contours:
        pen.moveTo((x1, y1))
        pen.lineTo((x2, y1))
        pen.lineTo((x2, y2))
        pen.lineTo((x1, y2))
        pen.closePath()

    charstring = pen.getCharString()
    return charstring, scaled_width


def create_notdef_charstring(width: int = 500) -> bytes:
    """Create a .notdef glyph (empty rectangle)."""
    pen = T2CharStringPen(width, None)
    pen.moveTo((50, 0))
    pen.lineTo((width - 50, 0))
    pen.lineTo((width - 50, 700))
    pen.lineTo((50, 700))
    pen.closePath()
    pen.moveTo((100, 50))
    pen.lineTo((100, 650))
    pen.lineTo((width - 100, 650))
    pen.lineTo((width - 100, 50))
    pen.closePath()
    return pen.getCharString()


def create_space_charstring(width: int = 250) -> bytes:
    """Create a space glyph."""
    pen = T2CharStringPen(width, None)
    return pen.getCharString()


def build_gsub_table(cmap: dict, ligature_glyph_map: dict):
    """Build GSUB table for ligature substitutions."""
    gsub = otTables.GSUB()
    gsub.Version = 0x00010000

    # Create a LangSys that references both feature indices (liga and calt)
    def make_langsys():
        langsys = otTables.DefaultLangSys()
        langsys.ReqFeatureIndex = 0xFFFF
        langsys.FeatureIndex = [0, 1]  # Both liga and calt
        langsys.LookupOrder = None
        return langsys

    script_list = otTables.ScriptList()
    script_list.ScriptRecord = []

    # DFLT script
    dflt_record = otTables.ScriptRecord()
    dflt_record.ScriptTag = "DFLT"
    dflt_script = otTables.Script()
    dflt_script.DefaultLangSys = make_langsys()
    dflt_script.LangSysRecord = []
    dflt_record.Script = dflt_script
    script_list.ScriptRecord.append(dflt_record)

    # hani script (for CJK)
    hani_record = otTables.ScriptRecord()
    hani_record.ScriptTag = "hani"
    hani_script = otTables.Script()
    hani_script.DefaultLangSys = make_langsys()
    hani_script.LangSysRecord = []
    hani_record.Script = hani_script
    script_list.ScriptRecord.append(hani_record)

    # Register both 'liga' and 'calt' features (calt is often enabled even when liga isn't)
    feature_list = otTables.FeatureList()
    feature_list.FeatureRecord = []

    liga_record = otTables.FeatureRecord()
    liga_record.FeatureTag = "liga"
    liga_feature = otTables.Feature()
    liga_feature.FeatureParams = None
    liga_feature.LookupListIndex = [0]
    liga_record.Feature = liga_feature
    feature_list.FeatureRecord.append(liga_record)

    calt_record = otTables.FeatureRecord()
    calt_record.FeatureTag = "calt"
    calt_feature = otTables.Feature()
    calt_feature.FeatureParams = None
    calt_feature.LookupListIndex = [0]
    calt_record.Feature = calt_feature
    feature_list.FeatureRecord.append(calt_record)

    lookup_list = otTables.LookupList()
    lookup = otTables.Lookup()
    lookup.LookupType = 4
    lookup.LookupFlag = 0

    ligature_subst = otTables.LigatureSubst()
    ligature_subst.Format = 1
    ligature_subst.ligatures = {}

    for chars, lig_glyph in ligature_glyph_map.items():
        first_char = chars[0]
        rest_chars = chars[1:]

        first_glyph = cmap.get(ord(first_char))
        if not first_glyph:
            continue

        rest_glyphs = []
        valid = True
        for c in rest_chars:
            g = cmap.get(ord(c))
            if not g:
                valid = False
                break
            rest_glyphs.append(g)

        if not valid:
            continue

        if first_glyph not in ligature_subst.ligatures:
            ligature_subst.ligatures[first_glyph] = []

        lig = otTables.Ligature()
        lig.LigGlyph = lig_glyph
        lig.Component = rest_glyphs
        ligature_subst.ligatures[first_glyph].append(lig)

    lookup.SubTable = [ligature_subst]
    lookup_list.Lookup = [lookup]

    gsub.ScriptList = script_list
    gsub.FeatureList = feature_list
    gsub.LookupList = lookup_list

    return gsub


def build_font():
    """Build the literal Chinese font."""
    download_cedict()

    print("Loading frequency data...")
    freq_data = load_frequency_data()
    if freq_data:
        print(f"Loaded {len(freq_data)} character frequencies")

    print("Parsing CC-CEDICT...")
    char_glosses, ligatures = parse_cedict(freq_data)
    print(f"Found {len(char_glosses)} single characters and {len(ligatures)} compounds")

    # Limit total glyphs to stay under OpenType's 65535 limit
    total_available = len(char_glosses) + len(ligatures) + 2  # +2 for .notdef and space
    if total_available > MAX_GLYPHS:
        # Prioritize single characters over ligatures, then truncate ligatures
        max_ligatures = MAX_GLYPHS - len(char_glosses) - 2
        if max_ligatures < 0:
            # Even chars alone exceed limit - truncate chars too
            char_glosses = dict(list(char_glosses.items())[:MAX_GLYPHS - 2])
            ligatures = {}
            print(f"Truncated to {len(char_glosses)} characters (OpenType limit)")
        else:
            # Truncate ligatures to fit
            ligatures = dict(list(ligatures.items())[:max_ligatures])
            print(f"Truncated to {len(char_glosses)} chars + {len(ligatures)} ligatures (OpenType limit)")

    glyph_names = [".notdef", "space"]
    char_strings = {}
    widths = {".notdef": 500, "space": 250}
    cmap = {32: "space"}

    char_strings[".notdef"] = create_notdef_charstring()
    char_strings["space"] = create_space_charstring()

    # Prepare work items for characters
    char_work = []
    seen_glyph_names = set()
    for char, gloss in char_glosses.items():
        codepoint = ord(char)
        glyph_name = f"u{codepoint:04X}"
        if glyph_name in seen_glyph_names:
            continue
        seen_glyph_names.add(glyph_name)
        char_work.append((glyph_name, gloss, codepoint))
        cmap[codepoint] = glyph_name

    # Prepare work items for ligatures (filter to those with all chars present)
    ligature_work = []
    ligature_glyph_map = {}
    for chars, gloss in ligatures.items():
        if not all(ord(c) in cmap for c in chars):
            continue
        glyph_name = "lig_" + "_".join(f"u{ord(c):04X}" for c in chars)
        if glyph_name in seen_glyph_names:
            continue
        seen_glyph_names.add(glyph_name)
        ligature_work.append((glyph_name, gloss, chars))

    total_work = len(char_work) + len(ligature_work)
    num_workers = os.cpu_count() or 4
    print(f"Building {total_work} glyphs using {num_workers} workers...")

    completed = 0
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit character work
        char_futures = {
            executor.submit(render_glyph, gn, gl): cp
            for gn, gl, cp in char_work
        }

        # Submit ligature work
        lig_futures = {
            executor.submit(render_glyph, gn, gl): chars
            for gn, gl, chars in ligature_work
        }

        # Process character results
        for future in as_completed(char_futures):
            codepoint = char_futures[future]
            glyph_name, charstring, width = future.result()
            glyph_names.append(glyph_name)
            char_strings[glyph_name] = charstring
            widths[glyph_name] = width
            completed += 1
            if completed % 10000 == 0:
                print(f"  {completed}/{total_work} glyphs...")

        # Process ligature results
        for future in as_completed(lig_futures):
            chars = lig_futures[future]
            glyph_name, charstring, width = future.result()
            glyph_names.append(glyph_name)
            char_strings[glyph_name] = charstring
            widths[glyph_name] = width
            ligature_glyph_map[chars] = glyph_name
            completed += 1
            if completed % 10000 == 0:
                print(f"  {completed}/{total_work} glyphs...")

    print(f"  Built {len(cmap) - 1} characters + {len(ligature_glyph_map)} ligatures")

    print("Assembling font...")
    fb = FontBuilder(UNITS_PER_EM, isTTF=False)
    fb.setupGlyphOrder(glyph_names)
    fb.setupCharacterMap(cmap)

    fb.setupCFF(
        psName="LiteralChinese-Regular",
        fontInfo={
            "FamilyName": "Literal Chinese",
            "FullName": "Literal Chinese Regular",
        },
        charStringsDict=char_strings,
        privateDict={},
    )

    advance_widths = {name: (widths.get(name, 500), 0) for name in glyph_names}
    fb.setupHorizontalMetrics(advance_widths)

    fb.setupHorizontalHeader(ascent=ASCENDER, descent=DESCENDER)
    fb.setupOS2(
        sTypoAscender=ASCENDER,
        sTypoDescender=DESCENDER,
        sCapHeight=CAP_HEIGHT,
        sxHeight=500,
    )
    fb.setupPost()
    fb.setupNameTable(
        {
            "familyName": "Literal Chinese",
            "styleName": "Regular",
            "uniqueFontIdentifier": "LiteralChinese-Regular",
            "fullName": "Literal Chinese Regular",
            "version": "Version 2.0",
            "psName": "LiteralChinese-Regular",
        }
    )

    font = fb.font
    gsub = font["GSUB"] = newTable("GSUB")
    gsub.table = build_gsub_table(cmap, ligature_glyph_map)

    font.save("literal_chinese.ttf")
    print(f"\nCreated literal_chinese.ttf")
    print(f"  - {len(cmap) - 1} character glyphs")
    print(f"  - {len(ligature_glyph_map)} ligature glyphs")
    print(f"  - Source: CC-CEDICT (CC BY-SA 4.0)")


if __name__ == "__main__":
    build_font()
