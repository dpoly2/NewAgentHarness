# Psi Beta Sigma 1914 — Austin Sigmas Chapter Website

**Live URL:** https://newsite.psibetasigma1914.org  
**Admin URL:** https://newsite.psibetasigma1914.org/wp-admin  
**Platform:** WordPress (Kadence Theme)  
**Agency:** S2T Designs  
**Last Updated:** May 2026  

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Site Architecture](#site-architecture)
4. [Installed Plugins](#installed-plugins)
5. [Brand Guidelines](#brand-guidelines)
6. [Page Inventory](#page-inventory)
7. [Navigation Structure](#navigation-structure)
8. [Officer Roster & Emails](#officer-roster--emails)
9. [Events & Ticketing](#events--ticketing)
10. [Next Steps](#next-steps)
11. [Content Management Guide](#content-management-guide)
12. [Credentials & Access](#credentials--access)

---

## Project Overview

The Austin Sigmas Chapter of Phi Beta Sigma Fraternity, Inc. needed a modern, professional web presence to serve its members, alumni, and community. This site was built from scratch on WordPress using the Kadence theme to replicate the visual quality and structure of the PBS Gulf Coast Region reference site (pbsgulfcoastregion.org) — without licensing costs.

**Goals:**
- Establish a credible digital presence for the chapter
- Enable event registration and ticket sales
- Provide a member portal for active brothers
- Publish news, announcements, and program updates
- Showcase the Executive Board and leadership

---

## Tech Stack

| Layer | Technology |
|---|---|
| CMS | WordPress (latest) |
| Theme | Kadence (free tier) |
| Page Builder | Kadence Blocks |
| Hosting | Namecheap / Bosnacweb (shared) |
| PHP Memory | 256MB (configured) |
| Events | The Events Calendar + Event Tickets |
| Forms | WPForms Lite |
| Email | MailPoet |
| Members | ProfilePress |
| SEO | Yoast SEO |
| Admin User | s2tdesignadmin |

---

## Site Architecture

```
newsite.psibetasigma1914.org/
├── Home
├── About Us/
│   ├── President's Corner
│   └── Executive Board
├── Programs
├── Events  (The Events Calendar)
│   └── 2026 Annual Scholarship Golf Tournament
├── News  (WordPress Posts)
├── Join Sigma
├── Groups
├── Members Portal  (ProfilePress login)
│   └── Membership Roster
├── Golf Tournament  (dedicated landing page)
└── Contact
```

---

## Installed Plugins

| Plugin | Purpose | Status |
|---|---|---|
| Kadence Blocks | Block-based page builder | ✅ Active |
| Kadence Starter Templates | Theme templates library | ✅ Active |
| The Events Calendar | Event listing & calendar | ✅ Active |
| Event Tickets | RSVP & ticket registration | ✅ Active |
| WPForms Lite | Contact & intake forms | ✅ Active |
| MailPoet | Email newsletters | ✅ Active |
| ProfilePress | Member login & portal | ✅ Active |
| Yoast SEO | Search engine optimization | ✅ Active |
| Akismet | Spam protection | ⏸ Inactive |

---

## Brand Guidelines

| Element | Value |
|---|---|
| Primary Color | Royal Blue `#164f90` |
| Secondary Color | White `#FFFFFF` |
| Accent | Black `#000000` |
| Dark Navy | `#0F3765` |
| Light Blue (bg) | `#E8EFF8` |
| Typography | Open Sans (Google Fonts) |
| Logo | Austin Sigmas Chapter Seal |
| Logo Source | GitHub → `.agents/projects/s2tdesigns/clients/pbs/assets/logo/image0.jpeg` |

**Usage Rules:**
- Royal Blue is the dominant color on all headers, hero sections, and buttons
- White is the primary text and background color
- Black is used for accent lines, borders, and dividers only
- Gold (`#FFC72C`) has been removed from all branded documents

---

## Page Inventory

| # | Page | URL Slug | Status | Notes |
|---|---|---|---|---|
| 1 | Home | `/` | ✅ Published | Hero + mission intro |
| 2 | About Us | `/about-us/` | ✅ Published | Chapter story |
| 3 | President's Corner | `/about-us/presidents-corner/` | ✅ Published | Bro. Tarrell Matlock |
| 4 | Executive Board | `/about-us/executive-board/` | ✅ Published | 8-officer card grid |
| 5 | Programs | `/programs/` | ✅ Published | Chapter initiatives |
| 6 | Events | `/events/` | ✅ Published | Live calendar |
| 7 | News | `/news/` | ✅ Published | Posts archive |
| 8 | Join Sigma | `/join-sigma/` | ✅ Published | Membership info |
| 9 | Groups | `/groups/` | ✅ Published | Chapter groups |
| 10 | Members Portal | `/members-portal/` | ✅ Published | ProfilePress login |
| 11 | Membership Roster | `/membership-roster/` | ✅ Published | Active brothers table |
| 12 | Golf Tournament | `/golf-tournament/` | ✅ Published | 2026 event landing page |
| 13 | Contact | `/contact/` | ✅ Published | Contact info |

---

## Navigation Structure

```
Primary Navigation (Menu ID: 4)
├── About Us
│   ├── President's Corner
│   └── Executive Board
├── Programs
├── Events
├── Join Sigma
├── Groups
├── News
├── Members Portal
│   └── Membership Roster
├── Contact
└── Golf Tournament
```

---

## Officer Roster & Emails

| # | Brother | Office | Email |
|---|---|---|---|
| 1 | Bro. Tarrell Matlock | President | president@psibetasigma1914.org |
| 2 | Bro. Rafeal Williams | 1st Vice President | 1stvp@psibetasigma1914.org |
| 3 | Bro. Antwon Horn | 2nd Vice President | 2ndvp@psibetasigma1914.org |
| 4 | Bro. Jai Cotman | Secretary | secretary@psibetasigma1914.org |
| 5 | Bro. Shaun Stagge | Financial Secretary | financialsecretary@psibetasigma1914.org |
| 6 | Bro. David Smith | Treasurer | treasurer@psibetasigma1914.org |
| 7 | Bro. Andre Siebert | Director of National Programs | nationalprograms@psibetasigma1914.org |
| 8 | Christian Broussard | Marketing Director | marketing@psibetasigma1914.org |

**General Chapter:** office@psibetasigma1914.org

---

## Events & Ticketing

### 2026 Annual Scholarship Golf Tournament
- **Event URL:** `/event/2026-annual-scholarship-golf-tournament/`
- **Landing Page:** `/golf-tournament/` (Register button points to event URL)
- **Date:** September 12, 2026
- **Venue:** Grey Rock Golf & Tennis, 5914 Lost Horizon Dr, Austin TX 78739
- **Format:** 6-6-6 Scramble
- **Capacity:** 72 players
- **RSVP Opens:** June 1, 2026
- **Ticketing:** Event Tickets (RSVP) — Stripe/PayPal not yet connected

### Adding Future Events
1. Go to **Events → Add New** in wp-admin
2. Set title, description, start/end date, and venue
3. Upload a featured image
4. Click **Publish** — appears on `/events/` automatically

---

## Next Steps

### 🔴 High Priority
- [ ] **Connect payment gateway** (Stripe or PayPal) to Event Tickets Commerce so the chapter can sell paid golf tournament tickets ($125/player suggested)
- [ ] **Create WPForms contact form** (Name / Email / Subject / Message) and insert shortcode into `/contact/` and `/join-sigma/` pages
- [ ] **Upload officer headshots** to Media Library and update Executive Board page cards
- [ ] **Migrate domain** — point `psibetasigma1914.org` to new site once content is finalized

### 🟡 Medium Priority
- [ ] **Populate President's Corner** with a full message from Bro. Tarrell Matlock (biography, photo, vision statement)
- [ ] **Activate MailPoet newsletter** — create a signup form and embed on Home and News pages
- [ ] **Add alumni roster** to Membership Roster page (contact Secretary to collect data)
- [ ] **Set up Google Analytics** — install tracking code or use Yoast's integration
- [ ] **Configure ProfilePress** member portal fully — member login, profile fields, dues status
- [ ] **Add line names** to Membership Roster table for each brother

### 🟢 Lower Priority
- [ ] **Add chapter history** content to About Us page
- [ ] **Create Programs sub-pages** for each initiative (mentorship, scholarship, community service)
- [ ] **Configure Yoast SEO** meta descriptions and open graph images for all 13 pages
- [ ] **Add Groups page content** — define each fraternity auxiliary group
- [ ] **Enable Akismet** spam protection with an API key
- [ ] **Set up automated news posts** for meeting announcements and recaps

### 🏗️ Future Enhancements
- [ ] **Online dues payment portal** — members pay annual dues via stripe through Members Portal
- [ ] **Scholarship application form** — WPForms intake for annual scholarship program
- [ ] **Photo gallery** — chapter events, brotherhood photos, community service
- [ ] **Private members-only section** — restrict Membership Roster to logged-in users only
- [ ] **Mobile app push notifications** via MailPoet for event reminders

---

## Content Management Guide

### Editing a Page
1. Log in at `/wp-admin`
2. Go to **Pages → All Pages**
3. Click the page title to edit
4. Use the Gutenberg block editor — click any block to edit
5. Click **Update** to save

### Adding a News Post
1. Go to **Posts → Add New**
2. Write title and content
3. Set a Category (Announcements, Programs, News)
4. Add a Featured Image
5. Click **Publish**

### Adding an Event
1. Go to **Events → Add New**
2. Set title, dates, venue, and featured image
3. Click **Publish** — appears on `/events/` automatically

### Adding an Officer Photo
1. Go to **Media → Add New** and upload the headshot
2. Copy the image URL
3. Go to **Pages → Executive Board → Edit**
4. Find the officer's image block and replace the placeholder

---

## Credentials & Access

> ⚠️ **Security Note:** Rotate these credentials after site launch. Store securely — do not commit plaintext passwords to public repositories.

| Item | Value |
|---|---|
| Admin Username | s2tdesignadmin |
| Admin URL | https://newsite.psibetasigma1914.org/wp-admin |
| API Auth Method | WordPress Application Password |
| Hosting | Namecheap / Bosnacweb |
| PHP Memory Limit | 256MB |
| GitHub Repo | dpoly2/AgentHarness |

---

## File References (GitHub)

```
AgentHarness/
├── projects/pbs/
│   ├── pbs_site_launch.pptx       ← Site launch presentation
│   └── pbs_user_guide.pdf         ← Content management user guide
└── .agents/projects/s2tdesigns/clients/pbs/
    ├── BRAND-GUIDE.md              ← PBS brand guidelines
    ├── PROJECT.md                  ← Project brief
    ├── THEME-RESEARCH.md           ← Theme selection research
    └── assets/
        └── logo/image0.jpeg        ← Official chapter seal
```

---

*Documentation maintained by S2T Designs Agency | AgentJames — Base44 Superagent*  
*Last updated: May 23, 2026*
