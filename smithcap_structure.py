from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

NAVY   = colors.HexColor('#002D72')
ROYAL  = colors.HexColor('#003087')
GREEN  = colors.HexColor('#1B5E20')
LGREEN = colors.HexColor('#E8F5E9')
DGREEN = colors.HexColor('#2E7D32')
GOLD   = colors.HexColor('#B8960C')
LGOLD  = colors.HexColor('#FFF8E1')
WHITE  = colors.white
GRAY   = colors.HexColor('#555555')
LGRAY  = colors.HexColor('#F5F5F5')
DGRAY  = colors.HexColor('#333333')
RED    = colors.HexColor('#B71C1C')
AMBER  = colors.HexColor('#E65100')
TEAL   = colors.HexColor('#00695C')
LTEAL  = colors.HexColor('#E0F2F1')
INDIGO = colors.HexColor('#1A237E')
LINDIGO= colors.HexColor('#E8EAF6')
PURP   = colors.HexColor('#4A148C')
LPURP  = colors.HexColor('#F3E5F5')

doc = SimpleDocTemplate(
    "/app/SmithCapGroup_Entity_Structure.pdf",
    pagesize=letter,
    topMargin=0.45*inch, bottomMargin=0.5*inch,
    leftMargin=0.6*inch, rightMargin=0.6*inch
)
styles = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name, parent=styles['Normal'], **kw)

SMALL = S('SMALL', fontSize=7.5, textColor=GRAY, leading=11)
NOTE  = S('NOTE',  fontSize=7.5, textColor=GRAY, fontName='Helvetica-Oblique', leading=11)

story = []

# ── HEADER ──────────────────────────────────────────────────────────
hdr = Table([[
    Paragraph("SMITH CAPITAL GROUP LLC", S('h1', fontSize=18, textColor=WHITE, fontName='Helvetica-Bold')),
    Paragraph("Entity Structure &amp; Ownership Map", S('h2', fontSize=10, textColor=colors.HexColor('#A8C4E0'), alignment=TA_RIGHT))
]], colWidths=[4.2*inch, 3.6*inch])
hdr.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,-1),NAVY),
    ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ('LEFTPADDING',(0,0),(0,0),16),('RIGHTPADDING',(-1,0),(-1,0),16),
    ('TOPPADDING',(0,0),(-1,-1),13),('BOTTOMPADDING',(0,0),(-1,-1),13),
]))
story.append(hdr)
story.append(Spacer(1,4))

sub = Table([[
    Paragraph("Prepared for: <b>David Smith</b>  |  Smith Capital Group LLC  |  Pflugerville, TX", S('sh', fontSize=8.5, textColor=GRAY)),
    Paragraph("<b>June 6, 2026</b>  |  CONFIDENTIAL", S('sh2', fontSize=8.5, textColor=GRAY, alignment=TA_RIGHT))
]], colWidths=[4.5*inch, 3.3*inch])
sub.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,-1),LGRAY),
    ('LEFTPADDING',(0,0),(0,0),12),('RIGHTPADDING',(-1,0),(-1,0),12),
    ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
]))
story.append(sub)
story.append(Spacer(1,12))

# ── PARENT BOX ──────────────────────────────────────────────────────
story.append(Paragraph("PARENT ENTITY", S('lbl', fontSize=7.5, textColor=GRAY, fontName='Helvetica-Bold', letterSpacing=1.5)))
story.append(Spacer(1,3))

parent = Table([[Table([[
    Paragraph("SMITH CAPITAL GROUP LLC", S('pe', fontSize=15, textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_CENTER)),
    Paragraph("Parent Holding Company  ·  Texas LLC  ·  Tax Classification: Pass-Through (Disregarded)", S('ps', fontSize=8.5, textColor=colors.HexColor('#A8C4E0'), alignment=TA_CENTER, leading=12)),
    Spacer(1,4),
    Paragraph("smithcapgroup.com  ·  CEO: David Smith", S('pu', fontSize=8, textColor=colors.HexColor('#7FA8D4'), alignment=TA_CENTER)),
]], colWidths=[7.6*inch])]], colWidths=[7.6*inch])
parent.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,-1),NAVY),
    ('LEFTPADDING',(0,0),(-1,-1),16),('RIGHTPADDING',(0,0),(-1,-1),16),
    ('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12),
    ('BOX',(0,0),(-1,-1),3,GOLD),
]))
story.append(parent)
story.append(Spacer(1,5))

arrow = Table([[Paragraph("▼  Owns membership interests in all operating entities below  ▼",
    S('ar', fontSize=8, textColor=GRAY, alignment=TA_CENTER))]], colWidths=[7.6*inch])
arrow.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1)]))
story.append(arrow)
story.append(Spacer(1,8))

# ── ENTITY CARD ──────────────────────────────────────────────────────
def entity_card(name, entity_type, tax, domain, status, status_color, notes, bg, border):
    status_bg = LGREEN if status_color=='green' else \
                colors.HexColor('#FFEBEE') if status_color=='red' else \
                colors.HexColor('#FFF8E1') if status_color=='amber' else LINDIGO
    status_fc = DGREEN if status_color=='green' else \
                RED if status_color=='red' else \
                AMBER if status_color=='amber' else INDIGO

    header = Table([[
        Paragraph(f"<b>{name}</b>", S('cn', fontSize=10, textColor=NAVY, fontName='Helvetica-Bold', leading=13)),
        Paragraph(status, S('cs', fontSize=7.5, textColor=status_fc, fontName='Helvetica-Bold', alignment=TA_RIGHT))
    ]], colWidths=[4.8*inch, 2.0*inch])
    header.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),bg),
        ('BACKGROUND',(1,0),(1,0),status_bg),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),4),
    ]))

    details = Table([[
        Paragraph(f"<b>Type:</b> {entity_type}", SMALL),
        Paragraph(f"<b>Tax:</b> {tax}", SMALL),
        Paragraph(f"<b>Domain:</b> {domain}", SMALL),
    ]], colWidths=[2.53*inch, 2.53*inch, 2.54*inch])
    details.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#FAFAFA')),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LINEBELOW',(0,0),(-1,-1),0.5,colors.HexColor('#E0E0E0')),
    ]))

    notes_row = Table([[Paragraph(f"📋  {notes}", NOTE)]], colWidths=[7.6*inch])
    notes_row.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),WHITE),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))

    outer = Table([[header],[details],[notes_row]], colWidths=[7.6*inch])
    outer.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),1.5,border),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
    ]))
    return outer

# ── FOR-PROFIT ENTITIES ──────────────────────────────────────────────
story.append(Paragraph("FOR-PROFIT OPERATING ENTITIES", S('sec', fontSize=9, textColor=NAVY, fontName='Helvetica-Bold', spaceAfter=4)))

entities = [
    dict(name="SmithCap Ventures LLC", entity_type="Texas LLC",
         tax="Pass-Through / Deal-specific S-Corp per venture",
         domain="smithcapventures.com", status="🚀 NEW — Form Now", status_color='indigo',
         notes="Venture incubator arm. Tests and launches new business concepts before spinning out as standalone LLCs. "
               "First candidates: Rowdy Crown, EmbroidOS, new media properties.",
         bg=LINDIGO, border=INDIGO),
    dict(name="Youth Elite Performance Complex (YEPC)", entity_type="Texas LLC",
         tax="Pass-Through / S-Corp if management fees generated",
         domain="yepc.com", status="🏗️ IN DEVELOPMENT", status_color='indigo',
         notes="110-acre Hutto CR 132 mixed-use youth sports & performance development complex. "
               "Opportunity Zone 2.0 nomination strategy active. Census Tract 208.08 verification pending on TX ArcGIS. "
               "First steps: zoning verification + LoopNet price negotiation.",
         bg=LINDIGO, border=INDIGO),
    dict(name="S2T Designs LLC", entity_type="Texas LLC",
         tax="S-Corp Election (when net profit ≥ $40K)",
         domain="s2tdesigns.com", status="⚡ ACTIVE — Form Now", status_color='green',
         notes="Web & graphic design agency. Primary revenue-generating entity. Active clients: Kinorva, LEBC, PBS, XFTC. "
               "S-Corp election saves SE tax once profitable.",
         bg=LGREEN, border=DGREEN),
    dict(name="Clarity Solar Services LLC", entity_type="Texas LLC",
         tax="S-Corp Election (when net profit ≥ $40K)",
         domain="claritysolarservices.com", status="⚡ ACTIVE — Form Now", status_color='green',
         notes="Residential solar repair. Subcontract pipeline via Hert Renewables. "
               "TX SB 1036 GL insurance required by Sep 1, 2026. Brand: sky blue + white + slate gray.",
         bg=LGREEN, border=DGREEN),
    dict(name="Smith Capital Properties LLC", entity_type="Texas LLC",
         tax="Pass-Through (Disregarded)",
         domain="smithcapitalproperties.com", status="⚠️ INACTIVE — Reinstate", status_color='red',
         notes="Real estate holding entity. Currently INACTIVE with TX SOS. "
               "File past-due PIR + franchise tax reports + Form 811 to reinstate. Priority: within 30 days.",
         bg=colors.HexColor('#FFEBEE'), border=RED),
    dict(name="Nutrue Apparel LLC", entity_type="Texas LLC (or DBA)",
         tax="Pass-Through / Schedule C",
         domain="nutrueapparel.com", status="🔧 FORM — Low Priority", status_color='amber',
         notes="POD apparel brand via Printful/Shopify (hoodswag.shop). Inbro embroidery machine retrofit in progress. "
               "Form entity when revenue is consistent; DBA under SmithCap OK for now.",
         bg=LGOLD, border=GOLD),
    dict(name="The Elevation ATX LLC", entity_type="Texas LLC",
         tax="Pass-Through / S-Corp if events scale",
         domain="theelevationatx.com", status="🔧 FORM — Medium Priority", status_color='amber',
         notes="Upscale private hospitality event series. Form LLC before first paid event to limit personal liability.",
         bg=LGOLD, border=GOLD),
    dict(name="SmithCap FMO LLC", entity_type="Texas LLC",
         tax="Pass-Through",
         domain="smithcapfmo.com", status="🔧 FORM — As Needed", status_color='amber',
         notes="Financial management office overseeing capital deployment, bookkeeping, and investment policy across all SmithCap entities.",
         bg=LGOLD, border=GOLD),
]

for e in entities:
    story.append(entity_card(**e))
    story.append(Spacer(1,5))

# ── NONPROFIT AFFILIATES ─────────────────────────────────────────────
story.append(Spacer(1,4))
story.append(Paragraph("NONPROFIT / TAX-EXEMPT AFFILIATES  (Not owned by SmithCap Group — Affiliated Only)",
    S('sec2', fontSize=9, textColor=TEAL, fontName='Helvetica-Bold', spaceAfter=4)))

nbox = Table([[Paragraph(
    "These entities are 501(c)(3) nonprofits. David serves in a leadership/director role. "
    "Smith Capital Group does not hold ownership interest — they operate independently. "
    "SmithCap may provide paid management services via a formal Management Services Agreement (MSA).",
    NOTE)]], colWidths=[7.6*inch])
nbox.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,-1),LTEAL),('BOX',(0,0),(-1,-1),1,TEAL),
    ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
]))
story.append(nbox)
story.append(Spacer(1,4))

nonprofits = [
    dict(name="Elevate Scholars Foundation", entity_type="Texas Nonprofit / 501(c)(3) Pending",
         tax="Tax-Exempt (pending IRS determination)", domain="elevatescholarsfoundation.org",
         status="🔄 501(c)(3) PENDING", status_color='amber',
         notes="Formerly 'Phi Beta Sigma Collegiate Pathways Foundation.' Renamed for broader donor appeal. "
               "Mission: financial assistance for collegiate conference travel, scholarships, and leadership development. "
               "Phi Beta Sigma affiliated — Austin Sigmas Chapter. Form 1023-EZ if projected revenue ≤ $50K/yr.",
         bg=LTEAL, border=TEAL),
    dict(name="Xtreme Force Track Club (XFTC)", entity_type="Texas Nonprofit / 501(c)(3)",
         tax="Tax-Exempt — No income tax", domain="xtremeforcetrackclub.org",
         status="✅ ACTIVE 501(c)(3)", status_color='green',
         notes="Youth track nonprofit ages 6–18. David serves as Executive Director. "
               "Operates fully independently — SmithCap provides management support via MSA only. "
               "Membership plugin + leaderboard platform in development.",
         bg=LTEAL, border=TEAL),
]

for e in nonprofits:
    story.append(entity_card(**e))
    story.append(Spacer(1,5))

story.append(Spacer(1,8))

# ── FORMATION ROADMAP ────────────────────────────────────────────────
story.append(Paragraph("FORMATION PRIORITY ROADMAP", S('lbl3', fontSize=7.5, textColor=GRAY, fontName='Helvetica-Bold', letterSpacing=1.5)))
story.append(Spacer(1,4))

roadmap = [
    ["#", "Entity", "Action Required", "Timeline", "Est. Cost"],
    ["🔴 1", "Smith Capital Group LLC",       "File Articles of Organization — TX SOS",                  "Now",          "~$300"],
    ["🔴 2", "SmithCap Ventures LLC",          "File Articles of Organization — TX SOS",                  "Now",          "~$300"],
    ["🔴 3", "Smith Capital Properties LLC",   "Reinstate: past-due PIR + franchise tax + Form 811",      "30 days",      "~$200–500"],
    ["🟡 4", "Clarity Solar Services LLC",     "Form TX LLC + S-Corp election (IRS Form 2553)",           "60 days",      "~$300"],
    ["🟡 5", "S2T Designs LLC",                "Form TX LLC + S-Corp election when net profit ≥ $40K",    "60–90 days",   "~$300"],
    ["🟡 6", "YEPC LLC",                       "Form TX LLC — zoning + ArcGIS census tract verification first", "90 days","~$300"],
    ["🟢 7", "The Elevation ATX LLC",          "Form TX LLC before first paid event",                     "Before event", "~$300"],
    ["🟢 8", "Nutrue Apparel LLC",             "Form TX LLC or keep as DBA until revenue consistent",     "When ready",   "~$300"],
    ["🟢 9", "Elevate Scholars Foundation",    "File nonprofit corp + IRS Form 1023-EZ (if ≤ $50K/yr)",   "Q3 2026",      "~$350–500"],
    ["⚪ 10","SmithCap FMO LLC",               "Form when active capital deployment begins",               "Q4 2026",      "~$300"],
]

rt = Table(roadmap, colWidths=[0.6*inch, 2.35*inch, 2.75*inch, 1.0*inch, 0.7*inch], repeatRows=1)
rt.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),WHITE),
    ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
    ('FONTSIZE',(0,0),(-1,-1),7.5),
    ('ALIGN',(0,0),(-1,-1),'LEFT'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,LGRAY]),
    ('BACKGROUND',(0,1),(-1,1),colors.HexColor('#FFEBEE')),
    ('BACKGROUND',(0,2),(-1,2),LINDIGO),
    ('BACKGROUND',(0,3),(-1,3),colors.HexColor('#FFEBEE')),
    ('BACKGROUND',(0,4),(-1,5),colors.HexColor('#FFF8E1')),
    ('BACKGROUND',(0,6),(-1,6),LINDIGO),
    ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#CCCCCC')),
    ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
]))
story.append(rt)
story.append(Spacer(1,8))

# ── TAX NOTE ────────────────────────────────────────────────────────
tax_note = Table([[Paragraph(
    "<b>💡 Tax Strategy:</b>  Smith Capital Group LLC (parent) = pass-through, no payroll required. "
    "SmithCap Ventures = pass-through at incubator level; individual ventures elect S-Corp independently once profitable. "
    "Operating LLCs elect S-Corp once net profit clears ~$40K/year — pay reasonable salary, take rest as distributions, "
    "save 15.3% SE tax on distribution portion. "
    "Nonprofits (XFTC, Elevate Scholars Foundation) file separately and are never included in SmithCap Group's tax return.",
    S('tn', fontSize=8, textColor=DGRAY, leading=12))]], colWidths=[7.6*inch])
tax_note.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,-1),LGOLD),('BOX',(0,0),(-1,-1),1,GOLD),
    ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
    ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
]))
story.append(tax_note)
story.append(Spacer(1,8))

# ── FOOTER ──────────────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CCCCCC'), spaceAfter=4))
story.append(Paragraph(
    "Smith Capital Group LLC  ·  Pflugerville, TX  ·  Confidential — For Internal Use Only  ·  Updated June 6, 2026",
    S('ft', fontSize=7.5, textColor=GRAY, alignment=TA_CENTER)
))

doc.build(story)
print("Done")
