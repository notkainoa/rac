# Makes src/assets/fonts/newsreader-display.woff2: Newsreader with its
# optical size fixed at 72 (the display cut, the only size the site uses) and
# weights limited to 300-600. That's about 40% of the full variable file, and
# it's the font the hero headline waits on.
#
#   pip install fonttools brotli
#   python3 scripts/make-display-font.py
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

site = Path(__file__).resolve().parent.parent
src = site / "node_modules/@fontsource-variable/newsreader/files/newsreader-latin-opsz-normal.woff2"
out = site / "src/assets/fonts/newsreader-display.woff2"

font = instancer.instantiateVariableFont(TTFont(src), {"opsz": 72, "wght": (300, 600)})
font.flavor = "woff2"
font.save(out)
