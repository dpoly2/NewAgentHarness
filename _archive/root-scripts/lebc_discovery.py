from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

doc = SimpleDocTemplate(
    "lebc_discovery_questionnaire.pdf",
    pagesize=letter,
    rightMargin=0.75*inch,
    leftMargin=0.75*inch,
    topMargin=0.75*inch,
    bottomMargin=0.75*inch
)

# Colors
ROYAL_BLUE = colors.HexColor("#1A3A6B")
GOLD = colors.HexColor("#C9A84C")
LIGHT_CREAM = colors.HexColor("#FAF7F2")
CHARCOAL = colors.HexColor("#2D2D2D")
LIGHT_GRAY = colors.HexColor("#EEEEEE")

styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle("Title", parent=styles["Normal"],
    fontSize=22, textColor=ROYAL_BLUE, fontName="Helvetica-Bold",
    alignment=TA_CENTER, spaceAfter=4)

subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"],
    fontSize=11, textColor=GOLD, fontName="Helvetica-Bold",
    alignment=TA_CENTER, spaceAfter=2)

meta_style = ParagraphStyle("Meta", parent=styles["Normal"],
    fontSize=9, textColor=colors.HexColor("#888888"),
    alignment=TA_CENTER, spaceAfter=16)

section_header_style = ParagraphStyle("SectionHeader", parent=styles["Normal"],
    fontSize=12, textColor=colors.white, fontName="Helvetica-Bold",
    leftIndent=8, spaceAfter=0, spaceBefore=0)

question_label_style = ParagraphStyle("QuestionLabel", parent=styles["Normal"],
    fontSize=10, textColor=ROYAL_BLUE, fontName="Helvetica-Bold",
    spaceAfter=3, spaceBefore=10)

question_note_style = ParagraphStyle("QuestionNote", parent=styles["Normal"],
    fontSize=8.5, textColor=colors.HexColor("#666666"), fontName="Helvetica-Oblique",
    spaceAfter=2)

answer_style = ParagraphStyle("Answer", parent=styles["Normal"],
    fontSize=9, textColor=CHARCOAL, spaceAfter=2)

footer_style = ParagraphStyle("Footer", parent=styles["Normal"],
    fontSize=8, textColor=colors.HexColor("#999999"), alignment=TA_CENTER)

story = []

# ─── HEADER ───
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph("LITTLE EBENEZER BAPTIST CHURCH", title_style))
story.append(Paragraph("Website Revamp — Discovery Questionnaire", subtitle_style))
story.append(Paragraph("Prepared by S2T Designs  |  May 2026  |  Confidential", meta_style))
story.append(HRFlowable(width="100%", thickness=2, color=GOLD, spaceAfter=16))

intro_style = ParagraphStyle("Intro", parent=styles["Normal"],
    fontSize=9.5, textColor=CHARCOAL, leading=14, spaceAfter=16,
    backColor=LIGHT_CREAM, borderPadding=10)
story.append(Paragraph(
    "Pastor Spence, thank you for partnering with S2T Designs for this project. "
    "This questionnaire helps us build a website that truly represents Little Ebenezer Baptist Church — "
    "your mission, your community, and your vision. Please answer as much as you can; "
    "we'll cover the rest together in our discovery meeting.",
    intro_style))

# ─── SECTION BUILDER ───
def section(title, questions):
    # Section header bar
    header_data = [[Paragraph(f"  {title}", section_header_style)]]
    header_table = Table(header_data, colWidths=[7*inch])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), ROYAL_BLUE),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(Spacer(1, 0.18*inch))
    story.append(header_table)
    story.append(Spacer(1, 0.06*inch))

    for i, q in enumerate(questions, 1):
        label = q["q"]
        note = q.get("note", "")
        lines = q.get("lines", 2)

        story.append(Paragraph(f"{i}. {label}", question_label_style))
        if note:
            story.append(Paragraph(f"  ✦ {note}", question_note_style))

        # Answer lines
        for _ in range(lines):
            line_table = Table([[""]], colWidths=[6.9*inch], rowHeights=[0.28*inch])
            line_table.setStyle(TableStyle([
                ("LINEBELOW", (0,0), (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
                ("LEFTPADDING", (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (-1,-1), 0),
                ("TOPPADDING", (0,0), (-1,-1), 0),
                ("BOTTOMPADDING", (0,0), (-1,-1), 0),
            ]))
            story.append(line_table)
        story.append(Spacer(1, 0.04*inch))

# ─── SECTIONS ───

section("1. Church Identity & History", [
    {"q": "What is the founding year of Little Ebenezer Baptist Church?", "lines": 1},
    {"q": "In 2–3 sentences, how would you describe the mission of LEBC?",
     "note": "This will be used on the homepage and About page.", "lines": 3},
    {"q": "What makes LEBC unique compared to other churches in the Hutto area?", "lines": 3},
    {"q": "Is there a founding story or significant church history you'd like featured?", "lines": 3},
    {"q": "What is your current church theme or vision for 2025–2026?", "lines": 2},
])

section("2. Congregation & Audience", [
    {"q": "Who is your primary website audience — existing members, new visitors, or both?", "lines": 1},
    {"q": "Approximate congregation size:", "lines": 1},
    {"q": "What is the age range/makeup of your congregation?",
     "note": "e.g. Family-focused, primarily seniors, young adults, mixed.", "lines": 2},
    {"q": "What neighborhoods or ZIP codes do most of your members come from?", "lines": 2},
    {"q": "Are there specific groups you're trying to reach or grow? (e.g. young families, youth, seniors)", "lines": 2},
])

section("3. Services & Schedule", [
    {"q": "List all regular weekly services with day, time, and name:",
     "note": "e.g. Sunday School, Sunday Worship, Wednesday Bible Study", "lines": 4},
    {"q": "Are there any services or programs that are seasonal or quarterly?", "lines": 2},
    {"q": "Do you livestream services? If so, which platform? (YouTube, Facebook Live, Zoom)", "lines": 2},
])

section("4. Ministries", [
    {"q": "List all active ministries (name, leader, brief description, meeting day/time):",
     "note": "e.g. Youth Ministry, Women's Ministry, Men's Ministry, Choir, Outreach, etc.", "lines": 8},
    {"q": "Which ministries are most active and should be featured prominently?", "lines": 2},
    {"q": "Are any ministries currently recruiting or open to new members?", "lines": 2},
])

section("5. Pastor & Leadership", [
    {"q": "Full name and title for the pastor bio page:", "lines": 1},
    {"q": "Brief biography of Rev. Arthur L. Spence (background, calling, education, years at LEBC):",
     "note": "3–5 sentences is ideal. We can help write/edit.", "lines": 5},
    {"q": "Would you like to feature First Lady LaShell M. Spence on the Pastor page?", "lines": 1},
    {"q": "Are there any other key leaders, deacons, or staff to feature?", "lines": 3},
    {"q": "Do you have professional headshots of the pastor and first lady?",
     "note": "If not, we recommend a simple photo session before launch.", "lines": 1},
])

section("6. Online Giving & Tithes", [
    {"q": "Do you currently accept online giving or tithes? If so, what platform?",
     "note": "e.g. Cash App, PayPal, Zelle, Tithe.ly, Pushpay", "lines": 2},
    {"q": "Would you like a dedicated Give/Tithe page with online giving on the new site?", "lines": 1},
    {"q": "Do you have specific giving funds to feature? (e.g. General Fund, Building Fund, Missions)",  "lines": 2},
    {"q": "Do you want to offer recurring giving (automatic weekly/monthly tithe)?", "lines": 1},
])

section("7. Sermons & Media", [
    {"q": "Do you record and post Sunday sermons? Where are they currently posted?", "lines": 2},
    {"q": "YouTube channel URL (if applicable):", "lines": 1},
    {"q": "Would you like a Sermon Archive page where visitors can search past messages?", "lines": 1},
    {"q": "Are there other media assets to include? (podcasts, devotionals, radio broadcast)", "lines": 2},
])

section("8. Events & Communications", [
    {"q": "What upcoming events should be on the new site at launch?",
     "note": "e.g. revivals, conferences, community outreach, holiday services", "lines": 4},
    {"q": "How do you currently communicate with members? (email, text, Facebook, church bulletin)", "lines": 2},
    {"q": "Would you like an email newsletter signup on the website?", "lines": 1},
    {"q": "Would you like a digital church bulletin or weekly announcement section?", "lines": 1},
])

section("9. Website Management", [
    {"q": "Who will be responsible for updating the website after launch?",
     "note": "Name and role — we will provide training and a simple guide.", "lines": 2},
    {"q": "How comfortable is your team with basic website editing? (1 = not comfortable, 5 = very comfortable)",
     "lines": 1},
    {"q": "How often do you anticipate needing to update content?",
     "note": "e.g. Weekly (events/sermons), Monthly (general content), Rarely", "lines": 1},
    {"q": "Would you like S2T Designs to provide ongoing monthly maintenance support?", "lines": 1},
])

section("10. Design Preferences", [
    {"q": "List 2–3 church websites you admire and what you like about them:", "lines": 4},
    {"q": "Are there any colors, fonts, or design styles you want to avoid?", "lines": 2},
    {"q": "Do you have an existing logo you want to keep, or are you open to a refresh?", "lines": 2},
    {"q": "What feeling should a visitor have when they land on your homepage?",
     "note": "e.g. welcoming, powerful, peaceful, joyful, reverent", "lines": 2},
])

section("11. Budget & Timeline", [
    {"q": "What is your approximate budget for this website project?",
     "note": "Typical church sites range from $1,500–$4,000 depending on features.", "lines": 1},
    {"q": "Is there a specific launch date or event you want the site ready for?", "lines": 1},
    {"q": "Are there any budget constraints we should design around?", "lines": 2},
])

section("12. Anything Else?", [
    {"q": "Is there anything else about LEBC — your community, your vision, your members — that you want the website to communicate?", "lines": 4},
    {"q": "Any questions or concerns about the website project you'd like to discuss?", "lines": 3},
])

# ─── FOOTER ───
story.append(Spacer(1, 0.3*inch))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=8))
story.append(Paragraph(
    "S2T Designs  |  David Smith, Principal  |  s2tdesigns.com  |  Prepared for Rev. Arthur L. Spence, Little Ebenezer Baptist Church, Hutto TX",
    footer_style))

doc.build(story)
print("✓ PDF generated: lebc_discovery_questionnaire.pdf")
