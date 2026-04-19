# Literal Chinese Font

A font that replaces Chinese characters with their English meanings. Compound words like 火山 render as "volcano" instead of "fire mountain" using OpenType ligatures.

## Demo

[**Try it live →**](https://thatxliner.github.io/chinese-font/)

Type Chinese text and see it rendered with English glosses in real-time.

## Features

- **~8,000 character glosses** — sourced from [CC-CEDICT](https://cc-cedict.org/), filtered by frequency for the most common characters
- **50,000+ ligature compounds** — multi-character words render as single glosses (日本→Japan, 图书馆→library, 北京→Beijing)
- **Parallel glyph generation** — uses all CPU cores to build the font quickly
- **Fallback rendering** — unsupported characters display normally

## Usage

### Generate the font

```bash
uv sync
uv run python generate_font.py
```

This downloads CC-CEDICT and frequency data automatically, then generates `literal_chinese.ttf`.

### Test locally

```bash
python3 -m http.server
# Open http://localhost:8000
```

### Deploy to GitHub Pages

Push to `main` — the workflow deploys the demo automatically.

## How it works

1. Downloads the CC-CEDICT dictionary and character frequency data
2. Parses entries, picking the shortest/best English gloss for each character
3. Filters characters by frequency to stay under OpenType's 65,535 glyph limit
4. Renders each gloss as a bitmap, traces contours, and converts to CFF outlines
5. Builds ligature substitution tables (GSUB) so compound words show as single glosses

## Dependencies

- Python 3.12+
- fonttools
- pillow

## License

- Code: [Unlicense](https://unlicense.org/) (public domain)
- Dictionary data: [CC-CEDICT](https://cc-cedict.org/) (CC BY-SA 4.0)
