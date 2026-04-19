# Literal Chinese Font

A font that replaces Chinese characters with their English meanings. Compound words like 火山 render as "volcano" instead of "fire mountain" using OpenType ligatures.

## Demo

Type Chinese text and see it rendered with English glosses in real-time.

## Features

- **96 character glosses** — common radicals and vocabulary (人→person, 山→mountain, 水→water, etc.)
- **20 ligature compounds** — multi-character words render as single glosses (日本→Japan, 图书馆→library, 北京→Beijing)
- **Fallback rendering** — unsupported characters display normally

## Usage

### Generate the font

```bash
uv run python generate_font.py
```

### Test locally

```bash
python3 -m http.server
# Open http://localhost:8000
```

### Deploy to GitHub Pages

Push to `main` — the workflow regenerates the font and deploys automatically.

## Dependencies

- Python 3.12+
- fonttools
- pillow
