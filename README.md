<h1 align="center">Literal Chinese Font</h1>

<p align="center"><strong>A font that replaces Chinese characters with their English meanings.</strong><br>
Compound words like 火山 render as "volcano" instead of "fire mountain" using OpenType ligatures.</p>

<p align="center">
  <a href="https://thatxliner.github.io/chinese-font/"><img alt="Try it live" src="https://img.shields.io/badge/try%20it-live-667eea"></a>
  <img alt="~6,000 characters" src="https://img.shields.io/badge/characters-~6%2C000-764ba2">
  <img alt="10,000+ ligature compounds" src="https://img.shields.io/badge/ligatures-10%2C000%2B-764ba2">
  <a href="LICENSE"><img alt="License: Unlicense" src="https://img.shields.io/badge/license-Unlicense-475569"></a>
</p>

## Demo

[**Try it live →**](https://thatxliner.github.io/chinese-font/)

Type Chinese text and see it rendered with English glosses in real-time.

## Features

Note that these sizes had to be lowered significantly to be able to be served on the web. Update the MAX_GLYPHS variable in the font-generation code to increase the capability.

- **~6,000+ character/phrase definitions** — sourced from [CC-CEDICT](https://cc-cedict.org/), filtered by frequency for the most common characters
- **10,000+ ligature compounds** — multi-character words render as single glosses (日本→Japan, 图书馆→library, 北京→Beijing)
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
