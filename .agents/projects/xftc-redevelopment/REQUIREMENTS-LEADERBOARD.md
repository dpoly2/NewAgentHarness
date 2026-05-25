# XFTC Leaderboard & Results Layout Requirements
## Goal
Create an Athletic.net / MileSplit style leaderboard showing Top 10-20 athletes per event and division, along with individual athlete history.

## Views Needed

### 1. Leaderboard (Top Times/Marks)
**Route:** `/results/leaderboard` or `[xftc_leaderboard]`
**Structure:**
- Filter bar: Season (2026 Outdoor, etc.), Gender (Boys/Girls), Division (Age Group)
- Grouped by Event Category (100m, 400m, Long Jump, etc.)
- Table per event:
  - Rank (1-10)
  - Result Value (Time/Mark)
  - Athlete Name (Linked to profile)
  - Meet Name & Date
  - Wind (if applicable, though we may skip this for AAU basic)
- Visual cues: PR badges, Club Record badges

### 2. Athlete Profile (Results History)
**Route:** `/athlete/{id}` or portal stats tab
**Structure:**
- Header: Athlete Name, Age, Division, PR summary
- Results Table (All-Time or Season):
  - Event
  - Result
  - Place
  - Meet Name
  - Date
- Progression Chart:
  - Chart.js line graph showing result over time for selected event.

## Database & Logic Updates
- **wp_xftc_results** table already tracks `result_value` as VARCHAR. We need a way to properly sort times (e.g. 10.02s vs 1:45.3) and marks (25-11.5).
- We may need a helper function to convert `result_value` to a standard decimal (seconds for track, meters/inches for field) for accurate `ORDER BY`.

## Shortcodes
- `[xftc_leaderboard limit="10" season="current"]`
- `[xftc_athlete_results id="123"]`
