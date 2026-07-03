---
type: design-system
client: smithcap
version: 1.0
updated: 2026-07-03
---

# Smith Capital Properties Design System

## 1. Brand Identity
- **Brand Name:** Smith Capital Properties
- **Tagline:** Strategic Land. Durable Growth.
- **Positioning Statement:** Smith Capital Properties is an investor-grade real estate development brand focused on high-growth opportunities across the Williamson County and Travis County corridor, with emphasis on commercial land, mixed-use development, hospitality, and sports/recreation assets.
- **Brand Promise:** Present disciplined, locally informed opportunities with confidence, clarity, and long-horizon value creation.
- **Voice & Tone:** Professional, credible, direct, financially literate, growth-oriented. Speak like a sponsor who understands capital stacks, entitlement risk, and community alignment.
- **Audience Priorities:** Investors, lenders, civic partners, brokers, landowners, and strategic operating partners.

## 2. Color Palette
- **Primary**
  - `SmithCap Navy` — `#12314A`
  - `Growth Gold` — `#B8872E`
- **Secondary**
  - `Corridor Slate` — `#425466`
  - `Parchment Stone` — `#EDE7DD`
- **Accent**
  - `Austin Copper` — `#A65A3A`
  - `Opportunity Teal` — `#2E7D7B`
- **Neutral**
  - `Ink` — `#111827`
  - `Charcoal` — `#374151`
  - `Cloud` — `#F7F8FA`
  - `White` — `#FFFFFF`
- **Semantic**
  - `Success` — `#1F7A4D`
  - `Warning` — `#C47B18`
  - `Error` — `#B42318`
  - `Info` — `#1D5FA7`
- **Usage Notes:** Navy and white should dominate. Gold is for emphasis, not flood fills. Copper is reserved for project highlights like The Elevation or hospitality storytelling.

## 3. Typography
- **Heading Font:** Playfair Display Semibold
- **Body Font:** Inter
- **Code/Data Font:** JetBrains Mono
- **Scale**
  - `xs` — 12px
  - `sm` — 14px
  - `base` — 16px
  - `lg` — 18px
  - `xl` — 24px
  - `2xl` — 32px
- **Typographic Rules:** Headlines should feel polished and boardroom-ready. Body copy should stay clean, modern, and easy to scan in investor memos and one-pagers. Use monospaced text only for metrics, parcel IDs, underwriting assumptions, and tabular data.

## 4. Spacing & Layout
- **Grid System:** 12-column desktop grid, 8-column tablet grid, 4-column mobile grid
- **Breakpoints**
  - `sm` — 640px
  - `md` — 768px
  - `lg` — 1024px
  - `xl` — 1280px
- **Spacing Scale:** 4, 8, 12, 16, 24, 32, 48, 64
- **Max Widths**
  - Narrative pages — 1200px
  - Investor memos / decks — 1280px
  - Reading column — 720px
- **Layout Guidance:** Favor generous whitespace, strong alignment, and modular information blocks. Use clear section breaks for market, thesis, risk, structure, and next steps.

## 5. Iconography
- **Icon Library:** Lucide or Font Awesome Pro-style outline icons
- **Sizes:** 16px, 20px, 24px, 32px
- **Stroke Weight:** 1.75px to 2px
- **Style:** Primarily outline; filled icons only for status chips or map pins
- **Usage Notes:** Use icons to support deal flow, parcels, hospitality, construction, sports/recreation, finance, and timelines. Avoid playful or cartoonish icon sets.

## 6. Motion & Animation
- **Duration Tokens**
  - `fast` — 120ms
  - `base` — 180ms
  - `slow` — 280ms
- **Easing Curves**
  - `standard` — `cubic-bezier(0.2, 0, 0, 1)`
  - `enter` — `cubic-bezier(0.16, 1, 0.3, 1)`
  - `exit` — `cubic-bezier(0.7, 0, 0.84, 0)`
- **Transition Patterns:** Fade-up cards, subtle hover elevation, tabular highlight transitions, slide-in detail panels for project summaries
- **Motion Principle:** Motion should communicate polish and confidence, never hype. Keep animation minimal, restrained, and useful.

## 7. Component Patterns
- **Buttons**
  - Primary: Navy background, white text
  - Secondary: White background, navy border, navy text
  - Tertiary: Text link with gold underline or accent rule
- **Cards:** White or parchment cards with subtle shadow, 12px radius, clear headline + metrics + CTA
- **Forms:** Investor inquiry and contact forms should use simple labels, strong contrast, and minimal required fields
- **Navigation:** Clean top navigation with high-trust language such as Portfolio, Projects, Strategy, Investor Contact
- **Tables & Data Blocks:** Use mono numerals, strong row separation, muted headers, and clear summary bars for tract size, basis, projected use, and financing status
- **Maps & Site Plans:** Present with muted land tones, navy annotations, and gold callouts for subject property

## 8. Content Voice
- **Writing Principles**
  - Lead with strategic clarity, not hype
  - Use market context and investment logic
  - Frame partnerships and community benefit as strengths
  - Keep sentences tight, factual, and sponsor-ready
- **Do Examples**
  - “Smith Capital is targeting infill and edge-growth opportunities in the Hutto–Pflugerville corridor where infrastructure expansion supports long-term land appreciation.”
  - “The project pairs commercial activation with community-serving sports and recreation uses to strengthen both revenue diversity and local relevance.”
- **Don't Examples**
  - “This is an unbelievable deal you can’t miss.”
  - “We’re trying a bunch of things and seeing what sticks.”
- **Terminology Glossary**
  - `Growth corridor` — the Williamson/Travis County expansion zone
  - `Investor memo` — concise opportunity summary for capital partners
  - `Entitlement` — zoning, approvals, and municipal path to execution
  - `Community anchor` — mission-aligned use that strengthens public/private support

## 9. Anti-Patterns
- Do not use neon, tech-startup gradients, or crypto-style visuals.
- Do not overuse gold; it is an accent, not the foundation color.
- Do not mix more than two type families in one artifact.
- Do not write in slang, exaggerated sales language, or speculative promises.
- Do not present civic or nonprofit affiliations as decorative; explain their strategic relevance clearly.
- Do not use crowded dashboards, tiny tables, or low-contrast financial data.
