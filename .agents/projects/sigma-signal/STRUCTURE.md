# The Sigma Signal — Newsletter Structure
**Version:** 1.1
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
│        SECTION 1: CHAPTER SPOTLIGHT          │
│   🌟 Royal Blue header bar                   │
│   Chapter name + photo placeholder           │
│   Spotlight copy (150–250 words)             │
│   New initiates list (if applicable)         │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│        SECTION 2: EDITOR'S NOTE (optional)   │
│   ✉️ Oxford Blue header bar                  │
│   50–100 words from David                    │
│   Signed: — Bro. David Smith, Editor         │
│   * Skip this section if nothing to say *    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│        SECTION 3: POEM                       │
│   ✍️ Midnight Blue header bar                │
│   Poem title (italic)                        │
│   Poem body (left-aligned or centered)       │
│   — Author Name / "The Sigma Signal"         │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│        SECTION 4: SIGMA BRAIN GAMES          │
│   🧠 Oxford Blue header bar                  │
│   Sub-label: "This Issue: [BrainTeaser /     │
│               Trivia / Sudoku]"              │
│                                              │
│   OPTION A — BRAINTEASER                     │
│   Logic / wordplay / history puzzle          │
│   3–6 sentences. Answer key = separate file  │
│                                              │
│   OPTION B — TRIVIA                          │
│   3–5 numbered questions                     │
│   Answers in next issue or separate file     │
│                                              │
│   OPTION C — SUDOKU                          │
│   9×9 HTML table grid (medium difficulty)    │
│   Answer key = separate file                 │
│                                              │
│   * David picks A, B, or C each issue *      │
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
│   Submission email + form link               │
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
1. **Chapter Spotlight first** — mirrors national PBS newsletter pattern; community recognition leads
2. **Editor's Note second (optional)** — leadership voice; skip if nothing meaningful to add
3. **Poem third** — emotional and cultural anchor, mid-newsletter break
4. **Sigma Brain Games fourth** — rotating puzzle section; David picks format at issue kickoff
5. **Membership Tips fifth** — practical value, brothers learn something
6. **News & Updates sixth** — informational closing block
7. **Submissions CTA last** — convert readers into contributors before footer

---

## Brain Games — Per-Issue Format Selection
At the start of each production cycle, David selects one:

| Format | When to Use |
|--------|-------------|
| **BrainTeaser** | Logic/wordplay focus; when you want engagement and replies |
| **Trivia** | History/culture focus; good for building from previous issues |
| **Sudoku** | Visual variety; great for issues with lighter editorial content |

The section header is always **"Sigma Brain Games"** — the sub-label changes per issue.

---

## Color Coding by Section

| Section | Header Bar Color | Background |
|---------|-----------------|------------|
| Header Banner | `#164f90` Royal Blue | `#164f90` |
| Chapter Spotlight | `#164f90` Royal Blue | `#FFFFFF` |
| Editor's Note | `#0B2848` Oxford Blue | `#FFFFFF` |
| Poem | `#0F3765` Midnight Blue | `#E8EDF4` Cloud Blue |
| Sigma Brain Games | `#0B2848` Oxford Blue | `#FFFFFF` |
| Membership Tips | `#164f90` Royal Blue | `#FFFFFF` |
| News & Updates | `#0B2848` Oxford Blue | `#FFFFFF` |
| Submit CTA | — | `#E8EDF4` Cloud Blue |
| Footer | — | `#0B2848` Oxford Blue |

---

## Constant Contact Template Blocks

| Block Type | Used For |
|-----------|----------|
| Image + Text | Header banner |
| Image + Text | Chapter Spotlight (with photo) |
| Text (full width) | Editor's Note, Poem, News & Updates |
| Text (full width) | Brain Games — BrainTeaser or Trivia |
| HTML Table block | Brain Games — Sudoku grid |
| Numbered List | Membership Tips |
| Button + Text | Brain Games answer CTA, Submissions CTA |
| Divider | Between all sections |
| Social Follow | Footer social icons |
| Footer | Unsubscribe, address, copyright |

---

## Answer Key / Separate File Convention
For BrainTeaser and Sudoku issues, the answer key is NEVER included in the newsletter body.

| File | Name Pattern |
|------|-------------|
| Brain Teaser HTML block | `sigma-signal-YYYY-MM-brainteaser.html` |
| Trivia block (if HTML export needed) | `sigma-signal-YYYY-MM-trivia.html` |
| Sudoku grid HTML block | `sigma-signal-YYYY-MM-sudoku.html` |
| Answer Key (BrainTeaser or Sudoku) | `sigma-signal-YYYY-MM-answer-key.txt` |
| Full issue draft | `sigma-signal-YYYY-MM-issue-NN-draft.md` |
| Final CC-ready HTML | `sigma-signal-YYYY-MM-issue-NN-final.html` |

---

## Production Timeline (Per Issue)

| Day | Task | Agent |
|-----|------|-------|
| T-14 | Open content collection window | sigma-signal-submissions |
| T-7 | Submission deadline | sigma-signal-submissions |
| T-7 | **David selects Brain Games format for this issue** | David Smith |
| T-6 | Research fallback if needed | sigma-signal-researcher |
| T-5 | Draft all sections | sigma-signal-writer, sigma-signal-poet |
| T-4 | Brain Games content + Answer Key generated | sigma-signal-writer |
| T-3 | Editor review + revisions | sigma-signal-project-lead |
| T-2 | HTML export + CC formatting | sigma-signal-designer |
| T-1 | David reviews final draft | David Smith |
| T-0 | Send via Constant Contact | David Smith |
