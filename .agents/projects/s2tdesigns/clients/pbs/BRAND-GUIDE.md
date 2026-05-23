# Psi Beta Sigma 1914 — Brand Guidelines Summary
**Source:** Psi Beta Sigma Brand Guidelines 2.0 (official PDF)
**Extracted:** 2026-05-22
**For use by:** s2t-webdev-agent, s2t-brand-designer-agent

---

## Official Names

| Usage | Name |
|-------|------|
| Full official name | **Psi Beta Sigma Graduate Chapter** |
| Short form (after first reference) | Austin Sigmas |
| Chapter slang | G.O.M.A.B / BLU PHI / YOU KNOW |
| Hashtags | #AUSTINSIGMAS / #PBS1914 |
| Contact | Marketing@psibetasigma1914.org |
| Address | 12407 Mopac Expwy N, Suite 250-412, Austin, Texas 78758 |
| Website | psibetasigma1914.org |

---

## Color Palette

### Primary Colors (required in all designs)

| Name | Hex | RGB | CMYK | Use |
|------|-----|-----|------|-----|
| **PBS Royal Blue** | `#164f90` | R:22 G:79 B:144 | C:85 M:45 Y:0 K:44 | Primary brand color — headers, buttons, backgrounds |
| **PBS Pure White** | `#FFFFFF` | R:255 G:255 B:255 | C:0 M:0 Y:0 K:0 | Text on blue, backgrounds |

### Secondary Colors (accents + support)

| Name | Hex | RGB | Use |
|------|-----|-----|-----|
| **Powder Blue** | `#A2B9D3` | R:162 G:185 B:211 | Light sections, card backgrounds, dividers |
| **Cloud Blue** | `#E8EDF4` | R:232 G:237 B:244 | Page backgrounds, subtle section fills |
| **Soft Slate Blue** | `#5C84B1` | R:92 G:132 B:177 | Secondary buttons, hover states, icons |
| **Midnight Blue** | `#0F3765` | R:15 G:55 B:101 | Dark section backgrounds, footer |
| **Oxford Blue** | `#0B2848` | R:11 G:40 B:72 | Darkest tone — announcement bar, deep backgrounds |
| **Black** | `#000000` | R:0 G:0 B:0 | Body text on white |
| **Lavender Gray** | `#D9D9D9` | R:217 G:217 B:217 | Borders, dividers, disabled states |

### ⚠️ Color Rules
- Royal Blue and Pure White **must** appear in all designs
- **DO NOT** change the official Royal Blue to any other shade
- No unauthorized color variations

---

## Typography

### Primary Typeface — Open Sans
- **Use:** Headlines, large typographic moments, body copy
- **Weights available:** Light, Regular, Semi Bold, Bold
- **Google Fonts:** https://fonts.google.com/specimen/Open+Sans

### Secondary Typeface — Arial
- **Use:** Subheads, pull quotes, official documents, communications, applications requiring immediate legibility
- **Weights available:** Light, Regular, Semi Bold, Bold
- **Note:** System font — always available as fallback

### Typography Hierarchy for Web
```
H1 — Open Sans Bold — PBS Royal Blue or White
H2 — Open Sans Semi Bold — PBS Royal Blue or Midnight Blue
H3 — Open Sans Semi Bold — PBS Royal Blue or Black
Body — Open Sans Regular — Black (#000000) on white, White on blue
Nav — Open Sans Semi Bold — White on Royal Blue background
Buttons — Open Sans Bold — White text on Royal Blue
```

---

## Logo & Brand Marks

### 1. Psi Beta Sigma Wordmark (PRIMARY LOGO)
- **Full form:** "PHI BETA SIGMA FRATERNITY, INCORPORATED / PSI BETA SIGMA" stacked
- Primary identifier — use in most applications
- May be paired with approved fraternity marks

### 2. Austin Sigmas Monogram (SPIRIT MARK)
- Most recognizable symbol for apparel, social media, merch, event branding
- Text: "Austin Sigmas" in styled script/display font

### 3. Chapter Seal (OFFICIAL MARK)
- Reserved for official chapter communications and materials
- Elements: Austin cityscape, 3 stars (Honorable Founders), circular form (unity), founding date
- Contact Marketing@psibetasigma1914.org before using

### 4. Phi Beta Sigma Fraternity Shield (NATIONAL MARK)
- Represents Brotherhood, Scholarship, Service at national level
- Use respectfully, per national fraternity guidelines

### ⚠️ Logo Rules (DO NOTs)
- ❌ DO NOT stretch, compress, or distort any mark
- ❌ DO NOT rotate or tilt any mark
- ❌ DO NOT crop any part of the seal
- ❌ DO NOT change the official Royal Blue color
- ❌ DO NOT remove any elements from the seal
- ❌ DO NOT place logo over a pattern or busy photo
- ❌ DO NOT recreate, alter, or redesign any mark

---

## Photography Direction

### Use
- Brotherhood and fellowship moments
- Community service and outreach
- Professional and formal chapter events
- Leadership, mentoring, scholarship activities
- Authentic high-quality candid and posed shots

### Avoid
- Low-resolution or blurry images
- Overly filtered or distorted photos
- Unprofessional or off-brand visuals
- Poorly lit or improperly cropped media
- Images not aligned with Brotherhood, Scholarship, Service values

---

## WordPress Implementation Notes (Kadence Theme)

### Global Colors to Set in Kadence
```
Primary:    #164f90  (PBS Royal Blue)
Secondary:  #0F3765  (Midnight Blue)
Accent:     #5C84B1  (Soft Slate Blue)
Background: #FFFFFF  (Pure White)
Text:       #000000  (Black)
```

### Global Fonts to Set in Kadence
```
Headings:  Open Sans (Bold / Semi Bold)
Body:      Open Sans (Regular)
Buttons:   Open Sans (Bold)
```

### Announcement Bar
- Background: `#0B2848` (Oxford Blue) or `#164f90` (Royal Blue)
- Text: White
- Content: Chapter tagline or current event/news

### Header
- Background: `#164f90` (PBS Royal Blue)
- Logo: Psi Beta Sigma Wordmark (white version) on left
- Nav: White text, Open Sans Semi Bold
- Top right: "Members Area / Log In" — white text

### Hero Section
- Full-bleed photo (brotherhood/event photography per brand guide)
- Bold white headline overlay — Open Sans Bold
- Optional: Royal Blue gradient overlay on photo for text legibility

### Buttons
- Primary: `#164f90` background, white text, Open Sans Bold
- Hover: `#0F3765` (Midnight Blue)
- Secondary/outline: white border + text on blue background

### Footer
- Background: `#0F3765` (Midnight Blue) or `#0B2848` (Oxford Blue)
- Text: White
- Links: `#A2B9D3` (Powder Blue) for hover states

---

## Asset Files
- `assets/branding/Psi Beta Sigma Brand Guidelines 2.0.pdf` — full official guidelines
- `assets/logo/` — upload logo files here (SVG + PNG preferred)
- `assets/images/` — upload site photography here
