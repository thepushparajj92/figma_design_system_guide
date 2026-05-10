#!/usr/bin/env python3
"""Design System Reference PDF Generator"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import Color, white, black
import os

W, H = A4  # 595.27 x 841.89 pts
ML = 20 * mm
MR = 20 * mm
MT = 22 * mm
MB = 18 * mm
CW = W - ML - MR

FONT   = "Helvetica"
FONT_B = "Helvetica-Bold"

OUTPUT = "./design_system.pdf"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def hc(h):
    h = h.lstrip("#")
    if len(h) == 8:
        return Color(int(h[0:2],16)/255, int(h[2:4],16)/255,
                     int(h[4:6],16)/255, int(h[6:8],16)/255)
    return Color(int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255)

def lum(h):
    h = h.lstrip("#")[:6]
    r,g,b = int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
    return 0.299*r + 0.587*g + 0.114*b

def text_on(h):
    return white if lum(h) < 0.52 else hc("#111827")

def page_header(c, title, subtitle, accent="#ec4899",
                bg="#ffffff", title_col="#111827", sub_col="#6b7280"):
    c.setFillColor(hc(bg))
    c.rect(0, 0, W, H, fill=1, stroke=0)
    # Top accent bar
    c.setFillColor(hc(accent))
    c.rect(0, H - 2.5*mm, W, 2.5*mm, fill=1, stroke=0)
    # Title
    c.setFont(FONT_B, 22)
    c.setFillColor(hc(title_col))
    c.drawString(ML, H - MT - 4, title)
    # Subtitle
    c.setFont(FONT, 9)
    c.setFillColor(hc(sub_col))
    c.drawString(ML, H - MT - 18, subtitle)
    # Divider
    c.setStrokeColor(hc("#e5e7eb"))
    c.setLineWidth(0.5)
    c.line(ML, H - MT - 26, W - MR, H - MT - 26)
    return H - MT - 40

def chip_label(c, x, y, label, bg, text_col="#ffffff", r=3):
    w = len(label) * 5.3 + 10
    c.setFillColor(hc(bg))
    c.roundRect(x, y - 1, w, 12, r, fill=1, stroke=0)
    c.setFillColor(hc(text_col) if isinstance(text_col, str) else text_col)
    c.setFont(FONT_B, 6.5)
    c.drawString(x + 5, y + 2, label)
    return w

# ─── Token Data ───────────────────────────────────────────────────────────────

BRAND = {
    "pink":  ("#ec4899", "Primary",
              ["#fdf2f8","#fce7f3","#fbcfe8","#f9a8d4","#f472b6",
               "#ec4899","#db2777","#be185d","#9d174d","#831843","#500724","#0f172a","#020617"]),
    "gray":  ("#6b7280", "Neutral",
              ["#fafbfc","#f3f4f6","#e5e7eb","#d1d5db","#9ca3af",
               "#6b7280","#4b5563","#374151","#1f2937","#111827","#0f172a","#020617","#000000"]),
    "green": ("#22c55e", "Success",
              ["#ecfdf5","#d1fae5","#bbf7d0","#86efac","#4ade80",
               "#22c55e","#16a34a","#15803d","#166534","#14532d","#064e3b","#022c22","#011511"]),
    "red":   ("#ef4444", "Error",
              ["#fef2f2","#fee2e2","#fecaca","#fca5a5","#f87171",
               "#ef4444","#dc2626","#b91c1c","#991b1b","#7f1d1d","#6b1010","#450a0a","#2d0606"]),
    "amber": ("#f59e0b", "Warning",
              ["#fffbeb","#fef3c7","#fde68a","#fcd34d","#fbbf24",
               "#f59e0b","#d97706","#b45309","#92400e","#78350f","#451a03","#2d1001","#1a0800"]),
    "teal":  ("#14b8a6", "Info",
              ["#f0fdfa","#ccfbf1","#99f6e4","#5eead4","#2dd4bf",
               "#14b8a6","#0d9488","#0f766e","#115e59","#134e4a","#0d3b37","#052e28","#011a16"]),
}
SCALE_LABELS = ["50","100","200","300","400","500","600","700","800","900","1k","1.1k","1.2k"]

SEMANTIC = {
    "primary":     {"subtle":"#fdf2f8","muted":"#fbcfe8","default":"#ec4899","emphasis":"#be185d","on":"#ffffff"},
    "neutral":     {"subtle":"#fafbfc","muted":"#e5e7eb","default":"#6b7280","emphasis":"#374151","on":"#ffffff"},
    "error":       {"subtle":"#fef2f2","muted":"#fecaca","default":"#ef4444","emphasis":"#b91c1c","on":"#ffffff"},
    "warning":     {"subtle":"#fffbeb","muted":"#fde68a","default":"#f59e0b","emphasis":"#b45309","on":"#78350f"},
    "success":     {"subtle":"#ecfdf5","muted":"#bbf7d0","default":"#22c55e","emphasis":"#15803d","on":"#ffffff"},
    "information": {"subtle":"#f0fdfa","muted":"#99f6e4","default":"#14b8a6","emphasis":"#0f766e","on":"#ffffff"},
}

THEME = {
    "light": {
        "bg_page":    "#ffffff",
        "accent":     "#ec4899",
        "title_col":  "#111827",
        "sub_col":    "#6b7280",
        "label_col":  "#6b7280",
        "hex_col":    "#9ca3af",
        "border_col": "#e5e7eb",
        "sections": [
            ("BACKGROUND", "#ec4899", [
                ("page",     "#f8fafc"),
                ("subtle",   "#f1f5f9"),
                ("elevated", "#ffffff"),
                ("overlay",  "#0000007a"),
                ("scrim",    "#00000052"),
            ]),
            ("SURFACE", "#14b8a6", [
                ("default",     "#ffffff"),
                ("subtle",      "#f8fafc"),
                ("raised",      "#ffffff"),
                ("error",       "#fef2f2"),
                ("warning",     "#fffbeb"),
                ("success",     "#ecfdf5"),
                ("information", "#f0fdfa"),
            ]),
            ("CONTENT", "#374151", [
                ("primary",   "#111827"),
                ("secondary", "#4b5563"),
                ("tertiary",  "#9ca3af"),
                ("disabled",  "#d1d5db"),
                ("inverse",   "#ffffff"),
                ("onPrimary", "#ffffff"),
                ("onError",   "#ffffff"),
                ("onWarning", "#78350f"),
            ]),
            ("CONTENT STATUS", "#ef4444", [
                ("error",       "#dc2626"),
                ("warning",     "#b45309"),
                ("success",     "#15803d"),
                ("information", "#0d9488"),
            ]),
            ("ACTION", "#be185d", [
                ("primary·default",   "#ec4899"),
                ("primary·pressed",   "#be185d"),
                ("primary·disabled",  "#fbcfe8"),
                ("secondary·default", "#f1f5f9"),
                ("secondary·pressed", "#cbd5e1"),
                ("destruct·default",  "#ef4444"),
                ("destruct·pressed",  "#b91c1c"),
                ("ghost·pressed",     "#0f172a1f"),
            ]),
            ("INPUT BORDER", "#f59e0b", [
                ("default",  "#d1d5db"),
                ("focused",  "#ec4899"),
                ("disabled", "#e5e7eb"),
                ("error",    "#ef4444"),
                ("success",  "#22c55e"),
            ]),
            ("BORDER", "#9ca3af", [
                ("subtle",  "#f3f4f6"),
                ("default", "#e5e7eb"),
                ("strong",  "#9ca3af"),
                ("focus",   "#ec4899"),
            ]),
        ]
    },
    "dark": {
        "bg_page":    "#0f172a",
        "accent":     "#f472b6",
        "title_col":  "#f1f5f9",
        "sub_col":    "#94a3b8",
        "label_col":  "#94a3b8",
        "hex_col":    "#64748b",
        "border_col": "#334155",
        "sections": [
            ("BACKGROUND", "#f472b6", [
                ("page",     "#0f172a"),
                ("subtle",   "#0a0f1e"),
                ("elevated", "#1e293b"),
                ("overlay",  "#0000007a"),
                ("scrim",    "#00000052"),
            ]),
            ("SURFACE", "#2dd4bf", [
                ("default",     "#1e293b"),
                ("subtle",      "#0f172a"),
                ("raised",      "#293548"),
                ("error",       "#2d0a0a"),
                ("warning",     "#1a0f03"),
                ("success",     "#042014"),
                ("information", "#011a16"),
            ]),
            ("CONTENT", "#94a3b8", [
                ("primary",   "#f1f5f9"),
                ("secondary", "#94a3b8"),
                ("tertiary",  "#64748b"),
                ("disabled",  "#475569"),
                ("inverse",   "#0f172a"),
                ("onPrimary", "#ffffff"),
                ("onError",   "#ffffff"),
                ("onWarning", "#78350f"),
            ]),
            ("CONTENT STATUS", "#f87171", [
                ("error",       "#f87171"),
                ("warning",     "#fbbf24"),
                ("success",     "#4ade80"),
                ("information", "#2dd4bf"),
            ]),
            ("ACTION", "#f9a8d4", [
                ("primary·default",   "#f472b6"),
                ("primary·pressed",   "#fbcfe8"),
                ("primary·disabled",  "#831843"),
                ("secondary·default", "#1e293b"),
                ("secondary·pressed", "#334155"),
                ("destruct·default",  "#f87171"),
                ("destruct·pressed",  "#fecaca"),
                ("ghost·pressed",     "#ffffff1f"),
            ]),
            ("INPUT BORDER", "#fbbf24", [
                ("default",  "#334155"),
                ("focused",  "#f472b6"),
                ("disabled", "#1e293b"),
                ("error",    "#f87171"),
                ("success",  "#4ade80"),
            ]),
            ("BORDER", "#64748b", [
                ("subtle",  "#1e293b"),
                ("default", "#334155"),
                ("strong",  "#475569"),
                ("focus",   "#f472b6"),
            ]),
        ]
    }
}

TYPOGRAPHY = [
    # (name, sample, font_size, line_height, letter_spacing, weight_name, font_family)
    ("displayHero",   "The quick brown fox jumps",    34, 40, -1.0,   "Bold",      "Inter"),
    ("displayLarge",  "The quick brown fox jumps",    28, 34, -0.5,   "Bold",      "Inter"),
    ("displayMedium", "The quick brown fox jumps",    24, 30, -0.25,  "Bold",      "Inter"),
    ("displaySmall",  "The quick brown fox jumps",    20, 26, -0.25,  "SemiBold",  "Inter"),
    ("headlineLarge", "The quick brown fox jumps",    18, 24, -0.15,  "SemiBold",  "Inter"),
    ("headlineMedium","The quick brown fox",          16, 22,  0.0,   "SemiBold",  "Inter"),
    ("headlineSmall", "The quick brown fox",          14, 20,  0.0,   "SemiBold",  "Inter"),
    ("titleLarge",    "The quick brown fox",          16, 22,  0.0,   "Medium",    "Inter"),
    ("titleMedium",   "The quick brown fox",          14, 20,  0.1,   "Medium",    "Inter"),
    ("titleSmall",    "The quick brown fox",          13, 18,  0.1,   "Medium",    "Inter"),
    ("bodyLarge",     "The quick brown fox jumps over the lazy dog",  16, 24, 0.0, "Regular", "Inter"),
    ("bodyMedium",    "The quick brown fox jumps over the lazy dog",  14, 22, 0.0, "Regular", "Inter"),
    ("bodySmall",     "The quick brown fox jumps over the lazy dog",  13, 20, 0.0, "Regular", "Inter"),
    ("labelLarge",    "Button Label",                 14, 20,  0.1,   "Medium",    "Inter"),
    ("labelMedium",   "Field Label",                  12, 18,  0.25,  "Medium",    "Inter"),
    ("labelSmall",    "SMALL LABEL",                  11, 16,  0.5,   "Medium",    "Inter"),
    ("caption",       "Helper text or caption",       11, 16,  0.0,   "Regular",   "Inter"),
    ("overline",      "SECTION OVERLINE",             11, 16,  1.0,   "SemiBold",  "Inter"),
    ("code",          "TXN-20240510-4829A",           13, 20,  0.0,   "Regular",   "JetBrains Mono"),
]

# ─── Page Drawers ─────────────────────────────────────────────────────────────

def draw_cover(c):
    # Background
    c.setFillColor(hc("#0f172a"))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Decorative blobs
    blobs = [
        (W - 30*mm, H - 25*mm, 55*mm, "#ec4899", 0.12),
        (W - 10*mm, H - 75*mm, 75*mm, "#14b8a6", 0.08),
        (W - 80*mm, H - 15*mm, 35*mm, "#f59e0b", 0.10),
        (50*mm,     20*mm,     45*mm, "#22c55e", 0.07),
    ]
    for bx, by, br, col, alpha in blobs:
        r, g, b = [int(col.lstrip("#")[i:i+2],16)/255 for i in (0,2,4)]
        c.setFillColor(Color(r, g, b, alpha=alpha))
        c.circle(bx, by, br, fill=1, stroke=0)

    # Bottom color strip
    strip = ["#ec4899","#22c55e","#ef4444","#f59e0b","#14b8a6","#6b7280"]
    sw = W / len(strip)
    for i, col in enumerate(strip):
        c.setFillColor(hc(col))
        c.rect(i * sw, 0, sw, 8*mm, fill=1, stroke=0)

    # Token file pills
    pills = [("colors_new.json","#ec4899"), ("typography_new.json","#14b8a6"), ("dimension_new.json","#f59e0b")]
    px = ML
    py = H - 48*mm
    for label, col in pills:
        pw = len(label) * 5.6 + 20
        r,g,b = [int(col.lstrip("#")[i:i+2],16)/255 for i in (0,2,4)]
        c.setFillColor(Color(r, g, b, alpha=0.22))
        c.roundRect(px, py - 8, pw, 18, 9, fill=1, stroke=0)
        c.setFillColor(hc(col))
        c.setFont(FONT_B, 8)
        c.drawString(px + 10, py - 1, label)
        px += pw + 8

    # Title
    c.setFillColor(white)
    c.setFont(FONT_B, 56)
    c.drawString(ML, H*0.5 + 30, "Design")
    c.setFont(FONT_B, 56)
    c.drawString(ML, H*0.5 - 30, "System")

    # Blue underline
    c.setFillColor(hc("#ec4899"))
    c.rect(ML, H*0.5 - 44, 72, 3.5, fill=1, stroke=0)

    # Tagline
    c.setFont(FONT, 12)
    c.setFillColor(hc("#94a3b8"))
    c.drawString(ML, H*0.5 - 64, "Colors  ·  Typography  ·  Dimensions")

    # Role legend bottom right
    roles = [("Primary","#ec4899"),("Success","#22c55e"),("Error","#ef4444"),
             ("Warning","#f59e0b"),("Info","#14b8a6"),("Neutral","#6b7280")]
    lx = W - MR - len(roles)*40 + 4
    ly = 22*mm
    for name, col in roles:
        c.setFillColor(hc(col))
        c.circle(lx + 5, ly, 5, fill=1, stroke=0)
        c.setFont(FONT, 7)
        c.setFillColor(hc("#94a3b8"))
        c.drawString(lx + 13, ly - 3, name)
        lx += 40

    # Page number style footer
    c.setFont(FONT, 8)
    c.setFillColor(hc("#334155"))
    c.drawCentredString(W/2, 14*mm, "Design Tokens Reference  ·  2025")


def draw_brand_palette(c):
    y = page_header(c, "Brand Palette",
                    "Primitive color scales — the raw material. Never reference these directly in components.",
                    accent="#ec4899")
    y -= 6

    n_swatches = 13
    sw = (CW - (n_swatches - 1) * 2) / n_swatches
    row_h = 46
    label_gap = 18
    row_total = row_h + label_gap + 10

    for family, (accent, role, shades) in BRAND.items():
        if y - row_total < MB:
            break

        # Family name + role tag
        c.setFont(FONT_B, 9)
        c.setFillColor(hc("#111827"))
        c.drawString(ML, y, family.upper())
        tag_x = ML + len(family) * 6.4 + 4
        chip_label(c, tag_x, y, role, accent,
                   text_col=("#78350f" if accent == "#f59e0b" else "#ffffff"))
        y -= 10

        for i, (shade, label) in enumerate(zip(shades, SCALE_LABELS)):
            sx = ML + i * (sw + 2)
            # Swatch
            c.setFillColor(hc(shade))
            c.roundRect(sx, y - row_h, sw, row_h, 3, fill=1, stroke=0)
            # Scale label inside
            tc = text_on(shade)
            c.setFillColor(tc)
            c.setFont(FONT_B, 6)
            c.drawCentredString(sx + sw/2, y - 11, label)
            # Hex below
            c.setFont(FONT, 5.2)
            c.setFillColor(hc("#9ca3af"))
            c.drawCentredString(sx + sw/2, y - row_h - 8, shade[1:].upper())

        y -= row_h + label_gap + 10


def draw_semantic(c):
    y = page_header(c, "Semantic Tokens",
                    "Role-based aliases giving meaning to primitive values. "
                    "subtle = bg tint · muted = badge bg · default = fill · emphasis = pressed · on = text on default",
                    accent="#14b8a6")
    y -= 10

    card_w  = (CW - 12) / 2
    card_h  = 126
    col_gap = 12
    row_gap = 12
    sw_keys = ["subtle", "muted", "default", "emphasis"]

    for i, (role, vals) in enumerate(SEMANTIC.items()):
        col  = i % 2
        row  = i // 2
        cx   = ML + col * (card_w + col_gap)
        cy   = y - row * (card_h + row_gap)

        if cy - card_h < MB:
            break

        # Card shell
        c.setFillColor(hc("#f8fafc"))
        c.setStrokeColor(hc("#e5e7eb"))
        c.setLineWidth(0.5)
        c.roundRect(cx, cy - card_h, card_w, card_h, 8, fill=1, stroke=1)

        # Left accent bar
        c.setFillColor(hc(vals["default"]))
        c.roundRect(cx, cy - card_h, 4, card_h, 2, fill=1, stroke=0)

        # Role name
        c.setFont(FONT_B, 11)
        c.setFillColor(hc(vals["default"]))
        c.drawString(cx + 14, cy - 20, role.upper())

        # "on" pill — right aligned
        on_col = vals["on"]
        on_bg  = vals["default"]
        pill_w = 52
        pill_x = cx + card_w - pill_w - 10
        c.setFillColor(hc(on_bg))
        c.roundRect(pill_x, cy - 24, pill_w, 14, 7, fill=1, stroke=0)
        c.setFillColor(hc(on_col))
        c.setFont(FONT_B, 6.5)
        c.drawCentredString(pill_x + pill_w/2, cy - 17, f"on · {on_col[1:].upper()}")

        # Swatches
        n   = len(sw_keys)
        sw  = (card_w - 24 - (n-1)*3) / n
        svh = 46
        svy = cy - 44

        for j, key in enumerate(sw_keys):
            sx    = cx + 12 + j * (sw + 3)
            shade = vals[key]

            c.setFillColor(hc(shade))
            c.setStrokeColor(hc("#e5e7eb"))
            c.setLineWidth(0.3)
            c.roundRect(sx, svy - svh, sw, svh, 4, fill=1, stroke=1)

            tc = text_on(shade)
            c.setFillColor(tc)
            c.setFont(FONT_B, 6)
            c.drawCentredString(sx + sw/2, svy - 13, key)

            c.setFillColor(hc("#9ca3af"))
            c.setFont(FONT, 5.2)
            c.drawCentredString(sx + sw/2, svy - svh - 8, shade[1:].upper())


def draw_theme_page(c, mode):
    t = THEME[mode]
    is_dark = (mode == "dark")

    y = page_header(c, f"Theme — {mode.capitalize()}",
                    f"All component-level color tokens for {mode} mode, fully resolved to hex values.",
                    accent=t["accent"], bg=t["bg_page"],
                    title_col=t["title_col"], sub_col=t["sub_col"])

    # Re-draw background fully (page_header may not cover all)
    c.setFillColor(hc(t["bg_page"]))
    c.rect(0, 0, W, H - 3*mm, fill=1, stroke=0)
    # Reprint header text on top
    c.setFillColor(hc(t["accent"]))
    c.rect(0, H - 2.5*mm, W, 2.5*mm, fill=1, stroke=0)
    c.setFont(FONT_B, 22)
    c.setFillColor(hc(t["title_col"]))
    c.drawString(ML, H - MT - 4, f"Theme — {mode.capitalize()}")
    c.setFont(FONT, 9)
    c.setFillColor(hc(t["sub_col"]))
    c.drawString(ML, H - MT - 18, f"All component-level color tokens for {mode} mode, fully resolved to hex values.")
    c.setStrokeColor(hc(t["border_col"]))
    c.setLineWidth(0.5)
    c.line(ML, H - MT - 26, W - MR, H - MT - 26)
    y = H - MT - 40
    y -= 6

    for sec_title, sec_accent, tokens in t["sections"]:
        if y - 70 < MB:
            break

        # Section heading
        c.setFont(FONT_B, 7.5)
        c.setFillColor(hc(sec_accent))
        c.drawString(ML, y, sec_title)
        c.setStrokeColor(hc(sec_accent))
        c.setLineWidth(1.2)
        c.line(ML, y - 3, ML + len(sec_title) * 5.2, y - 3)
        y -= 10

        # Token chips
        n      = len(tokens)
        chip_h = 38
        chip_w = min((CW - (n - 1) * 5) / n, 82)
        cx_    = ML

        for name, hex_val in tokens:
            # Handle alpha colors — display as checkerboard hint
            is_alpha = len(hex_val) == 9  # #rrggbbaa
            if is_alpha:
                c.setFillColor(hc("#ffffff" if not is_dark else "#293548"))
                c.setStrokeColor(hc(t["border_col"]))
                c.setLineWidth(0.4)
                c.roundRect(cx_, y - chip_h, chip_w, chip_h, 4, fill=1, stroke=1)
                # Diagonal stripe overlay to hint transparency
                c.setStrokeColor(hc("#d1d5db" if not is_dark else "#334155"))
                c.setLineWidth(0.3)
                for offset in range(int(-chip_h), int(chip_w + chip_h), 6):
                    c.line(cx_ + max(0, offset), y, cx_ + min(chip_w, offset + chip_h), y - min(chip_h, chip_w - offset + chip_h))
            else:
                c.setFillColor(hc(hex_val))
                c.setStrokeColor(hc(t["border_col"]))
                c.setLineWidth(0.4)
                c.roundRect(cx_, y - chip_h, chip_w, chip_h, 4, fill=1, stroke=1)

            # Token name
            if is_alpha:
                c.setFillColor(hc(t["label_col"]))
            else:
                lv = lum(hex_val)
                if lv < 0.52:
                    c.setFillColor(white)
                elif lv > 0.88:
                    c.setFillColor(hc("#9ca3af"))
                else:
                    c.setFillColor(hc("#374151"))
            c.setFont(FONT_B, 5.8)
            c.drawCentredString(cx_ + chip_w/2, y - 14, name.replace("·","·"))

            # Hex value
            c.setFillColor(hc(t["hex_col"]))
            c.setFont(FONT, 5.2)
            display_hex = "alpha" if is_alpha else hex_val[1:].upper()
            c.drawCentredString(cx_ + chip_w/2, y - chip_h - 8, display_hex)

            cx_ += chip_w + 5

        y -= chip_h + 20


def draw_typography(c):
    y = page_header(c, "Typography Scale",
                    "Inter (sans) · JetBrains Mono (code)  —  All values shown are mobile sizes in sp/dp",
                    accent="#f59e0b")
    y -= 6

    font_map = {
        "Bold":           FONT_B,
        "SemiBold":       FONT_B,
        "Medium":         FONT,
        "Regular":        FONT,
        "Regular · Mono": FONT,
    }

    # Column headers
    cols = [
        ("STYLE",    ML,       60),
        ("FONT",     ML + 74,  50),
        ("SAMPLE",   ML + 128, 200),
        ("SIZE",     ML + 336, 24),
        ("LH",       ML + 362, 20),
        ("LS",       ML + 386, 26),
        ("WEIGHT",   ML + 418, 60),
    ]
    c.setFont(FONT_B, 6.5)
    c.setFillColor(hc("#9ca3af"))
    for label, lx, _ in cols:
        c.drawString(lx, y, label)
    y -= 5
    c.setStrokeColor(hc("#e5e7eb"))
    c.setLineWidth(0.5)
    c.line(ML, y, W - MR, y)
    y -= 6

    accent_colors = {
        "Bold": "#ec4899", "SemiBold": "#14b8a6",
        "Medium": "#f59e0b", "Regular": "#6b7280",
    }

    for name, sample, fs, lh, ls, fw_name, font_family in TYPOGRAPHY:
        row_h = max(lh + 4, 18)
        if y - row_h < MB:
            break

        # Style name
        c.setFont(FONT, 7.5)
        c.setFillColor(hc("#6b7280"))
        c.drawString(ML, y - 5, name)

        # Font family
        is_mono = font_family != "Inter"
        c.setFont(FONT, 6.5)
        c.setFillColor(hc("#ef4444" if is_mono else "#374151"))
        c.drawString(ML + 74, y - 5, font_family)

        # Sample text (capped render size, clipped)
        render_fs = min(fs, 20)
        font = font_map.get(fw_name, FONT)
        c.setFont(font, render_fs)
        c.setFillColor(hc("#111827"))
        c.saveState()
        p = c.beginPath()
        p.rect(ML + 128, y - row_h, 202, row_h + 2)
        c.clipPath(p, stroke=0)
        c.drawString(ML + 128, y - render_fs + 4, sample)
        c.restoreState()

        # Properties
        c.setFont(FONT, 7.5)
        c.setFillColor(hc("#374151"))
        c.drawString(ML + 336, y - 5, str(fs))
        c.drawString(ML + 362, y - 5, str(lh))
        c.drawString(ML + 386, y - 5, str(ls))

        # Weight tag
        wc = accent_colors.get(fw_name, "#6b7280")
        c.setFillColor(hc(wc))
        c.setFont(FONT_B, 6.5)
        c.drawString(ML + 418, y - 5, fw_name)

        # Row divider
        c.setStrokeColor(hc("#f3f4f6"))
        c.setLineWidth(0.3)
        c.line(ML, y - row_h, W - MR, y - row_h)

        y -= row_h


def draw_dimensions(c):
    y = page_header(c, "Dimensions",
                    "Spacing · Border radius · Border widths · Elevation · Animation · Opacity · Breakpoints",
                    accent="#22c55e")
    y -= 8

    def section_title(c, label, accent, y):
        c.setFont(FONT_B, 8.5)
        c.setFillColor(hc(accent))
        c.drawString(ML, y, label)
        c.setStrokeColor(hc(accent))
        c.setLineWidth(1.5)
        c.line(ML, y - 3, ML + len(label) * 5.5, y - 3)
        return y - 14

    # ── Spacing ──────────────────────────────────────────────────────────────
    y = section_title(c, "SPACING SCALE  (dp)", "#22c55e", y)
    spacing = [0,2,4,6,8,10,12,16,20,24,32,40,48,64,80,96]
    bar_area = CW * 0.58
    bar_h    = 8
    bar_gap  = 4

    for val in spacing:
        bw = max((val / 96) * bar_area, 2)
        alpha_v = 0.3 + 0.7 * (val / 96) if val > 0 else 0.2
        c.setFillColor(Color(0.09, 0.56, 0.29, alpha=alpha_v))
        c.roundRect(ML, y - bar_h, bw, bar_h, 2, fill=1, stroke=0)
        c.setFont(FONT, 6.5)
        c.setFillColor(hc("#374151"))
        c.drawString(ML + bar_area + 8, y - bar_h + 1, f"{val} dp")
        y -= bar_h + bar_gap
    y -= 10

    # ── Border Radius ─────────────────────────────────────────────────────────
    y = section_title(c, "BORDER RADIUS", "#ec4899", y)
    radii = [("none",0),("xs",2),("sm",4),("md",8),("lg",12),("xl",16),("2xl",20),("3xl",24),("full",9999)]
    box_s = 36
    box_g = 7
    rx_   = ML

    for name, r in radii:
        disp_r = min(r, box_s / 2)
        c.setFillColor(hc("#fdf2f8"))
        c.setStrokeColor(hc("#ec4899"))
        c.setLineWidth(1)
        c.roundRect(rx_, y - box_s, box_s, box_s, disp_r, fill=1, stroke=1)
        c.setFont(FONT_B, 6)
        c.setFillColor(hc("#be185d"))
        c.drawCentredString(rx_ + box_s/2, y - box_s/2 - 3, name)
        c.setFont(FONT, 5.5)
        c.setFillColor(hc("#9ca3af"))
        c.drawCentredString(rx_ + box_s/2, y - box_s - 8, "∞" if r == 9999 else f"{r}")
        rx_ += box_s + box_g

    y -= box_s + 18

    # Semantic radius
    sem_r = [("button",12),("input",12),("card",16),("modal",24),("chip",20),("badge",6),("avatar",9999)]
    c.setFont(FONT_B, 7)
    c.setFillColor(hc("#6b7280"))
    c.drawString(ML, y, "Semantic  →")
    rx_ = ML + 58
    for name, r in sem_r:
        disp_r = min(r, 12)
        pw = max(len(name) * 5.4 + 12, 34)
        c.setFillColor(hc("#f0fdfa"))
        c.setStrokeColor(hc("#14b8a6"))
        c.setLineWidth(0.8)
        c.roundRect(rx_, y - 18, pw, 18, disp_r, fill=1, stroke=1)
        c.setFont(FONT, 6.2)
        c.setFillColor(hc("#0f766e"))
        c.drawCentredString(rx_ + pw/2, y - 11, f"{name} · {'∞' if r==9999 else r}")
        rx_ += pw + 5
    y -= 30

    # ── Border Widths ─────────────────────────────────────────────────────────
    y = section_title(c, "BORDER WIDTHS", "#ef4444", y)
    bw_items = [("hairline", 0.5), ("thin", 1), ("medium", 2), ("thick", 4)]
    bx_ = ML
    for name, bw in bw_items:
        c.setStrokeColor(hc("#111827"))
        c.setLineWidth(bw)
        c.line(bx_, y - 8, bx_ + 55, y - 8)
        c.setFont(FONT_B, 7)
        c.setFillColor(hc("#374151"))
        c.drawString(bx_, y - 20, name)
        c.setFont(FONT, 6.5)
        c.setFillColor(hc("#9ca3af"))
        c.drawString(bx_, y - 29, f"{bw} pt")
        bx_ += 76
    y -= 40

    # ── Elevation ─────────────────────────────────────────────────────────────
    y = section_title(c, "ELEVATION  (Flutter dp)", "#f59e0b", y)
    elev = [("none",0),("xs",1),("sm",2),("md",4),("lg",8),("xl",16),("2xl",24)]
    ex_ = ML
    card_w_ = 52
    card_h_ = 30

    for name, dp in elev:
        if dp > 0:
            s = min(dp * 0.7, 7)
            c.setFillColor(Color(0, 0, 0, alpha=min(dp * 0.022 + 0.04, 0.22)))
            c.roundRect(ex_ + s/2, y - card_h_ - s, card_w_, card_h_, 4, fill=1, stroke=0)
        c.setFillColor(white)
        c.setStrokeColor(hc("#e5e7eb"))
        c.setLineWidth(0.5)
        c.roundRect(ex_, y - card_h_, card_w_, card_h_, 4, fill=1, stroke=1)
        c.setFont(FONT_B, 7)
        c.setFillColor(hc("#374151"))
        c.drawCentredString(ex_ + card_w_/2, y - card_h_/2 - 2, name)
        c.setFont(FONT, 6)
        c.setFillColor(hc("#9ca3af"))
        c.drawCentredString(ex_ + card_w_/2, y - card_h_ + 6, f"{dp} dp")
        ex_ += card_w_ + 8
    y -= card_h_ + 22

    # ── Opacity ───────────────────────────────────────────────────────────────
    y = section_title(c, "OPACITY", "#14b8a6", y)
    op_items = [("disabled","0.38"),("pressed","0.12"),("focus","0.12"),("overlay","0.48"),("scrim","0.32")]
    ox_ = ML
    op_s = 46
    for name, val in op_items:
        alpha_v = float(val)
        c.setFillColor(hc("#f3f4f6"))
        c.roundRect(ox_, y - op_s, op_s, op_s, 4, fill=1, stroke=0)
        c.setFillColor(Color(0.082, 0.714, 0.651, alpha=alpha_v))
        c.roundRect(ox_, y - op_s, op_s, op_s, 4, fill=1, stroke=0)
        c.setFont(FONT_B, 6.5)
        c.setFillColor(hc("#374151"))
        c.drawCentredString(ox_ + op_s/2, y - op_s - 9, name)
        c.setFont(FONT, 6)
        c.setFillColor(hc("#9ca3af"))
        c.drawCentredString(ox_ + op_s/2, y - op_s - 17, val)
        ox_ += op_s + 10
    y -= op_s + 28

    # ── Animation ─────────────────────────────────────────────────────────────
    y = section_title(c, "ANIMATION DURATION  (ms)", "#6b7280", y)
    dur_items = [("instant",0),("fast",100),("normal",200),("slow",300),("slower",500)]
    dx_ = ML
    track_w = 88
    for name, ms in dur_items:
        fill_w = (ms / 500) * track_w if ms > 0 else 2
        c.setFillColor(hc("#e5e7eb"))
        c.roundRect(dx_, y - 10, track_w, 10, 5, fill=1, stroke=0)
        c.setFillColor(hc("#374151"))
        c.roundRect(dx_, y - 10, max(fill_w, 2), 10, 5, fill=1, stroke=0)
        c.setFont(FONT_B, 7)
        c.setFillColor(hc("#374151"))
        c.drawString(dx_, y - 20, name)
        c.setFont(FONT, 6.5)
        c.setFillColor(hc("#9ca3af"))
        c.drawString(dx_, y - 29, f"{ms} ms")
        dx_ += track_w + 12
    y -= 38

    # ── Breakpoints ───────────────────────────────────────────────────────────
    y = section_title(c, "BREAKPOINTS", "#be185d", y)
    bps = [("mobile", "≥ 0 dp", "Default — phone"), ("tablet", "≥ 600 dp", "Wider layout, side nav")]
    bpx_ = ML
    for bp_name, bp_val, bp_desc in bps:
        c.setFillColor(hc("#fdf2f8"))
        c.setStrokeColor(hc("#ec4899"))
        c.setLineWidth(0.8)
        c.roundRect(bpx_, y - 26, 155, 26, 6, fill=1, stroke=1)
        c.setFont(FONT_B, 8)
        c.setFillColor(hc("#be185d"))
        c.drawString(bpx_ + 10, y - 11, f"{bp_name}  {bp_val}")
        c.setFont(FONT, 7)
        c.setFillColor(hc("#6b7280"))
        c.drawString(bpx_ + 10, y - 22, bp_desc)
        bpx_ += 168


def draw_hierarchy(c):
    y = page_header(c, "Color Hierarchy",
                    "How color layers stack — background → surface → content, and when to use onColor tokens.",
                    accent="#ec4899")
    y -= 4

    lt = THEME["light"]
    dk = THEME["dark"]

    def get_tok(theme, section, name):
        for sec_title, _, tokens in theme["sections"]:
            if sec_title == section:
                for tname, tval in tokens:
                    if tname == name:
                        return tval
        return "#ff00ff"

    half_w = (CW - 16) / 2

    def draw_scenario(c, x, y, w, title, desc, layers, theme, is_dark):
        bg = theme["bg_page"]
        lbl_col = theme["label_col"]
        border = theme["border_col"]

        c.setFont(FONT_B, 8)
        c.setFillColor(hc(theme["title_col"]))
        c.drawString(x, y, title)
        c.setFont(FONT, 6.5)
        c.setFillColor(hc(lbl_col))
        c.drawString(x, y - 11, desc)
        y -= 20

        total_h = 120
        c.setFillColor(hc(layers[0][1]))
        c.setStrokeColor(hc(border))
        c.setLineWidth(0.5)
        c.roundRect(x, y - total_h, w, total_h, 6, fill=1, stroke=1)

        c.setFont(FONT, 5.5)
        c.setFillColor(hc(lbl_col))
        c.drawString(x + 6, y - 12, layers[0][0])

        if len(layers) >= 2:
            inset = 14
            inner_w = w - inset * 2
            inner_h = total_h - 34
            inner_y = y - 22

            c.setFillColor(hc(layers[1][1]))
            c.setStrokeColor(hc(border))
            c.setLineWidth(0.4)
            c.roundRect(x + inset, inner_y - inner_h, inner_w, inner_h, 5, fill=1, stroke=1)

            c.setFont(FONT, 5.5)
            c.setFillColor(hc(lbl_col))
            c.drawString(x + inset + 6, inner_y - 12, layers[1][0])

            if len(layers) >= 3:
                txt_label = layers[2][0]
                txt_col = layers[2][1]
                c.setFont(FONT_B, 14)
                c.setFillColor(hc(txt_col))
                c.drawString(x + inset + 12, inner_y - inner_h + 20, "Aa Text")
                c.setFont(FONT, 5.5)
                c.setFillColor(hc(lbl_col))
                c.drawString(x + inset + 12, inner_y - inner_h + 10, txt_label)

        return y - total_h - 8

    def draw_action_scenario(c, x, y, w, title, desc, bg_hex, btn_hex, text_hex, action_label, label_text, theme, is_dark):
        lbl_col = theme["label_col"]
        border = theme["border_col"]

        c.setFont(FONT_B, 8)
        c.setFillColor(hc(theme["title_col"]))
        c.drawString(x, y, title)
        c.setFont(FONT, 6.5)
        c.setFillColor(hc(lbl_col))
        c.drawString(x, y - 11, desc)
        y -= 20

        total_h = 120
        c.setFillColor(hc(bg_hex))
        c.setStrokeColor(hc(border))
        c.setLineWidth(0.5)
        c.roundRect(x, y - total_h, w, total_h, 6, fill=1, stroke=1)

        c.setFont(FONT, 5.5)
        c.setFillColor(hc(lbl_col))
        c.drawString(x + 6, y - 12, "background.page")

        btn_w = w - 40
        btn_h = 36
        btn_x = x + 20
        btn_y = y - 40

        c.setFillColor(hc(btn_hex))
        c.roundRect(btn_x, btn_y - btn_h, btn_w, btn_h, 10, fill=1, stroke=0)

        c.setFont(FONT_B, 12)
        c.setFillColor(hc(text_hex))
        tw = c.stringWidth("Submit", FONT_B, 12)
        c.drawString(btn_x + (btn_w - tw) / 2, btn_y - btn_h / 2 - 4, "Submit")

        c.setFont(FONT, 5.5)
        c.setFillColor(hc(lbl_col))
        c.drawString(btn_x, btn_y - btn_h - 10, f"action: {action_label}")
        c.drawString(btn_x, btn_y - btn_h - 19, f"text: {label_text}")

        return y - total_h - 8

    for mode_name, theme, is_dark in [("Light Mode", lt, False), ("Dark Mode", dk, True)]:
        c.setFont(FONT_B, 10)
        c.setFillColor(hc(theme["accent"]))
        c.drawString(ML, y, mode_name)
        c.setStrokeColor(hc(theme["accent"]))
        c.setLineWidth(1)
        c.line(ML, y - 3, ML + 60, y - 3)
        y -= 16

        lx = ML
        rx = ML + half_w + 16

        bg_page = get_tok(theme, "BACKGROUND", "page")
        surf_default = get_tok(theme, "SURFACE", "default")
        cont_primary = get_tok(theme, "CONTENT", "primary")
        surf_success = get_tok(theme, "SURFACE", "success")
        cont_success = get_tok(theme, "CONTENT STATUS", "success")
        act_primary = get_tok(theme, "ACTION", "primary·default")
        cont_on = get_tok(theme, "CONTENT", "onPrimary")

        y1 = draw_scenario(c, lx, y, half_w,
                           "Standard Content",
                           "background → surface → content.primary",
                           [("background.page", bg_page),
                            ("surface.default", surf_default),
                            ("content.primary", cont_primary)],
                           theme, is_dark)

        y2 = draw_scenario(c, rx, y, half_w,
                           "Status Surface",
                           "background → surface.success → content.status",
                           [("background.page", bg_page),
                            ("surface.success", surf_success),
                            ("content.status.success", cont_success)],
                           theme, is_dark)

        y = min(y1, y2) - 4

        y3 = draw_action_scenario(c, lx, y, half_w,
                                  "Action Button",
                                  "action.primary → content.onPrimary",
                                  bg_page, act_primary, cont_on,
                                  "action.primary.default", "content.onPrimary",
                                  theme, is_dark)

        y4 = draw_action_scenario(c, rx, y, half_w,
                                  "Destructive Button",
                                  "action.destructive → content.onError",
                                  bg_page,
                                  get_tok(theme, "ACTION", "destruct·default"),
                                  get_tok(theme, "CONTENT", "onError"),
                                  "action.destructive.default", "content.onError",
                                  theme, is_dark)

        y = min(y3, y4) - 12


def draw_footer(c, page_num, total=8):
    c.setFont(FONT, 7)
    c.setFillColor(hc("#d1d5db"))
    c.drawCentredString(W/2, 9*mm, f"Design System Reference  ·  Page {page_num} of {total}")


# ─── Build PDF ────────────────────────────────────────────────────────────────

def build():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    cv = canvas.Canvas(OUTPUT, pagesize=A4)
    cv.setTitle("Design System Reference")
    cv.setSubject("Colors · Typography · Dimensions")

    pages = [
        (draw_cover,              "Cover"),
        (draw_brand_palette,      "Brand Palette"),
        (draw_semantic,           "Semantic Tokens"),
        (lambda c: draw_theme_page(c, "light"), "Theme Light"),
        (lambda c: draw_theme_page(c, "dark"),  "Theme Dark"),
        (draw_hierarchy,          "Color Hierarchy"),
        (draw_typography,         "Typography"),
        (draw_dimensions,         "Dimensions"),
    ]

    for i, (fn, name) in enumerate(pages, 1):
        fn(cv)
        if i > 1:  # no footer on cover
            draw_footer(cv, i)
        cv.showPage()

    cv.save()
    print(f"✓  Saved → {OUTPUT}")


if __name__ == "__main__":
    build()
