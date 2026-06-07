from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import KeepTogether
import reportlab.lib.colors as rlcolors

# ── Brand Colors ──────────────────────────────────────────────────────────────
SCG_BLACK      = rlcolors.HexColor("#0A0A0A")
SCG_DEEP_BLACK = rlcolors.HexColor("#050505")
SCG_GOLD       = rlcolors.HexColor("#C9A84C")
SCG_GOLD_LIGHT = rlcolors.HexColor("#E8D08A")
SCG_GOLD_DARK  = rlcolors.HexColor("#8B6914")
SCG_WHITE      = rlcolors.HexColor("#F5F5F0")
SCG_WARM_GRAY  = rlcolors.HexColor("#2A2A2A")
SCG_MID_GRAY   = rlcolors.HexColor("#4A4A4A")
SCG_LIGHT_GRAY = rlcolors.HexColor("#9A9A9A")
SCG_CREAM      = rlcolors.HexColor("#FAF6EE")
SCG_RULE       = rlcolors.HexColor("#C9A84C")

doc = SimpleDocTemplate(
    "smith_cap_group_brand_guide.pdf",
    pagesize=letter,
    leftMargin=0.75*inch,
    rightMargin=0.75*inch,
    topMargin=0.75*inch,
    bottomMargin=0.75*inch,
)

# ── Styles ────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def sty(name, parent="Normal", **kwargs):
    return ParagraphStyle(name, parent=styles[parent], **kwargs)

COVER_TITLE = sty("CoverTitle",
    fontSize=36, leading=42, textColor=SCG_GOLD,
    fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=6)

COVER_SUB = sty("CoverSub",
    fontSize=13, leading=18, textColor=SCG_LIGHT_GRAY,
    fontName="Helvetica", alignment=TA_CENTER, spaceAfter=4)

COVER_TAGLINE = sty("CoverTagline",
    fontSize=11, leading=16, textColor=SCG_GOLD_LIGHT,
    fontName="Helvetica-Oblique", alignment=TA_CENTER)

SECTION_TITLE = sty("SectionTitle",
    fontSize=22, leading=28, textColor=SCG_GOLD,
    fontName="Helvetica-Bold", spaceBefore=18, spaceAfter=6)

SUBSECTION = sty("Subsection",
    fontSize=13, leading=18, textColor=SCG_GOLD_LIGHT,
    fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=4)

BODY = sty("Body",
    fontSize=9.5, leading=14, textColor=SCG_WHITE,
    fontName="Helvetica", spaceAfter=6)

BODY_DARK = sty("BodyDark",
    fontSize=9.5, leading=14, textColor=SCG_DEEP_BLACK,
    fontName="Helvetica", spaceAfter=6)

CAPTION = sty("Caption",
    fontSize=8, leading=11, textColor=SCG_LIGHT_GRAY,
    fontName="Helvetica-Oblique", spaceAfter=4)

LABEL = sty("Label",
    fontSize=8.5, leading=12, textColor=SCG_GOLD,
    fontName="Helvetica-Bold", spaceAfter=2)

BIG_QUOTE = sty("BigQuote",
    fontSize=14, leading=20, textColor=SCG_GOLD_LIGHT,
    fontName="Helvetica-Oblique", alignment=TA_CENTER,
    spaceBefore=12, spaceAfter=12)

TABLE_HEADER = sty("TableHeader",
    fontSize=9, leading=12, textColor=SCG_BLACK,
    fontName="Helvetica-Bold", alignment=TA_CENTER)

TABLE_CELL = sty("TableCell",
    fontSize=9, leading=12, textColor=SCG_WHITE,
    fontName="Helvetica")

def gold_rule():
    return HRFlowable(width="100%", thickness=1, color=SCG_GOLD, spaceAfter=10, spaceBefore=4)

def thin_rule():
    return HRFlowable(width="100%", thickness=0.5, color=SCG_MID_GRAY, spaceAfter=8, spaceBefore=4)

def section_header(title):
    return [
        Spacer(1, 0.1*inch),
        Paragraph(title.upper(), SECTION_TITLE),
        gold_rule(),
    ]

def dark_table(data, col_widths, header_bg=SCG_GOLD, row_bg=SCG_WARM_GRAY, alt_bg=SCG_DEEP_BLACK):
    t = Table(data, colWidths=col_widths)
    style = TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), header_bg),
        ("TEXTCOLOR",     (0,0), (-1,0), SCG_BLACK),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0), 9),
        ("ALIGN",         (0,0), (-1,-1), "LEFT"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [row_bg, alt_bg]),
        ("TEXTCOLOR",     (0,1), (-1,-1), SCG_WHITE),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,1), (-1,-1), 9),
        ("GRID",          (0,0), (-1,-1), 0.4, SCG_MID_GRAY),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS",(0,0), (-1,0), [header_bg]),
    ])
    t.setStyle(style)
    return t

def color_swatch_table(swatches):
    """swatches = list of (label, hex, role, usage)"""
    data = [["", "COLOR NAME", "HEX CODE", "PANTONE", "ROLE", "USAGE"]]
    for label, hexval, pantone, role, usage in swatches:
        data.append([label, hexval[0], hexval[1], pantone, role, usage])
    
    t = Table(data, colWidths=[0.4*inch, 1.3*inch, 0.9*inch, 0.9*inch, 1.1*inch, 2.2*inch])
    ts = TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), SCG_GOLD),
        ("TEXTCOLOR",     (0,0), (-1,0), SCG_BLACK),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0), 8),
        ("ALIGN",         (0,0), (-1,-1), "LEFT"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("GRID",          (0,0), (-1,-1), 0.4, SCG_MID_GRAY),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ])
    for i, (label, hexval, pantone, role, usage) in enumerate(swatches, start=1):
        swatch_color = rlcolors.HexColor(hexval[1])
        ts.add("BACKGROUND", (0,i), (0,i), swatch_color)
        row_bg = SCG_WARM_GRAY if i % 2 == 1 else SCG_DEEP_BLACK
        ts.add("BACKGROUND", (1,i), (-1,i), row_bg)
        ts.add("TEXTCOLOR",  (1,i), (-1,i), SCG_WHITE)
        ts.add("FONTNAME",   (1,i), (-1,i), "Helvetica")
        ts.add("FONTSIZE",   (1,i), (-1,i), 8.5)
    t.setStyle(ts)
    return t

# ═══════════════════════════════════════════════════════════════════════════════
# BUILD DOCUMENT
# ═══════════════════════════════════════════════════════════════════════════════
story = []

# ── PAGE 1: COVER ─────────────────────────────────────────────────────────────
story.append(Spacer(1, 1.2*inch))
story.append(Paragraph("SMITH CAP GROUP", COVER_TITLE))
story.append(Spacer(1, 0.05*inch))
story.append(Paragraph("A HOLDING COMPANY", COVER_SUB))
story.append(Spacer(1, 0.2*inch))
story.append(gold_rule())
story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("B R A N D   I D E N T I T Y   G U I D E", sty("CI",
    fontSize=15, leading=20, textColor=SCG_WHITE, fontName="Helvetica",
    alignment=TA_CENTER, spaceAfter=6, letterSpacing=3)))
story.append(Spacer(1, 0.15*inch))
story.append(Paragraph('"Protect. Grow. Transfer."', BIG_QUOTE))
story.append(Spacer(1, 0.2*inch))
story.append(gold_rule())
story.append(Spacer(1, 0.3*inch))

cover_desc = (
    "This Brand Identity Guide governs the visual language, voice, and standards for "
    "Smith Cap Group and all subsidiary entities under the SCG portfolio. Every touchpoint — "
    "from investor decks to social media to business cards — must adhere to these guidelines "
    "to maintain the integrity, authority, and legacy positioning of the Smith Cap Group brand."
)
story.append(Paragraph(cover_desc, sty("CoverDesc",
    fontSize=10, leading=15, textColor=SCG_LIGHT_GRAY,
    fontName="Helvetica", alignment=TA_CENTER, spaceAfter=8)))
story.append(Spacer(1, 0.4*inch))

meta_data = [
    ["DOCUMENT",  "SCG Brand Identity Guide v1.0"],
    ["ISSUED",    "June 2026"],
    ["PREPARED BY", "S2T Designs × SmithCap FMO"],
    ["STATUS",    "Official — Confidential"],
]
meta_table = Table(meta_data, colWidths=[1.5*inch, 4.5*inch])
meta_table.setStyle(TableStyle([
    ("TEXTCOLOR",     (0,0), (0,-1), SCG_GOLD),
    ("TEXTCOLOR",     (1,0), (1,-1), SCG_LIGHT_GRAY),
    ("FONTNAME",      (0,0), (-1,-1), "Helvetica"),
    ("FONTSIZE",      (0,0), (-1,-1), 9),
    ("ALIGN",         (0,0), (0,-1), "RIGHT"),
    ("ALIGN",         (1,0), (1,-1), "LEFT"),
    ("TOPPADDING",    (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ("LINEABOVE",     (0,0), (-1,0), 0.5, SCG_MID_GRAY),
    ("LINEBELOW",     (0,-1), (-1,-1), 0.5, SCG_MID_GRAY),
]))
story.append(meta_table)
story.append(PageBreak())

# ── PAGE 2: TABLE OF CONTENTS ──────────────────────────────────────────────────
story += section_header("Table of Contents")
toc = [
    ("01", "Brand Foundation",          "Mission, Values, Brand Promise, Positioning"),
    ("02", "Logo System",               "Primary Mark, Variants, Clear Space, Sizing"),
    ("03", "Color Palette",             "Primary, Secondary, Neutral, Sub-brand Colors"),
    ("04", "Typography",                "Typefaces, Hierarchy, Usage Rules"),
    ("05", "Voice & Tone",              "Brand Voice, Taglines, Messaging Framework"),
    ("06", "Logo Applications",         "Business Cards, Letterhead, Decks, Signage"),
    ("07", "Sub-Brand Architecture",    "Portfolio Entities, SCG Lockup Rules"),
    ("08", "Digital Standards",         "Web, Social Media, Email Signatures"),
    ("09", "Prohibited Uses",           "Logo Misuse, Color Violations, Typography Don'ts"),
    ("10", "Trademark & Legal",         "Filing Strategy, Usage Rights, Enforcement"),
]
for num, title, desc in toc:
    row_data = [[
        Paragraph(f"<b>{num}</b>", sty("TN", fontSize=11, textColor=SCG_GOLD, fontName="Helvetica-Bold")),
        Paragraph(f"<b>{title}</b>", sty("TT", fontSize=10, textColor=SCG_WHITE, fontName="Helvetica-Bold")),
        Paragraph(desc, sty("TD", fontSize=9, textColor=SCG_LIGHT_GRAY, fontName="Helvetica")),
    ]]
    t = Table(row_data, colWidths=[0.4*inch, 1.8*inch, 4.6*inch])
    t.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LINEBELOW",     (0,0), (-1,0), 0.3, SCG_MID_GRAY),
    ]))
    story.append(t)
story.append(PageBreak())

# ── PAGE 3: BRAND FOUNDATION ──────────────────────────────────────────────────
story += section_header("01 — Brand Foundation")

story.append(Paragraph("MISSION STATEMENT", SUBSECTION))
story.append(Paragraph(
    "Smith Cap Group exists to build, protect, and transfer generational wealth across "
    "multiple asset classes and operating businesses — with discipline, integrity, and a "
    "long-term perspective that outlasts market cycles.",
    BODY))

story.append(Paragraph("BRAND PROMISE", SUBSECTION))
story.append(Paragraph(
    "<i>\"We invest with discipline, operate with integrity, and build lasting value across generations.\"</i>",
    sty("BP", fontSize=11, leading=16, textColor=SCG_GOLD_LIGHT,
        fontName="Helvetica-Oblique", spaceAfter=8)))

story.append(Paragraph("CORE VALUES", SUBSECTION))
values = [
    ["DISCIPLINE", "Every decision is governed by process, not emotion. We follow the thesis."],
    ["INTEGRITY",  "Transparent with partners, subsidiaries, and the communities we serve."],
    ["LEGACY",     "We build for the next generation — not the next quarter."],
    ["STEWARDSHIP","Capital entrusted to us is protected before it is grown."],
    ["EXCELLENCE", "Institutional-grade standards applied to every business we operate."],
]
story.append(dark_table(
    [["VALUE", "DEFINITION"]] + values,
    [1.5*inch, 5.3*inch]
))

story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("BRAND POSITIONING STATEMENT", SUBSECTION))
story.append(Paragraph(
    "Smith Cap Group is a diversified private holding company that operates at the intersection "
    "of entrepreneurship and institutional capital management. Unlike traditional investment firms, "
    "SCG builds and operates businesses directly — creating value through active ownership, not "
    "passive speculation. Our brand communicates authority, permanence, and the disciplined pursuit "
    "of generational wealth.",
    BODY))

story.append(Paragraph("TARGET AUDIENCES", SUBSECTION))
audiences = [
    ["PRIMARY",     "High-net-worth individuals, institutional partners, investment collaborators"],
    ["SECONDARY",   "Business owners, entrepreneurs, operators seeking capital or partnership"],
    ["COMMUNITY",   "Pflugerville/Austin/Hutto TX community, fraternal networks, church community"],
    ["INTERNAL",    "SCG operating company leaders, subsidiary management teams"],
]
story.append(dark_table(
    [["AUDIENCE", "DESCRIPTION"]] + audiences,
    [1.3*inch, 5.5*inch]
))
story.append(PageBreak())

# ── PAGE 4: LOGO SYSTEM ───────────────────────────────────────────────────────
story += section_header("02 — Logo System")

story.append(Paragraph("PRIMARY MARK — THE SMITH CREST", SUBSECTION))
story.append(Paragraph(
    "The Smith Crest is the official primary mark of Smith Cap Group. It consists of a heraldic "
    "shield bearing the SCG monogram, flanked by laurel branches and topped by a torch. The shield "
    "contains three symbolic elements: the lion (strength), the torch (vision), and the key "
    "(access to opportunity). This mark is used on all formal, legal, and institutional materials.",
    BODY))

logo_variants = [
    ["VARIANT",          "USAGE",                              "BACKGROUND"],
    ["Full Color",       "Primary — all standard applications", "Dark/Black only"],
    ["Gold on Black",    "Premium, formal, investor materials", "Black (#0A0A0A)"],
    ["Gold on White",    "Print, legal documents, letterhead",  "White/Cream"],
    ["Monochrome White", "Reversed on dark photography",        "Dark backgrounds"],
    ["Monochrome Black", "Single-color print, embossing",       "White/Cream"],
    ["SCG Monogram",     "App icons, favicons, social avatars", "Black or Gold"],
]
story.append(dark_table(logo_variants, [1.4*inch, 2.8*inch, 2.6*inch]))

story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("CLEAR SPACE RULE", SUBSECTION))
story.append(Paragraph(
    "The clear space around the Smith Crest mark must never be less than the height of the "
    "<b>'S'</b> in the SCG monogram on all sides. No other graphic element, text, or imagery "
    "may intrude on this protected zone.",
    BODY))

story.append(Paragraph("MINIMUM SIZE", SUBSECTION))
min_sizes = [
    ["APPLICATION",       "MINIMUM SIZE",    "FORMAT"],
    ["Print / Letterhead","0.75 inch wide",  "Vector (EPS/SVG)"],
    ["Digital / Web",     "60px wide",       "PNG (transparent)"],
    ["Social Avatar",     "400×400px",       "PNG"],
    ["App Icon",          "1024×1024px",     "PNG"],
    ["Embroidery",        "1.25 inch wide",  "DST/EMB file"],
    ["Embossing/Stamp",   "1.0 inch wide",   "Vector (EPS)"],
]
story.append(dark_table(min_sizes, [2.0*inch, 1.8*inch, 2.9*inch]))

story.append(Spacer(1, 0.15*inch))
story.append(Paragraph("SECONDARY MARKS", SUBSECTION))
secondary = [
    ["SCG Crown (#6)",         "Social media, merchandise, sponsorships, events"],
    ["SCG Eagle (#9)",         "Community outreach, youth programs, XFTC sponsorships"],
    ["Architecture Mark (#5)", "Investor decks only — shows holding company structure"],
    ["Legacy Vault (#10)",     "Wealth management marketing, estate planning materials"],
]
story.append(dark_table(
    [["MARK", "APPROVED USE ONLY"]] + secondary,
    [2.0*inch, 4.8*inch]
))
story.append(PageBreak())

# ── PAGE 5: COLOR PALETTE ──────────────────────────────────────────────────────
story += section_header("03 — Color Palette")

story.append(Paragraph(
    "The SCG color system is built on a foundation of Deep Black and Imperial Gold — "
    "the language of institutional authority and generational wealth. Every color in the "
    "palette has a defined role. Never substitute, approximate, or invent new brand colors.",
    BODY))

story.append(Paragraph("PRIMARY PALETTE", SUBSECTION))
primary_swatches = [
    (("SCG Deep Black",  "#0A0A0A"), "PMS Black 6 C",    "Dominant background",     "All primary backgrounds, primary mark"),
    (("Imperial Gold",   "#C9A84C"), "PMS 124 C",         "Hero accent, primary gold","Logo, headlines, borders, CTAs"),
    (("SCG White",       "#F5F5F0"), "PMS Cool Gray 1 C", "Primary text on dark",    "Body text, clean backgrounds"),
]
primary_data = [["", "COLOR NAME", "HEX", "PANTONE", "ROLE", "TYPICAL USE"]]
for (name, hexval), pantone, role, usage in primary_swatches:
    primary_data.append(["", name, hexval, pantone, role, usage])
pt = Table(primary_data, colWidths=[0.5*inch, 1.4*inch, 0.9*inch, 1.0*inch, 1.1*inch, 1.9*inch])
pstyle = TableStyle([
    ("BACKGROUND",    (0,0), (-1,0), SCG_GOLD),
    ("TEXTCOLOR",     (0,0), (-1,0), SCG_BLACK),
    ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE",      (0,0), (-1,-1), 9),
    ("GRID",          (0,0), (-1,-1), 0.4, SCG_MID_GRAY),
    ("TOPPADDING",    (0,0), (-1,-1), 7),
    ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ("RIGHTPADDING",  (0,0), (-1,-1), 6),
])
for i, (name, hexval), pantone, role, usage in [(i+1, *s) for i, s in enumerate(primary_swatches)]:
    pstyle.add("BACKGROUND", (0,i), (0,i), rlcolors.HexColor(hexval))
    row_bg = SCG_WARM_GRAY if i % 2 == 1 else SCG_DEEP_BLACK
    pstyle.add("BACKGROUND", (1,i), (-1,i), row_bg)
    pstyle.add("TEXTCOLOR",  (1,i), (-1,i), SCG_WHITE)
    pstyle.add("FONTNAME",   (1,i), (-1,i), "Helvetica")
pt.setStyle(pstyle)
story.append(pt)

story.append(Paragraph("SECONDARY PALETTE", SUBSECTION))
sec_swatches = [
    (("Gold Light",    "#E8D08A"), "PMS 134 C",       "Highlights, hover states",     "Gradient light, text on dark mid-tones"),
    (("Gold Dark",     "#8B6914"), "PMS 131 C",       "Shadows, depth on gold",       "Gradient dark, embossed effects"),
    (("Warm Gray",     "#2A2A2A"), "PMS Cool Gray 11","Secondary backgrounds",         "Cards, panels, table rows"),
    (("Mid Gray",      "#4A4A4A"), "PMS Cool Gray 9", "Borders, dividers",             "Rules, table borders, UI strokes"),
    (("SCG Cream",     "#FAF6EE"), "PMS Warm Gray 1", "Light mode background",         "Print documents, light-mode digital"),
]
sec_data = [["", "COLOR NAME", "HEX", "PANTONE", "ROLE", "TYPICAL USE"]]
for (name, hexval), pantone, role, usage in sec_swatches:
    sec_data.append(["", name, hexval, pantone, role, usage])
st = Table(sec_data, colWidths=[0.5*inch, 1.4*inch, 0.9*inch, 1.0*inch, 1.1*inch, 1.9*inch])
sstyle = TableStyle([
    ("BACKGROUND",    (0,0), (-1,0), SCG_GOLD),
    ("TEXTCOLOR",     (0,0), (-1,0), SCG_BLACK),
    ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE",      (0,0), (-1,-1), 9),
    ("GRID",          (0,0), (-1,-1), 0.4, SCG_MID_GRAY),
    ("TOPPADDING",    (0,0), (-1,-1), 7),
    ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ("RIGHTPADDING",  (0,0), (-1,-1), 6),
])
for i, (name, hexval), pantone, role, usage in [(i+1, *s) for i, s in enumerate(sec_swatches)]:
    sstyle.add("BACKGROUND", (0,i), (0,i), rlcolors.HexColor(hexval))
    row_bg = SCG_WARM_GRAY if i % 2 == 1 else SCG_DEEP_BLACK
    sstyle.add("BACKGROUND", (1,i), (-1,i), row_bg)
    sstyle.add("TEXTCOLOR",  (1,i), (-1,i), SCG_WHITE)
    sstyle.add("FONTNAME",   (1,i), (-1,i), "Helvetica")
st.setStyle(sstyle)
story.append(st)

story.append(Paragraph("APPROVED COLOR COMBINATIONS", SUBSECTION))
combos = [
    ["Gold on Deep Black",   "#C9A84C on #0A0A0A", "✅ PRIMARY — all formal materials"],
    ["White on Deep Black",  "#F5F5F0 on #0A0A0A", "✅ Body text, captions"],
    ["Gold on Warm Gray",    "#C9A84C on #2A2A2A", "✅ Cards, panels"],
    ["Black on Gold",        "#0A0A0A on #C9A84C", "✅ CTAs, buttons, callouts"],
    ["Black on Cream",       "#0A0A0A on #FAF6EE", "✅ Print, letterhead"],
    ["White on Gold",        "#F5F5F0 on #C9A84C", "⚠️ Large text only — low contrast at small sizes"],
    ["Gold on Gold Light",   "#C9A84C on #E8D08A", "❌ NEVER — insufficient contrast"],
    ["White on Cream",       "#F5F5F0 on #FAF6EE", "❌ NEVER — invisible"],
]
story.append(dark_table(
    [["COMBINATION", "HEX VALUES", "STATUS"]] + combos,
    [1.8*inch, 2.2*inch, 2.8*inch]
))
story.append(PageBreak())

# ── PAGE 6: TYPOGRAPHY ────────────────────────────────────────────────────────
story += section_header("04 — Typography")

story.append(Paragraph(
    "Typography is the second most recognizable element of the SCG brand after the logo. "
    "The type system uses three typefaces — each with a defined role. Never substitute "
    "system fonts on formal materials.",
    BODY))

story.append(Paragraph("PRIMARY TYPEFACE — CORMORANT GARAMOND", SUBSECTION))
story.append(Paragraph(
    "<b>Cormorant Garamond</b> (Bold / SemiBold / Regular / Italic) — "
    "A refined serif that communicates heritage, authority, and prestige. Used for all "
    "primary headlines, the SCG wordmark in documents, and institutional materials.",
    BODY))
story.append(Paragraph(
    "Google Fonts (free) · Adobe Fonts · fonts.google.com/specimen/Cormorant+Garamond",
    CAPTION))

type_hier_1 = [
    ["USE",                "WEIGHT",      "SIZE",       "TRACKING"],
    ["Document Title",     "Bold",        "36–48pt",    "Wide (+50)"],
    ["Section Header",     "SemiBold",    "22–28pt",    "Normal"],
    ["Sub-Header",         "SemiBold",    "14–18pt",    "Normal"],
    ["Pull Quote",         "Italic",      "14–18pt",    "Normal"],
    ["Tagline",            "Regular",     "11–13pt",    "Wide (+100)"],
]
story.append(dark_table(type_hier_1, [2.0*inch, 1.4*inch, 1.4*inch, 2.0*inch]))

story.append(Paragraph("SECONDARY TYPEFACE — MONTSERRAT", SUBSECTION))
story.append(Paragraph(
    "<b>Montserrat</b> (Bold / Medium / Regular / Light) — "
    "A modern geometric sans-serif for body copy, labels, UI elements, and digital applications. "
    "Pairs with Cormorant Garamond to balance classic and contemporary.",
    BODY))
story.append(Paragraph(
    "Google Fonts (free) · fonts.google.com/specimen/Montserrat",
    CAPTION))

type_hier_2 = [
    ["USE",                "WEIGHT",   "SIZE",      "TRACKING"],
    ["Body Copy",          "Regular",  "9–10pt",    "Normal"],
    ["Captions",           "Light",    "8pt",       "Normal"],
    ["Labels / Tags",      "Bold",     "8–9pt",     "Wide (+80)"],
    ["Navigation",         "Medium",   "10–12pt",   "Wide (+50)"],
    ["Data / Numbers",     "Medium",   "10–14pt",   "Normal"],
    ["Buttons / CTAs",     "Bold",     "10–12pt",   "Wide (+80)"],
]
story.append(dark_table(type_hier_2, [2.0*inch, 1.4*inch, 1.4*inch, 2.0*inch]))

story.append(Paragraph("ACCENT TYPEFACE — CINZEL DECORATIVE", SUBSECTION))
story.append(Paragraph(
    "<b>Cinzel Decorative</b> (Regular / Bold) — "
    "Used SPARINGLY for high-impact formal moments only: cover pages, event materials, "
    "award certificates, formal invitations, and the SCG brand mark text when rendered in "
    "documents. Never use for body copy.",
    BODY))
story.append(Paragraph(
    "Google Fonts (free) · fonts.google.com/specimen/Cinzel+Decorative",
    CAPTION))

story.append(Paragraph("FALLBACK FONTS (Digital / System)", SUBSECTION))
fallback = [
    ["ROLE",          "PRIMARY",              "FALLBACK 1",    "FALLBACK 2"],
    ["Headlines",     "Cormorant Garamond",   "Georgia",       "Times New Roman"],
    ["Body",          "Montserrat",           "Helvetica Neue","Arial"],
    ["Accent",        "Cinzel Decorative",    "Trajan Pro",    "Georgia Bold"],
    ["Monospace",     "Courier Prime",        "Courier New",   "Courier"],
]
story.append(dark_table(fallback, [1.5*inch, 1.9*inch, 1.7*inch, 1.7*inch]))
story.append(PageBreak())

# ── PAGE 7: VOICE & TONE ──────────────────────────────────────────────────────
story += section_header("05 — Voice & Tone")

story.append(Paragraph("BRAND VOICE PILLARS", SUBSECTION))
voice_pillars = [
    ["AUTHORITATIVE", "We speak with conviction. We don't hedge or qualify. We know capital."],
    ["PERMANENT",     "We use language that implies longevity. Not 'growth hacks' — generational wealth."],
    ["PRECISE",       "Every word earns its place. No filler. No marketing fluff. Clean sentences."],
    ["ACCESSIBLE",    "Institutional without being cold. We are serious but not sterile."],
    ["PRINCIPLED",    "We reference integrity, discipline, and stewardship — not hype or trends."],
]
story.append(dark_table([["PILLAR", "DEFINITION"]] + voice_pillars, [1.5*inch, 5.3*inch]))

story.append(Paragraph("OFFICIAL TAGLINES", SUBSECTION))
taglines = [
    ["PRIMARY",    "Protect. Grow. Transfer.",           "All primary brand materials, hero messaging"],
    ["SECONDARY",  "Build. Invest. Preserve.",           "Investment-facing materials, decks"],
    ["TERTIARY",   "Unlocking Generational Value.",      "Narrative context, longer-form marketing"],
    ["COMMUNITY",  "Vision. Strength. Stewardship.",     "Community events, sponsorships, youth programs"],
    ["FORMAL",     "We invest with discipline, operate\nwith integrity, and build lasting\nvalue across generations.", "Legal documents, official statements, website footer"],
]
story.append(dark_table([["TIER", "TAGLINE", "USE CONTEXT"]] + taglines, [1.0*inch, 2.5*inch, 3.3*inch]))

story.append(Paragraph("VOICE IN PRACTICE", SUBSECTION))
voice_ex = [
    ["❌ DO NOT SAY",                              "✅ SAY INSTEAD"],
    ["We help you grow your money",               "We build strategies to compound capital across generations"],
    ["Exciting investment opportunities",         "Disciplined capital deployment in proven asset classes"],
    ["Check out our latest deals",               "Current portfolio activity available to accredited partners"],
    ["We're crushing it this quarter",           "Q2 performance reflects the strength of our thesis"],
    ["DM us to get started!",                    "Contact us to discuss a potential partnership"],
    ["Smith Cap is killing the game",            "Smith Cap Group continues to execute on its founding mandate"],
]
story.append(dark_table(voice_ex, [3.2*inch, 3.6*inch]))

story.append(Paragraph("CHANNEL TONE CALIBRATION", SUBSECTION))
channels = [
    ["Investor Decks",     "Formal, precise, data-driven. No adjectives without data to back them."],
    ["Website",            "Authoritative and clear. Brief paragraphs. Strong headlines."],
    ["LinkedIn",           "Professional thought leadership. Insights, not promotions."],
    ["Instagram",          "Aspirational and visual. Minimal text. Brand imagery-led."],
    ["Email to Partners",  "Direct, respectful, zero fluff. Lead with the point."],
    ["Community Events",   "Warm, proud, accessible. Lead with impact on community."],
    ["Press / Media",      "Formal, factual. Quote-ready language."],
]
story.append(dark_table([["CHANNEL", "TONE DIRECTIVE"]] + channels, [1.7*inch, 5.1*inch]))
story.append(PageBreak())

# ── PAGE 8: LOGO APPLICATIONS ─────────────────────────────────────────────────
story += section_header("06 — Logo Applications")

story.append(Paragraph("BUSINESS CARDS", SUBSECTION))
bc_specs = [
    ["SIZE",          "3.5\" × 2.0\" (Standard US) — also offer 3.5\" × 2.0\" soft-touch matte"],
    ["FRONT",         "Smith Crest logo (gold) | Name in Cormorant Garamond Bold | Title in Montserrat Light"],
    ["BACK",          "SCG wordmark centered | Tagline: 'Protect. Grow. Transfer.' | Website URL"],
    ["BACKGROUND",    "Deep Black (#0A0A0A) — both sides"],
    ["FINISH",        "Soft-touch matte lamination + gold foil on crest and name"],
    ["PAPER STOCK",   "16pt card stock minimum — 32pt preferred for premium feel"],
    ["PRINTER",       "MOO.com, Canva Print Premium, or local offset printer"],
]
story.append(dark_table(bc_specs, [1.4*inch, 5.4*inch]))

story.append(Paragraph("LETTERHEAD", SUBSECTION))
lh_specs = [
    ["PAPER",         "8.5\" × 11\" — 24lb bond, cream or white"],
    ["HEADER",        "Smith Crest (0.75\" tall) left-aligned | 'SMITH CAP GROUP' right-aligned in Cinzel Decorative"],
    ["FOOTER",        "Website | Email | Address | Gold rule across full width"],
    ["BODY FONT",     "Montserrat Regular 10pt, black on white"],
    ["MARGINS",       "1\" all sides — text block starts below gold rule at 1.5\""],
    ["DIGITAL COPY",  "Use SCG Cream (#FAF6EE) background for email/digital letterhead"],
]
story.append(dark_table(lh_specs, [1.4*inch, 5.4*inch]))

story.append(Paragraph("INVESTOR DECKS (PowerPoint / PDF)", SUBSECTION))
deck_specs = [
    ["SLIDE SIZE",    "16:9 (1920×1080px) — widescreen standard"],
    ["COVER SLIDE",   "Full black background | Smith Crest centered | Title in Cormorant Garamond"],
    ["SECTION SLIDES","Dark background | Gold rule below section title | Architecture Mark (#5) for structure slides"],
    ["BODY SLIDES",   "Warm Gray (#2A2A2A) bg | White body text | Gold for data points and headers"],
    ["CHARTS/DATA",   "Gold primary data color | Light Gray secondary | White labels"],
    ["FOOTER",        "SCG monogram + confidentiality notice on every slide"],
    ["FONT PAIRING",  "Cormorant Garamond (titles) + Montserrat (body/data)"],
]
story.append(dark_table(deck_specs, [1.4*inch, 5.4*inch]))

story.append(Paragraph("EMAIL SIGNATURE", SUBSECTION))
story.append(Paragraph(
    "Structure: Full Name | Title | Smith Cap Group | Phone | Email | smithcapgroup.com",
    BODY))
story.append(Paragraph(
    "Logo: SCG monogram (100px wide) — gold on black — left-aligned. "
    "Tagline: <i>Protect. Grow. Transfer.</i> in Montserrat Light 8pt gold below URL. "
    "Do not include social icons in formal investor signatures.",
    BODY))
story.append(PageBreak())

# ── PAGE 9: SUB-BRAND ARCHITECTURE ───────────────────────────────────────────
story += section_header("07 — Sub-Brand Architecture")

story.append(Paragraph(
    "Smith Cap Group is the parent holding entity. All operating companies exist under the "
    "SCG umbrella. Sub-brands maintain their own identity but must adhere to the SCG "
    "endorsement lockup standard when appearing in formal portfolio contexts.",
    BODY))

story.append(Paragraph("SCG PORTFOLIO — ENTITY REGISTRY", SUBSECTION))
entities = [
    ["ENTITY",                    "TYPE",           "SCG MARK USE",       "COLOR VARIANT"],
    ["S2T Designs",               "For-Profit LLC", "Endorsed lockup",    "SCG Black + Brand Blue"],
    ["Clarity Solar Services",    "For-Profit LLC", "Endorsed lockup",    "SCG Black + Sky Blue"],
    ["The Elevation ATX",         "For-Profit LLC", "Endorsed lockup",    "SCG Black + Deep Purple"],
    ["Nutrue Apparel",            "For-Profit LLC", "Endorsed lockup",    "SCG Black + Earth Green"],
    ["YEPC",                      "For-Profit LLC", "Endorsed lockup",    "SCG Black + Forest Green"],
    ["Xtreme Force Track Club",   "501(c)(3)",      "Separate identity",  "XFTC Black + Royal Blue"],
    ["Elevate Scholars Foundation","501(c)(3)",     "Separate identity",  "PBS Royal Blue + White"],
    ["SmithCap FMO",              "Financial",      "Full SCG identity",  "Full SCG primary palette"],
    ["Legacy Alpha Capital AI",   "Investment",     "Full SCG identity",  "Full SCG primary palette"],
]
story.append(dark_table(entities, [1.9*inch, 1.1*inch, 1.4*inch, 2.4*inch]))

story.append(Paragraph("ENDORSED LOCKUP RULE", SUBSECTION))
story.append(Paragraph(
    "When a subsidiary appears in an SCG portfolio context (investor decks, annual reports, "
    "press releases), use the endorsed lockup format:",
    BODY))

lockup_rule = [
    ["FORMAT",       "[Subsidiary Logo]  |  [gold divider rule]  |  A Smith Cap Group Company"],
    ["TYPOGRAPHY",   "'A Smith Cap Group Company' — Montserrat Light 8pt — SCG Gold"],
    ["PLACEMENT",    "Below or to the right of the subsidiary logo"],
    ["SPACING",      "Minimum 16px / 0.2\" clear space between subsidiary logo and SCG endorsement"],
]
story.append(dark_table(lockup_rule, [1.3*inch, 5.5*inch]))

story.append(Paragraph("NONPROFIT ENTITIES — SPECIAL RULE", SUBSECTION))
story.append(Paragraph(
    "XFTC and Elevate Scholars Foundation are 501(c)(3) nonprofits with independent brand identities. "
    "They DO NOT carry the SCG endorsed lockup in external/public communications to avoid any "
    "perception that SCG receives financial benefit from nonprofit activities. "
    "SCG association is disclosed in formal governance and grant documents only.",
    BODY))
story.append(PageBreak())

# ── PAGE 10: DIGITAL STANDARDS ───────────────────────────────────────────────
story += section_header("08 — Digital Standards")

story.append(Paragraph("WEBSITE STANDARDS", SUBSECTION))
web = [
    ["Domain",           "smithcapgroup.com (register immediately — verify availability)"],
    ["Color Mode",       "Dark mode primary — Deep Black bg, Gold accents, White text"],
    ["Light Mode",       "SCG Cream bg, Black text, Gold accents — for document/print pages"],
    ["Hero Section",     "Full-width dark bg | Smith Crest animated entrance | Primary tagline"],
    ["Navigation",       "Montserrat Medium | All caps | Gold active state | Black bg nav bar"],
    ["CTA Buttons",      "Gold bg (#C9A84C) + Black text | Hover: Gold Dark (#8B6914)"],
    ["Body Text",        "Montserrat Regular 16px / 24px leading | #F5F5F0"],
    ["Section Headers",  "Cormorant Garamond Bold 32–40px | SCG Gold"],
]
story.append(dark_table(web, [1.4*inch, 5.4*inch]))

story.append(Paragraph("SOCIAL MEDIA STANDARDS", SUBSECTION))
social = [
    ["PLATFORM",     "LOGO VERSION",         "PROFILE BG",       "CONTENT TONE"],
    ["LinkedIn",     "Smith Crest full",     "Deep Black",       "Formal, thought leadership"],
    ["Instagram",    "SCG Eagle or Crown",   "Deep Black",       "Aspirational, visual-first"],
    ["Facebook",     "Smith Crest full",     "Deep Black",       "Community, announcements"],
    ["X/Twitter",    "SCG monogram",         "Deep Black",       "Market insights, commentary"],
    ["YouTube",      "Smith Crest full",     "SCG Gold banner",  "Educational, portfolio stories"],
]
story.append(dark_table(social, [1.1*inch, 1.5*inch, 1.3*inch, 2.9*inch]))

story.append(Paragraph("SOCIAL MEDIA IMAGE SIZES", SUBSECTION))
sizes = [
    ["Profile Photo",  "LinkedIn",  "400×400px",   "Smith Crest on black — gold version"],
    ["Cover Photo",    "LinkedIn",  "1584×396px",  "SCG Architecture Mark + tagline + dark bg"],
    ["Profile Photo",  "Instagram", "320×320px",   "SCG Eagle or Crown on black"],
    ["Feed Post",      "Instagram", "1080×1080px", "Gold rule, dark bg, brand imagery"],
    ["Story",          "Instagram", "1080×1920px", "Smith Crest centered, tagline below"],
    ["Profile Photo",  "Facebook",  "170×170px",   "Smith Crest on black"],
    ["Cover Photo",    "Facebook",  "851×315px",   "SCG + tagline + portfolio preview"],
    ["Profile Photo",  "X/Twitter", "400×400px",   "SCG monogram on black"],
    ["Banner",         "X/Twitter", "1500×500px",  "Architecture Mark or Crest + tagline"],
]
story.append(dark_table(
    [["ASSET", "PLATFORM", "DIMENSIONS", "CONTENT SPEC"]] + sizes,
    [1.2*inch, 1.1*inch, 1.2*inch, 3.3*inch]
))
story.append(PageBreak())

# ── PAGE 11: PROHIBITED USES ──────────────────────────────────────────────────
story += section_header("09 — Prohibited Uses")

story.append(Paragraph(
    "The following actions are strictly prohibited and constitute a brand standards violation. "
    "All SCG entities, partners, and vendors must adhere to these rules without exception.",
    BODY))

prohibit = [
    ["🚫 PROHIBITED ACTION",                                      "WHY IT'S PROHIBITED"],
    ["Stretching or distorting the logo in any direction",        "Destroys proportional integrity of the mark"],
    ["Using any color not in the approved SCG palette",           "Dilutes brand recognition and authority"],
    ["Placing the logo on a busy/photographic background",        "Reduces legibility and prestige"],
    ["Using unapproved fonts in branded materials",               "Creates brand inconsistency"],
    ["Recreating the logo in a different software/style",         "Only official files from S2T Designs are approved"],
    ["Using Gold on Gold Light — any light-on-light combo",       "Fails accessibility contrast standards"],
    ["Adding drop shadows, glows, or gradients to the logo",      "Cheapens the premium aesthetic"],
    ["Using the logo at sizes below minimum specification",        "Illegible and unprofessional"],
    ["Placing the logo in any color other than approved variants", "Violates primary color system"],
    ["Using a screenshot or low-res version of the logo",         "Always use vector (EPS/SVG/PDF) source files"],
    ["Using 'Smith Capital Group' as the brand name",             "Official name is Smith Cap Group — no exceptions"],
    ["Combining SCG mark with another brand mark at equal size",  "SCG must always be the dominant mark in SCG contexts"],
    ["Using nonprofit entity logos to represent SCG commercially","XFTC and ESF are independent — do not conflate"],
]
story.append(dark_table(prohibit, [3.5*inch, 3.3*inch]))
story.append(PageBreak())

# ── PAGE 12: TRADEMARK & LEGAL ────────────────────────────────────────────────
story += section_header("10 — Trademark & Legal")

story.append(Paragraph("TRADEMARK FILING PLAN", SUBSECTION))
tm_filings = [
    ["PRIORITY", "MARK",                     "CLASS",                    "EST. COST", "TIMELINE"],
    ["🔴 1st",   "SCG + Crest Design Mark",  "Class 36 — Financial Svcs","$350",      "File within 30 days"],
    ["🔴 2nd",   "SCG + Crest Design Mark",  "Class 35 — Business Mgmt", "$350",      "Same day as #1"],
    ["🟡 3rd",   "'Smith Cap Group' Wordmark","Class 36 — Financial Svcs","$350",      "File within 90 days"],
    ["🟢 4th",   "SCG Monogram Only",         "Class 36 + 35 (combined)", "$700",      "File within 120 days"],
]
story.append(dark_table(tm_filings, [0.6*inch, 1.9*inch, 1.9*inch, 0.8*inch, 1.6*inch]))

story.append(Paragraph(
    "Total estimated USPTO filing cost: <b>$1,050 – $1,400</b>. "
    "Engage a trademark attorney for Class 36 financial services filings — USPTO examining "
    "attorneys scrutinize financial services marks heavily. Recommended attorney budget: $500–$1,000 "
    "additional for professional prosecution.",
    BODY))

story.append(Paragraph("NAME AVAILABILITY", SUBSECTION))
tm_analysis = [
    ["'Smith Cap Group'",    "✅ AVAILABLE", "No identical marks found in Class 36. 'Cap' ≠ 'Capital' legally."],
    ["'Capital Group'",      "❌ BLOCKED",   "Registered by The Capital Group Companies, Inc. — do not use."],
    ["'SCG' as initials",    "✅ AVAILABLE", "No conflicting SCG marks found in financial services classes."],
    ["SCG + Crest design",   "✅ AVAILABLE", "Original design — no conflicts identified. File immediately."],
    ["'Smith' surname alone","⚠️ WEAK",      "Surnames get limited trademark protection — use composite mark."],
]
story.append(dark_table(
    [["MARK", "STATUS", "NOTES"]] + tm_analysis,
    [1.5*inch, 1.1*inch, 4.2*inch]
))

story.append(Paragraph("USAGE NOTICES", SUBSECTION))
notices = [
    ["™ Symbol",   "Use immediately on all materials — establishes common law rights before USPTO registration"],
    ["® Symbol",   "Use ONLY after USPTO registration is confirmed — using ® before registration is a federal violation"],
    ["Copyright",  "All brand materials: © 2026 Smith Cap Group. All Rights Reserved."],
    ["Vendor Use", "All vendors and partners must sign a brand license agreement before using any SCG mark"],
]
story.append(dark_table([["NOTICE", "RULE"]] + notices, [1.2*inch, 5.6*inch]))

story.append(Spacer(1, 0.2*inch))
story.append(gold_rule())
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph(
    "SMITH CAP GROUP — BRAND IDENTITY GUIDE v1.0 · JUNE 2026 · CONFIDENTIAL",
    sty("Footer", fontSize=8, textColor=SCG_MID_GRAY, fontName="Helvetica",
        alignment=TA_CENTER, spaceAfter=4)))
story.append(Paragraph(
    "Prepared by S2T Designs × SmithCap FMO · smithcapgroup.com",
    sty("Footer2", fontSize=8, textColor=SCG_GOLD_DARK, fontName="Helvetica",
        alignment=TA_CENTER)))

# ── BUILD ─────────────────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    # gold bottom bar
    canvas.setFillColor(SCG_WARM_GRAY)
    canvas.rect(0, 0, letter[0], 0.35*inch, fill=1, stroke=0)
    canvas.setFillColor(SCG_GOLD)
    canvas.rect(0, 0.35*inch, letter[0], 2, fill=1, stroke=0)
    # page number
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(SCG_LIGHT_GRAY)
    canvas.drawCentredString(letter[0]/2, 0.14*inch, f"Smith Cap Group Brand Guide  ·  Page {doc.page}")
    canvas.restoreState()

doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print("✅ Brand Guide PDF generated: smith_cap_group_brand_guide.pdf")
