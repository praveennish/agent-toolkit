"""Tiny helper for hand-laid-out SVG diagrams (standard library only).

Used by build_diagrams.py. Every diagram in ../ is generated from code so it can be
edited and re-rendered: run `python3 build_diagrams.py` then `node render.js`.
"""
from html import escape

FONT = "Inter, 'DejaVu Sans', Arial, sans-serif"

# name: (fill, stroke, title colour)
THEMES = {
    "client":   ("#EEF2FF", "#6366F1", "#3730A3"),
    "edge":     ("#F0F9FF", "#0EA5E9", "#075985"),
    "gateway":  ("#E0F2FE", "#0284C7", "#0C4A6E"),
    "infer":    ("#ECFDF5", "#059669", "#065F46"),
    "repo":     ("#FFF7ED", "#EA580C", "#9A3412"),
    "obs":      ("#F5F3FF", "#7C3AED", "#5B21B6"),
    "platform": ("#F1F5F9", "#64748B", "#334155"),
    "compute":  ("#1E3A8A", "#1E3A8A", "#FFFFFF"),
    "deploy":   ("#FEFCE8", "#CA8A04", "#713F12"),
    "white":    ("#FFFFFF", "#94A3B8", "#0F172A"),
    "danger":   ("#FEF2F2", "#DC2626", "#991B1B"),
    "note":     ("#FFFBEB", "#D97706", "#78350F"),
}

ARROW_COLOURS = {
    "default": "#334155",
    "blue": "#0284C7",
    "green": "#059669",
    "orange": "#EA580C",
    "purple": "#7C3AED",
    "red": "#DC2626",
    "grey": "#94A3B8",
}


class SVG:
    def __init__(self, width, height, bg="#FFFFFF", preserve_space=False):
        self.w, self.h = width, height
        self.parts = []
        self.bg = bg
        # keep leading/multiple spaces in text (used for aligned code-like lines)
        self.preserve_space = preserve_space

    # ---------- primitives ----------
    def rect(self, x, y, w, h, fill, stroke, rx=10, sw=1.5, dash=None, opacity=1.0):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d} fill-opacity="{opacity}"/>'
        )

    def text(self, x, y, s, size=13, weight=400, fill="#0F172A", anchor="start", italic=False):
        style = ' font-style="italic"' if italic else ""
        self.parts.append(
            f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{style}>{escape(s)}</text>'
        )

    def line(self, x1, y1, x2, y2, colour="#94A3B8", sw=1.2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour}" stroke-width="{sw}"{d}/>'
        )

    # ---------- composites ----------
    def box(self, x, y, w, h, title, lines=(), theme="white", title_size=15,
            line_size=12.5, dash=None, align="left", badge=None, line_gap=None):
        fill, stroke, tcol = THEMES[theme]
        self.rect(x, y, w, h, fill, stroke, dash=dash)
        body_col = "#E0E7FF" if theme == "compute" else "#1E293B"
        gap = line_gap or (line_size + 5)
        if align == "center":
            cx = x + w / 2
            self.text(cx, y + 22, title, size=title_size, weight=700, fill=tcol, anchor="middle")
            for i, ln in enumerate(lines):
                self.text(cx, y + 22 + (i + 1) * gap + 2, ln, size=line_size, fill=body_col, anchor="middle")
        else:
            self.text(x + 12, y + 22, title, size=title_size, weight=700, fill=tcol)
            for i, ln in enumerate(lines):
                self.text(x + 12, y + 22 + (i + 1) * gap + 2, ln, size=line_size, fill=body_col)
        if badge:
            bw = 7.2 * len(badge) + 14
            self.rect(x + w - bw - 8, y + 8, bw, 20, stroke, stroke, rx=10, sw=0)
            self.text(x + w - bw / 2 - 8, y + 22, badge, size=11, weight=700, fill="#FFFFFF", anchor="middle")

    def container(self, x, y, w, h, label, theme="platform", dash="6 4"):
        fill, stroke, tcol = THEMES[theme]
        self.rect(x, y, w, h, fill, stroke, rx=14, sw=1.4, dash=dash, opacity=0.55)
        self.text(x + 12, y + 18, label, size=12, weight=700, fill=tcol)

    def arrow(self, points, colour="default", label=None, label_at=None, dashed=False,
              sw=1.6, label_size=11.5, label_anchor="start", label_bg=True):
        c = ARROW_COLOURS.get(colour, colour)
        pts = " ".join(f"{px},{py}" for px, py in points)
        d = ' stroke-dasharray="6 4"' if dashed else ""
        mk = colour if colour in ARROW_COLOURS else "default"
        self.parts.append(
            f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="{sw}"{d} '
            f'marker-end="url(#ah-{mk})" stroke-linejoin="round"/>'
        )
        if label:
            lx, ly = label_at if label_at else points[len(points) // 2]
            self.label(lx, ly, label, colour=c, size=label_size, anchor=label_anchor, bg=label_bg)

    def label(self, x, y, s, colour="#334155", size=11.5, anchor="start", bg=True, weight=600):
        if bg:
            w = len(s) * size * 0.56 + 8
            if anchor == "middle":
                bx = x - w / 2
            elif anchor == "end":
                bx = x - w + 4
            else:
                bx = x - 4
            self.parts.append(
                f'<rect x="{bx}" y="{y - size}" width="{w}" height="{size + 6}" rx="4" '
                f'fill="#FFFFFF" fill-opacity="0.92"/>'
            )
        self.text(x, y, s, size=size, weight=weight, fill=colour, anchor=anchor)

    # ---------- output ----------
    def render(self):
        markers = "".join(
            f'<marker id="ah-{n}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" '
            f'markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
            for n, c in ARROW_COLOURS.items()
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}"'
            # no ligatures: keeps operators such as <=> and -> rendered literally
            + (' style="font-variant-ligatures: none; white-space: pre"' if self.preserve_space
               else ' style="font-variant-ligatures: none"')
            + f'><defs>{markers}</defs>'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="{self.bg}"/>'
            + "".join(self.parts)
            + "</svg>"
        )

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.render())
