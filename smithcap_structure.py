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
MGRAY  = colors.HexColor('#EEEEEE')
DGRAY  = colors.HexColor('#333333')
RED    = colors.HexColor('#B71C1C')
AMBER  = colors.HexColor('#E65100')
LAMBER = colors.HexColor('#FFF3E0')
BLUE2  = colors.HexColor('#E3EBF7')
TEAL   = colors.HexColor('#00695C')
LTEAL  = colors.HexColor('#E0F2F1')
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

BODY  = S('BODY',  fontSize=8.5, textColor=DGRAY, leading=13)
SMALL = S('SMALL', fontSize=7.5, textColor=GRAY, leading=11)
NOTE  = S('NOTE',  fontSize=7.5, textColor=GRAY, fontName='Helvetica-Oblique', leading=11)
BOLD  = S('BOLD',  fontSize=8.5, textColor=NAVY, fontName='Helvetica-Bold', leading=13)

story = []

# ── HEADER ─────────────────────────────────────────────────────────
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
    Paragraph("<b>June 5, 2026</b>  |  CONFIDENTIAL", S('sh2', fontSize=8.5, textColor=GRAY, alignment=TA_RIGHT))
]], colWidths=[4.5*inch, 3.3*inch])
sub.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,-1),LGRAY),
    ('LEFTPADDING',(0,0),(0,0),12),('RIGHTPADDING',(-1,0),(-1,0),12),
    ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
]))
story.append(sub)
story.append(Spacer(1,12))

# ── HOLDING COMPANY BOX ────────────────────────────────────────────
story.append(Paragraph("PARENT ENTITY", S('lbl', fontSize=7.5, textColor=GRAY, fontName='Helvetica-Bold', letterSpacing=1.5)))
story.append(Spacer(1,3))

parent = Table([[
    Table([[
        Paragraph("SMITH CAPITAL GROUP LLC", S('pe', fontSize=15, textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph("Parent Holding Company  ·  Texas LLC  ·  Tax Classification: Disregarded / Pass-Through", S('ps', fontSize=8.5, textColor=colors.HexColor('#A8C4E0'), alignment=TA_CENTER, leading=12)),
        Spacer(1,4),
        Paragraph("smithcapgroup.com  ·  CEO: David Smith", S('pu', fontSize=8, textColor=colors.HexColor('#7FA8D4'), alignment=TA_CENTER)),
    ]], colWidths=[7.6*inch])
]], colWidths=[7.6*inch])
parent.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,-1),NAVY),
    ('LEFTPADDING',(0,0),(-1,-1),16),('RIGHTPADDING',(0,0),(-1,-1),16),
    ('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12),
    ('BOX',(0,0),(-1,-1),3,GOLD),
]))
story.append(parent)
story.append(Spacer(1,6))

# Arrow down
arrow = Table([[Paragraph("▼  Owns membership interests in all operating entities below  ▼",
    S('ar', fontSize=8, textColor=GRAY, alignment=TA_CENTER))]], colWidths=[7.6*inch])
arrow.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
story.append(arrow)
story.append(Spacer(1,8))

# ── OPERATING ENTITIES ─────────────────────────────────────────────
story.append(Paragraph("OPERATING ENTITIES", S('lbl2', fontSize=7.5, textColor=GRAY, fontName='Helvetica-Bold', letterSpacing=1.5)))
story.append(Spacer(1,5))

def entity_card(label, name, entity_type, tax, domain, status, status_color, notes, bg, border, fg=None):
    fg = fg or DGRAY
    status_bg = colors.HexColor('#E8F5E9') if status_color == 'green' else \
                colors.HexColor('#FFEBEE') if status_color == 'red' else \
                colors.HexColor('#FFF8E1')
    status_fc = DGREEN if status_color == 'green' else RED if status_color == 'red' else AMBER

    inner = [
        [Paragraph(f"<b>{name}</b>", S('cn', fontSize=10, textColor=NAVY, fontName='Helvetica-Bold', leading=13)),
         Paragraph(status, S('cs', fontSize=7.5, textColor=status_fc, fontName='Helvetica-Bold', alignment=TA_RIGHT))],
    ]
    header = Table(inner, colWidths=[4.8*inch, 2.0*inch])
    header.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), bg),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('BACKGROUND',(1,0),(1,0), status_bg),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]))

    detail_rows = [
        [Paragraph(f"<b>Type:</b> {entity_type}", SMALL),
         Paragraph(f"<b>Tax:</b> {tax}", SMALL),
         Paragraph(f"<b>Domain:</b> {domain}", SMALL)],
    ]
    details = Table(detail_rows, colWidths=[2.53*inch, 2.53*inch, 2.54*inch])
    details.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), colors.HexColor('#FAFAFA')),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LINEBELOW',(0,0),(-1,-1),0.5,colors.HexColor('#E0E0E0')),
    ]))

    notes_row = Table([[Paragraph(f"📋  {notes}", NOTE)]], colWidths=[7.6*inch])
    notes_row.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), WHITE),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))

    outer = Table([[header],[details],[notes_row]], colWidths=[7.6*inch])
    outer.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),1.5, border),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
    ]))
    return outer

entities = [
    dict(label="01", name="S2T Designs LLC", entity_type="Texas LLC", tax="S-Corp Election (when revenue ≥ $40K net)",
         domain="s2tdesigns.com", status="⚡ ACTIVE — Form Now", status_color='green',
         notes="Web & graphic design agency. Primary revenue-generating operating entity. S-Corp election saves SE tax once profitable.",
         bg=LGREEN, border=DGREEN),
    dict(label="02", name="Clarity Solar Services LLC", entity_type="Texas LLC", tax="S-Corp Election (when revenue ≥ $40K net)",
         domain="claritysolarservices.com", status="⚡ ACTIVE — Form Now", status_color='green',
         notes="Residential solar repair. Subcontract pipeline via Hert Renewables. TX SB 1036 GL insurance required by Sep 1, 2026.",
         bg=LGREEN, border=DGREEN),
    dict(label="03", name="Smith Capital Properties LLC", entity_type="Texas LLC", tax="Pass-Through (Disregarded)",
         domain="smithcapitalproperties.com", status="⚠️ INACTIVE — Reinstate", status_color='red',
         notes="Real estate holding entity. Currently inactive with TX SOS. File past-due PIR + franchise tax reports + Form 811 to reinstate.",
         bg=colors.HexColor('#FFEBEE'), border=RED),
    dict(label="04", name="Nutrue Apparel LLC", entity_type="Texas LLC (or DBA)", tax="Pass-Through / Schedule C",
         domain="nutrueapparel.com", status="🔧 FORM — Low Priority", status_color='amber',
         notes="POD apparel brand via Printful/Shopify (hoodswag.shop). Form entity when revenue is consistent. DBA under SmithCap OK for now.",
         bg=LGOLD, border=GOLD),
    dict(label="05", name="The Elevation ATX LLC", entity_type="Texas LLC", tax="Pass-Through / S-Corp if events scale",
         domain="theelevationatx.com", status="🔧 FORM — Medium Priority", status_color='amber',
         notes="Upscale private hospitality event series. Form once first paid event is confirmed to protect liability.",
         bg=LGOLD, border=GOLD),
    dict(label="06", name="SmithCap FMO LLC", entity_type="Texas LLC", tax="Pass-Through",
         domain="smithcapfmo.com", status="🔧 FORM — As Needed", status_color='amber',
         notes="Financial management office overseeing capital deployment, bookkeeping, and investment policy across all entities.",
         bg=LGOLD, border=GOLD),
]

nonprofits = [
    dict(label="N1", name="Xtreme Force Track Club (XFTC)", entity_type="Texas Nonprofit / 501(c)(3)",
         tax="Tax-Exempt — NO income tax", domain="xtremeforcetrackclub.org",
         status="✅ ACTIVE 501(c)(3)", status_color='green',
         notes="Youth track nonprofit ages 6–18. Operates independently — SmithCap Group does NOT own XFTC. David serves as Executive Director.",
         bg=LTEAL, border=TEAL),
    dict(label="N2", name="Psi Beta Sigma Foundation (PBS)", entity_type="Texas Nonprofit / 501(c)(3) Pending",
         tax="Tax-Exempt (pending IRS determination)", domain="psibetasigma1914.org",
         status="🔄 501(c)(3) PENDING", status_color='amber',
         notes="Collegiate pathways nonprofit. Fraternity-affiliated. SmithCap provides management support only — not an owner.",
         bg=LTEAL, border=TEAL),
]

story.append(Paragraph("For-Profit Operating Entities", S('sec', fontSize=9, textColor=NAVY, fontName='Helvetica-Bold', spaceAfter=4)))

for e in entities:
    story.append(entity_card(**e))
    story.append(Spacer(1,5))

story.append(Spacer(1,6))
story.append(Paragraph("Nonprofit / Tax-Exempt Entities  (Affiliated — NOT owned by SmithCap Group)", 
    S('sec2', fontSize=9, textColor=TEAL, fontName='Helvetica-Bold', spaceAfter=4)))

nbox = Table([[Paragraph(
    "These entities are 501(c)(3) nonprofits. David serves in a leadership/director role. "
    "Smith Capital Group does not hold ownership interest — they operate independently. "
    "SmithCap may provide paid management services to these entities via a formal services agreement.",
    NOTE)]], colWidths=[7.6*inch])
nbox.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,-1),LTEAL),('BOX',(0,0),(-1,-1),1,TEAL),
    ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
]))
story.append(nbox)
story.append(Spacer(1,4))

for e in nonprofits:
    story.append(entity_card(**e))
    story.append(Spacer(1,5))

story.append(Spacer(1,8))

# ── FORMATION PRIORITY TABLE ───────────────────────────────────────
story.append(Paragraph("FORMATION PRIORITY ROADMAP", S('lbl3', fontSize=7.5, textColor=GRAY, fontName='Helvetica-Bold', letterSpacing=1.5)))
story.append(Spacer(1,4))

roadmap = [
    ["Priority", "Entity", "Action", "Timeline", "Est. Cost"],
    ["🔴 1", "Smith Capital Group LLC", "Form new TX LLC — file Articles of Organization", "Now", "~$300"],
    ["🔴 2", "Smith Capital Properties LLC", "Reinstate — file PIR + franchise tax + Form 811", "30 days", "~$200–500"],
    ["🟡 3", "Clarity Solar Services LLC", "Form TX LLC + S-Corp election (IRS Form 2553)", "60 days", "~$300"],
    ["🟡 4", "S2T Designs LLC", "Form TX LLC + S-Corp election when net profit ≥ $40K", "60–90 days", "~$300"],
    ["🟢 5", "The Elevation ATX LLC", "Form TX LLC before first paid event", "Before event", "~$300"],
    ["🟢 6", "Nutrue Apparel LLC", "Form TX LLC or keep as DBA until revenue consistent", "When ready", "~$300"],
    ["⚪ 7", "SmithCap FMO LLC", "Form when capital deployment activity begins", "Q4 2026", "~$300"],
]

rt = Table(roadmap, colWidths=[0.7*inch, 2.5*inch, 2.45*inch, 1.0*inch, 0.75*inch], repeatRows=1)
rt.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),WHITE),
    ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),
    ('ALIGN',(0,0),(-1,-1),'LEFT'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,LGRAY]),
    ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#CCCCCC')),
    ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
    ('BACKGROUND',(0,1),(-1,2),colors.HexColor('#FFEBEE')),  # red priority rows
    ('BACKGROUND',(0,3),(-1,4),colors.HexColor('#FFF8E1')),  # yellow
]))
story.append(rt)
story.append(Spacer(1,8))

# ── TAX STRATEGY NOTE ──────────────────────────────────────────────
tax_note = Table([[Paragraph(
    "<b>💡 Tax Strategy Summary:</b>  Smith Capital Group LLC (parent) = pass-through, no payroll required. "
    "Operating LLCs elect S-Corp status once net profit clears ~$40K/year — pay yourself a reasonable salary, "
    "take the rest as distributions, save 15.3% SE tax on the distribution portion. "
    "Nonprofits (XFTC, PBS) file separately and are never included in SmithCap Group's tax return.",
    S('tn', fontSize=8, textColor=DGRAY, leading=12)
)]], colWidths=[7.6*inch])
tax_note.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,-1),LGOLD),('BOX',(0,0),(-1,-1),1,GOLD),
    ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
    ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
]))
story.append(tax_note)
story.append(Spacer(1,8))

# ── FOOTER ─────────────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CCCCCC'), spaceAfter=4))
story.append(Paragraph(
    "Smith Capital Group LLC  ·  Pflugerville, TX  ·  Confidential — For Internal Use Only  ·  Prepared June 5, 2026",
    S('ft', fontSize=7.5, textColor=GRAY, alignment=TA_CENTER)
))

doc.build(story)
print("Done")
