# The Sigma Signal — Newsletter Structure
**Version:** 1.0
**Date:** 2026-05-25
**Based on:** Analysis of 6 national PBS Constant Contact issues + project requirements

---

## Visual Layout (Top to Bottom)

```
┌─────────────────────────────────────────────┐
│           HEADER BANNER                      │
│   [PBS Logo + "The Sigma Signal" wordmark]   │
│   [Month Year | Issue #] — Royal Blue BG     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│        SECTION 1: SIGMA BRAINTEASER          │
│   🧠 Oxford Blue header bar                  │
│   Puzzle statement (3–6 sentences)           │
│   [Submit Your Answer] button (optional)     │
│   * Answer Key delivered as SEPARATE file *  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│        SECTION 2: CHAPTER SPOTLIGHT          │
│   🌟 Royal Blue header bar                   │
│   Chapter name + photo placeholder           │
│   Spotlight copy (150–250 words)             │
│   New initiates list (if applicable)         │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│        SECTION 3: POEM                       │
│   ✍️ Midnight Blue header bar                │
│   Poem title (italic)                        │
│   Poem body (left-aligned or centered)       │
│   — Author Name / "The Sigma Signal"         │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│        SECTION 4: SIGMA TRIVIA               │
│   ❓ Powder Blue header bar + dark text      │
│   3–5 numbered trivia questions              │
│   [Answers in next issue / answer file]      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│        SECTION 5: MEMBERSHIP TIPS            │
│   💡 Royal Blue header bar                   │
│   3–5 numbered/bulleted tips                 │
│   Optional: sourced quote or message         │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│        SECTION 6: NEWS & UPDATES             │
│   📢 Oxford Blue header bar                  │
│   Short paragraph or bullet list             │
│   National/regional/chapter news             │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│        SECTION 7: SUBMIT YOUR CONTENT        │
│   📬 Cloud Blue BG (light section)           │
│   Call-to-action: "Share your story..."      │
│   Submission email / form link               │
│   Deadline reminder                          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│              FOOTER                          │
│   PBS Shield + Austin Sigmas logo            │
│   Chapter address                            │
│   Social media icons (IG, FB, Twitter/X)    │
│   Unsubscribe link (required by CC)          │
│   © 2026 Psi Beta Sigma Graduate Chapter     │
└─────────────────────────────────────────────┘
```

---

## Section Order Rationale
1. **BrainTeaser first** — hooks the reader immediately, creates engagement before they scroll
2. **Chapter Spotlight second** — community recognition, relatable content
3. **Poem third** — emotional + cultural depth, mid-newsletter break
4. **Trivia fourth** — light, interactive content to re-engage
5. **Membership Tips fifth** — practical value, brothers learn something
6. **News sixth** — informational, end of main content
7. **Submissions CTA last** — convert readers into contributors before footer

---

## Color Coding by Section

| Section | Header Bar Color | Background |
|---------|-----------------|------------|
| Header Banner | `#164f90` Royal Blue | `#164f90` |
| BrainTeaser | `#0B2848` Oxford Blue | `#FFFFFF` |
| Chapter Spotlight | `#164f90` Royal Blue | `#FFFFFF` |
| Poem | `#0F3765` Midnight Blue | `#E8EDF4` Cloud Blue |
| Trivia | `#A2B9D3` Powder Blue | `#FFFFFF` |
| Membership Tips | `#164f90` Royal Blue | `#FFFFFF` |
| News & Updates | `#0B2848` Oxford Blue | `#FFFFFF` |
| Submit CTA | — | `#E8EDF4` Cloud Blue |
| Footer | — | `#0B2848` Oxford Blue |

---

## Constant Contact Template Blocks

Each section maps to a CC content block:

| Block Type | Used For |
|-----------|----------|
| Image + Text | Header banner |
| Text (full width) | BrainTeaser, Poem |
| Image + Text | Chapter Spotlight (with photo) |
| Text with columns | Trivia (2-col: Q on left, category on right) |
| Button + Text | BrainTeaser answer CTA, Submissions CTA |
| Divider | Between all sections |
| Social Follow | Footer social icons |
| Footer | Unsubscribe, address, copyright |

---

## Brain Teaser Export Format

The brain teaser is exported as a **standalone HTML file** for copy-paste into Constant Contact:

```html
<!-- SIGMA BRAINTEASER BLOCK — paste into CC HTML editor -->
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px; margin:0 auto;">
  <tr>
    <td style="background-color:#0B2848; padding:12px 20px;">
      <h2 style="color:#ffffff; font-family:Arial,sans-serif; font-size:18px; margin:0;">
        🧠 Sigma BrainTeaser
      </h2>
    </td>
  </tr>
  <tr>
    <td style="background-color:#ffffff; padding:20px; font-family:Arial,sans-serif; color:#000000; font-size:15px; line-height:1.6;">
      <!-- PUZZLE TEXT GOES HERE -->
      <p><strong>[Puzzle Statement]</strong></p>
      <p>[Additional context or clues]</p>
      <p style="color:#5C84B1; font-size:13px;">
        * Answer key delivered separately — check your email or download below.
      </p>
    </td>
  </tr>
</table>
```

**Answer Key file:** Plain `.txt` or `.pdf` — named `sigma-signal-[YYYY-MM]-brainteaser-answer.txt`

---

## File Naming Convention

| File | Name Pattern |
|------|-------------|
| Issue draft | `sigma-signal-YYYY-MM-issue-NN-draft.md` |
| Brain Teaser HTML | `sigma-signal-YYYY-MM-brainteaser.html` |
| Answer Key | `sigma-signal-YYYY-MM-brainteaser-answer.txt` |
| Final CC-ready HTML | `sigma-signal-YYYY-MM-issue-NN-final.html` |

---

## Production Timeline (Per Issue)

| Day | Task | Agent |
|-----|------|-------|
| T-14 | Open content collection window | sigma-signal-submissions |
| T-7 | Submission deadline | sigma-signal-submissions |
| T-6 | Research fallback if needed | sigma-signal-researcher |
| T-5 | Draft all 7 sections | sigma-signal-writer, sigma-signal-poet |
| T-4 | Brain Teaser + Answer Key generated | sigma-signal-writer |
| T-3 | Editor review + revisions | sigma-signal-project-lead |
| T-2 | HTML export + CC formatting | sigma-signal-designer |
| T-1 | David reviews final draft | David Smith |
| T-0 | Send via Constant Contact | David Smith |
