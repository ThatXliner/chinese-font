#!/usr/bin/env python3
"""Generate a Chinese literal-meaning font where characters are replaced by English glosses."""

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
import math

# Character to English gloss mapping (~80 common characters)
CHAR_GLOSSES = {
    # Basic elements
    "人": "person",
    "山": "mountain",
    "火": "fire",
    "水": "water",
    "日": "sun",
    "月": "moon",
    "木": "tree",
    "口": "mouth",
    "手": "hand",
    "心": "heart",
    # Nature
    "天": "sky",
    "地": "earth",
    "风": "wind",
    "雨": "rain",
    "云": "cloud",
    "雪": "snow",
    "石": "stone",
    "金": "gold",
    "土": "soil",
    "草": "grass",
    # Body parts
    "目": "eye",
    "耳": "ear",
    "鼻": "nose",
    "足": "foot",
    "头": "head",
    "身": "body",
    "骨": "bone",
    "血": "blood",
    "肉": "flesh",
    "皮": "skin",
    # Animals
    "鸟": "bird",
    "鱼": "fish",
    "马": "horse",
    "牛": "cow",
    "羊": "sheep",
    "虫": "insect",
    "狗": "dog",
    "猫": "cat",
    "龙": "dragon",
    "虎": "tiger",
    # Actions
    "走": "walk",
    "跑": "run",
    "看": "look",
    "听": "listen",
    "说": "speak",
    "写": "write",
    "读": "read",
    "吃": "eat",
    "喝": "drink",
    "睡": "sleep",
    # Objects
    "门": "door",
    "窗": "window",
    "车": "vehicle",
    "船": "boat",
    "书": "book",
    "笔": "pen",
    "刀": "knife",
    "衣": "clothes",
    "食": "food",
    "酒": "wine",
    # Abstract
    "大": "big",
    "小": "small",
    "上": "up",
    "下": "down",
    "左": "left",
    "右": "right",
    "中": "middle",
    "内": "inside",
    "外": "outside",
    "前": "front",
    # More common
    "电": "electric",
    "话": "speech",
    "图": "picture",
    "馆": "hall",
    "本": "origin",
    "文": "writing",
    "北": "north",
    "京": "capital",
    "海": "sea",
    "国": "country",
    "学": "study",
    "生": "life",
    "老": "old",
    "新": "new",
    "好": "good",
    "坏": "bad",
    "男": "male",
    "女": "female",
    "子": "child",
    "父": "father",
    "母": "mother",
    "家": "home",
    "朋": "friend",
    "友": "companion",
    "爱": "love",
    "恨": "hate",
}

# Compound ligatures (~20 common words)
LIGATURES = {
    ("火", "山"): "volcano",
    ("日", "本"): "Japan",
    ("人", "口"): "population",
    ("电", "话"): "telephone",
    ("图", "书", "馆"): "library",
    ("中", "文"): "Chinese",
    ("北", "京"): "Beijing",
    ("上", "海"): "Shanghai",
    ("手", "心"): "palm",
    ("山", "水"): "landscape",
    ("大", "学"): "university",
    ("小", "学"): "elementary school",
    ("学", "生"): "student",
    ("老", "人"): "elderly",
    ("朋", "友"): "friend",
    ("中", "国"): "China",
    ("日", "月"): "time",
    ("天", "地"): "heaven and earth",
    ("父", "母"): "parents",
    ("男", "女"): "man and woman",
}

UNITS_PER_EM = 1000
ASCENDER = 800
DESCENDER = -200
CAP_HEIGHT = 700


def text_to_outline(text: str, font_size: int = 60) -> tuple[list, int]:
    """Convert text to outline paths using PIL and return contours and width."""
    try:
        pil_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except OSError:
        try:
            pil_font = ImageFont.truetype(
                "/System/Library/Fonts/SFNSMono.ttf", font_size
            )
        except OSError:
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


def build_font():
    """Build the literal Chinese font."""
    print("Building literal_chinese.ttf...")

    glyph_names = [".notdef", "space"]
    char_strings = {}
    widths = {".notdef": 500, "space": 250}
    cmap = {32: "space"}

    char_strings[".notdef"] = create_notdef_charstring()
    char_strings["space"] = create_space_charstring()

    ligature_glyph_map = {}

    for chars, gloss in LIGATURES.items():
        glyph_name = "lig_" + "_".join(f"u{ord(c):04X}" for c in chars)
        glyph_names.append(glyph_name)

        img, img_w, img_h = text_to_outline(gloss)
        charstring, width = image_to_charstring(img, img_w, img_h)
        char_strings[glyph_name] = charstring
        widths[glyph_name] = width
        ligature_glyph_map[chars] = glyph_name

    for char, gloss in CHAR_GLOSSES.items():
        codepoint = ord(char)
        glyph_name = f"u{codepoint:04X}"
        glyph_names.append(glyph_name)

        img, img_w, img_h = text_to_outline(gloss)
        charstring, width = image_to_charstring(img, img_w, img_h)
        char_strings[glyph_name] = charstring
        widths[glyph_name] = width
        cmap[codepoint] = glyph_name

    fb = FontBuilder(UNITS_PER_EM, isTTF=False)
    fb.setupGlyphOrder(glyph_names)
    fb.setupCharacterMap(cmap)

    fb.setupCFF(
        psName="LiteralChinese-Regular",
        fontInfo={"FamilyName": "Literal Chinese", "FullName": "Literal Chinese Regular"},
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
            "version": "Version 1.0",
            "psName": "LiteralChinese-Regular",
        }
    )

    font = fb.font

    from fontTools.ttLib import newTable
    gsub = font["GSUB"] = newTable("GSUB")
    gsub.table = build_gsub_table(cmap, ligature_glyph_map)

    font.save("literal_chinese.ttf")
    print(f"Created literal_chinese.ttf with {len(CHAR_GLOSSES)} characters and {len(LIGATURES)} ligatures")


def build_gsub_table(cmap, ligature_glyph_map):
    """Build GSUB table for ligature substitutions."""
    from fontTools.ttLib.tables import otTables

    gsub = otTables.GSUB()
    gsub.Version = 0x00010000

    script_list = otTables.ScriptList()
    script_record = otTables.ScriptRecord()
    script_record.ScriptTag = "DFLT"
    script = otTables.Script()
    script.DefaultLangSys = otTables.DefaultLangSys()
    script.DefaultLangSys.ReqFeatureIndex = 0xFFFF
    script.DefaultLangSys.FeatureIndex = [0]
    script.DefaultLangSys.LookupOrder = None
    script.LangSysRecord = []
    script_record.Script = script
    script_list.ScriptRecord = [script_record]

    feature_list = otTables.FeatureList()
    feature_record = otTables.FeatureRecord()
    feature_record.FeatureTag = "liga"
    feature = otTables.Feature()
    feature.FeatureParams = None
    feature.LookupListIndex = [0]
    feature_record.Feature = feature
    feature_list.FeatureRecord = [feature_record]

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


if __name__ == "__main__":
    build_font()
