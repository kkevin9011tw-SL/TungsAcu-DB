"""把文字轉成 SVG 外框路徑（不依賴檢視端字型與編碼）。

用 macOS 內建字型集（Heiti TC、Songti TC），fontTools 取 glyph 外框。
回傳的 path d 已縮放到目標字級、y 軸向上（字型座標），
呼叫端用 transform="translate(x,y) scale(1,-1)" 翻轉到 SVG 座標。
"""
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTCollection


class Face:
    def __init__(self, path, name):
        coll = TTCollection(path, lazy=True)
        self.font = next(f for f in coll.fonts if f["name"].getDebugName(4) == name)
        self.cmap = self.font.getBestCmap()
        self.glyphs = self.font.getGlyphSet()
        self.upem = self.font["head"].unitsPerEm
        self._cache = {}

    def path_d(self, text, size):
        """回傳 (d, 總寬)。d 座標 = 目標字級、y 向上。"""
        key = (text, size)
        if key in self._cache:
            return self._cache[key]
        s = size / self.upem
        x = 0.0
        parts = []
        for ch in text:
            gname = self.cmap.get(ord(ch))
            if gname is None:
                x += size * 0.5
                continue
            glyph = self.glyphs[gname]
            pen = SVGPathPen(self.glyphs)
            glyph.draw(TransformPen(pen, (s, 0, 0, s, x, 0)))
            d = pen.getCommands()
            if d:
                parts.append(d)
            x += glyph.width * s
        result = (" ".join(parts), x)
        self._cache[key] = result
        return result


SANS = Face("/System/Library/Fonts/STHeiti Light.ttc", "Heiti TC Light")
SANS_BOLD = Face("/System/Library/Fonts/STHeiti Medium.ttc", "Heiti TC Medium")
SERIF_BOLD = Face("/System/Library/Fonts/Supplemental/Songti.ttc", "Songti TC Bold")
