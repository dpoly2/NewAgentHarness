---
type: design-system
client: xftc
version: 1.0
updated: 2026-07-03
---

# Xtreme Force Track Club Design System

## 1. Brand Identity
- **Brand Name:** Xtreme Force Track Club
- **Tagline:** Build Speed. Build Confidence.
- **Positioning Statement:** Xtreme Force Track Club is a youth development track and field organization that combines athletic training, competitive opportunity, and family-centered support into a disciplined, high-energy club experience.
- **Brand Promise:** Deliver a fast, motivational, structured brand that reflects performance, growth, and community pride.
- **Voice & Tone:** Energetic, athletic, motivational, organized, encouraging. Speak like a coach who values discipline, progress, and belonging.
- **Audience Priorities:** Parents, athletes, coaches, volunteers, and event participants.

## 2. Color Palette
- **Primary**
  - `Force Navy` — `#0C2340`
  - `Victory Gold` — `#D4A017`
- **Secondary**
  - `Sprint Red` — `#C62828`
  - `Track White` — `#FFFFFF`
- **Accent**
  - `Electric Blue` — `#1E88E5`
  - `Finish Line Gray` — `#6B7280`
- **Neutral**
  - `Jet` — `#111827`
  - `Graphite` — `#374151`
  - `Cloud` — `#F5F7FA`
  - `Lane Silver` — `#D1D5DB`
- **Semantic**
  - `Success` — `#15803D`
  - `Warning` — `#D97706`
  - `Error` — `#B91C1C`
  - `Info` — `#2563EB`
- **Usage Notes:** Navy and gold establish the main identity. Red is a performance accent for CTA moments, meet alerts, and action states. Avoid spreading all three strong colors equally in the same composition.

## 3. Typography
- **Heading Font:** Montserrat ExtraBold
- **Body Font:** Inter
- **Code/Data Font:** Roboto Mono
- **Scale**
  - `xs` — 12px
  - `sm` — 14px
  - `base` — 16px
  - `lg` — 18px
  - `xl` — 26px
  - `2xl` — 36px
- **Typographic Rules:** Headlines should feel bold, athletic, and high-visibility. Body copy should remain simple for parents managing registration, schedules, and payments. Use strong numeric styling for times, meet dates, and performance data.

## 4. Spacing & Layout
- **Grid System:** 12-column desktop grid, 8-column tablet grid, 4-column mobile grid
- **Breakpoints**
  - `sm` — 640px
  - `md` — 768px
  - `lg` — 1024px
  - `xl` — 1280px
- **Spacing Scale:** 4, 8, 12, 16, 20, 24, 32, 48, 64
- **Max Widths**
  - Site shell — 1280px
  - Portal dashboard — 1360px
  - Reading column — 760px
- **Layout Guidance:** Keep interfaces fast to scan and easy to act on. Prioritize clear hierarchy for registration steps, roster status, practice schedules, event dates, and athlete performance summaries.

## 5. Iconography
- **Icon Library:** Lucide, Heroicons, or Font Awesome Sports set
- **Sizes:** 16px, 20px, 24px, 32px
- **Stroke Weight:** 2px
- **Style:** Bold outline icons with occasional filled badges for achievements or notifications
- **Usage Notes:** Use track, stopwatch, medal, calendar, roster, payment, and location icons. Icons should reinforce motion and organization without becoming cartoon mascots.

## 6. Motion & Animation
- **Duration Tokens**
  - `fast` — 100ms
  - `base` — 160ms
  - `slow` — 240ms
- **Easing Curves**
  - `standard` — `cubic-bezier(0.2, 0, 0, 1)`
  - `accelerate` — `cubic-bezier(0.3, 0, 0.8, 0.15)`
  - `decelerate` — `cubic-bezier(0.05, 0.7, 0.1, 1)`
- **Transition Patterns:** Quick hover shifts, scorecard count-ups, slide transitions between registration steps, subtle celebratory pulses for successful completion states
- **Motion Principle:** Motion should feel fast and motivating, but never chaotic. Performance energy should support usability.

## 7. Component Patterns
- **Buttons**
  - Primary: Gold or red emphasis on navy background contexts
  - Secondary: Navy background with white text
  - Utility: White or light gray background with navy text for dashboard actions
- **Cards:** Strong headline, athlete or event status, prominent CTA, 14px radius, subtle shadow
- **Forms:** Multi-step registration with clear progress, large tap targets, inline validation, and mobile-first layout
- **Navigation:** Home, Programs, Register, Schedule, Results, Portal, Contact
- **Dashboards:** KPI tiles for dues, meets, attendance, and recent results; include clear empty states
- **Email Templates:** Branded header strip, strong CTA button, concise schedule and payment details

## 8. Content Voice
- **Writing Principles**
  - Motivate without overpromising
  - Keep instructions crisp for busy families
  - Celebrate development, discipline, and consistency
  - Sound organized and team-oriented
- **Do Examples**
  - “Train with purpose, compete with confidence, and track progress all season long.”
  - “Parents can manage registration, schedules, and meet updates from one streamlined portal.”
- **Don't Examples**
  - “Become a champion overnight.”
  - “Only elite athletes belong here.”
- **Terminology Glossary**
  - `Portal` — parent/athlete dashboard for membership activity
  - `Meet schedule` — official event calendar and logistics
  - `TrackSuite` — XFTC membership and management system
  - `Athlete development` — training, discipline, confidence, and performance growth

## 9. Anti-Patterns
- Do not overload layouts with all-caps text, flames, speed streaks, or generic sports clichés.
- Do not mix too many accent colors in the same screen.
- Do not hide registration or payment actions behind low-contrast buttons.
- Do not use small text for schedules, meet info, or parent instructions.
- Do not make the club feel exclusionary, intimidating, or hyper-commercial.
- Do not use slow, heavy animations that hurt portal responsiveness.
