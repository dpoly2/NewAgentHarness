"""
data_import.py — ArchonHub Data Seeder
=======================================
Imports all existing markdown/JSON source files into the SQLite DB so that
Inez and all surfaces can operate from the database with no file references.

Run once to seed; safe to re-run (idempotent via upsert patterns).
Usage:
    python data_import.py               # run all importers
    python data_import.py --agents      # agents only
    python data_import.py --projects    # projects only
    python data_import.py --clients     # clients only
    python data_import.py --automations # automations only
    python data_import.py --docs        # documents/knowledge only
"""

from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

HERE     = Path(__file__).parent
HARNESS  = HERE.parent.parent
AGENTS   = HARNESS.parent
APP_ROOT = AGENTS.parent

for _p in (HERE, HARNESS, AGENTS, APP_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import hub_db as db

# ── Source file paths ──────────────────────────────────────────────────────────
ROSTER_MD         = AGENTS / "agents" / "roster.md"
PROFILES_MD       = AGENTS / "agents" / "agent_profiles.md"
AGENT_PROJECTS    = AGENTS / "agents" / "projects"
PROJECTS_DIR      = AGENTS / "projects"
S2T_CLIENTS_DIR   = AGENTS / "projects" / "s2tdesigns" / "clients"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _uid() -> str:
    return uuid.uuid4().hex


# ── 1. Agent Registry — parse roster.md + agent skill files ───────────────────

# Roster project definitions (hand-coded from roster.md for reliability)
ROSTER_PROJECTS = [
    {"slug": "xftc",             "name": "XFTC Website & Membership Plugin",    "status": "sprint-3",      "lead": "xftc-project-lead",          "url": "xtremeforcetrackclub.org",      "platform": "WordPress"},
    {"slug": "yepc",             "name": "YEPC — Youth Elite Performance Complex","status": "pre-dev",       "lead": "yepc-project-manager",        "url": "",                              "platform": ""},
    {"slug": "elevation",        "name": "The Elevation ATX",                    "status": "llc-pending",   "lead": "elevation-project-lead",      "url": "theElevationATX.com",           "platform": ""},
    {"slug": "pbs-foundation",   "name": "PBS Collegiate Pathways Foundation",   "status": "filing-pending","lead": "pbs-project-lead",            "url": "psibetasigma1914.org",          "platform": "WordPress"},
    {"slug": "nutrue",           "name": "Nutrue Apparel",                       "status": "pod-setup",     "lead": "nutrue-project-lead",         "url": "nutrueapparel.com",             "platform": "WordPress/Printful"},
    {"slug": "smithcap",         "name": "Smith Capital Properties",             "status": "reactivation",  "lead": "smithcap-project-lead",       "url": "smithcapitalproperties.com",    "platform": "WordPress"},
    {"slug": "s2tdesigns",       "name": "S2T Designs Agency",                   "status": "active",        "lead": "s2t-project-lead",            "url": "s2tdesigns.com",                "platform": "WordPress"},
    {"slug": "productivity",     "name": "Personal Productivity",                "status": "active",        "lead": "productivity-coordinator",    "url": "",                              "platform": ""},
    {"slug": "smithcap-finance", "name": "SmithCap Financial Management Office", "status": "active",        "lead": "finance-project-lead",        "url": "",                              "platform": ""},
    {"slug": "solar",            "name": "Clarity Solar Services",               "status": "pre-launch",    "lead": "solar-project-lead",          "url": "",                              "platform": ""},
    {"slug": "social-media",     "name": "S2T Social Media Division",            "status": "active",        "lead": "social-project-lead",         "url": "",                              "platform": ""},
    {"slug": "ministry",         "name": "Ministry & Preaching Team",            "status": "active",        "lead": "ministry-project-lead",       "url": "",                              "platform": ""},
    {"slug": "sigma-signal",     "name": "The Sigma Signal Newsletter",          "status": "active",        "lead": "sigma-signal-project-lead",   "url": "",                              "platform": "Constant Contact"},
    {"slug": "travel",           "name": "Travel Division",                      "status": "active",        "lead": "travel-project-lead",         "url": "",                              "platform": ""},
    {"slug": "holdings",         "name": "Business Structure & Holdings",        "status": "formation",     "lead": "holdings-project-lead",       "url": "",                              "platform": ""},
    {"slug": "business-law",     "name": "Business Law Division",                "status": "active",        "lead": "business-law-project-lead",   "url": "",                              "platform": ""},
    {"slug": "markets",          "name": "Markets & Investment Intelligence",    "status": "active",        "lead": "markets-project-lead",        "url": "",                              "platform": ""},
    {"slug": "nightking",        "name": "NightKing Project",                    "status": "active",        "lead": "",                            "url": "",                              "platform": ""},
]

# All agents extracted from roster.md — type: lead|specialist|helper|personal|system
ROSTER_AGENTS = [
    # XFTC
    {"agent_id": "xftc-project-lead",     "name": "XFTC Project Lead",           "type": "lead",       "project": "xftc",           "role": "Sprint planning, milestone tracking, board communications"},
    {"agent_id": "xftc-plugin-dev",       "name": "XFTC Plugin Dev",             "type": "specialist", "project": "xftc",           "role": "Senior PHP Developer — plugin architecture, REST API"},
    {"agent_id": "xftc-frontend-dev",     "name": "XFTC Frontend Dev",           "type": "specialist", "project": "xftc",           "role": "Frontend/Theme Developer — CSS/JS, portal UX, Gutenberg"},
    {"agent_id": "xftc-payments-agent",   "name": "XFTC Payments Agent",         "type": "specialist", "project": "xftc",           "role": "Payments & Billing — Stripe PHP SDK, webhooks, refunds"},
    {"agent_id": "xftc-qa-agent",         "name": "XFTC QA Agent",               "type": "specialist", "project": "xftc",           "role": "QA & Testing — staging environment, regression testing"},
    {"agent_id": "xftc-devops-agent",     "name": "XFTC DevOps Agent",           "type": "specialist", "project": "xftc",           "role": "DevOps & Deployment — GitHub, plugin packaging, staging→prod"},
    # YEPC
    {"agent_id": "yepc-project-manager",        "name": "YEPC Project Manager",        "type": "lead",       "project": "yepc",           "role": "Master milestone tracker, cross-agency coordination"},
    {"agent_id": "yepc-real-estate-agent",      "name": "YEPC Real Estate Agent",      "type": "specialist", "project": "yepc",           "role": "Land search, parcel due diligence, zoning analysis"},
    {"agent_id": "yepc-capital-fundraising-agent","name": "YEPC Capital Fundraising",  "type": "specialist", "project": "yepc",           "role": "Investor pitch decks, naming rights, sponsor outreach"},
    {"agent_id": "yepc-government-relations-agent","name": "YEPC Government Relations","type": "specialist", "project": "yepc",           "role": "Hutto EDC, Williamson County, TxDOT/CAMPO monitoring"},
    {"agent_id": "yepc-grant-writer-agent",     "name": "YEPC Grant Writer",           "type": "specialist", "project": "yepc",           "role": "EDA, HUD CDBG, USATF, FHWA TAP grant applications"},
    {"agent_id": "yepc-financial-model-agent",  "name": "YEPC Financial Model Agent",  "type": "specialist", "project": "yepc",           "role": "Phase 1-3 cost projections, ROI, 5-yr pro forma"},
    {"agent_id": "yepc-legal-agent",            "name": "YEPC Legal Agent",            "type": "specialist", "project": "yepc",           "role": "YEPC LLC formation, partnership agreements, ground lease"},
    # Elevation
    {"agent_id": "elevation-project-lead",   "name": "Elevation Project Lead",   "type": "lead",       "project": "elevation",      "role": "Brand vision, event calendar, LLC milestone, investor deck"},
    {"agent_id": "elevation-brand-agent",    "name": "Elevation Brand Agent",    "type": "specialist", "project": "elevation",      "role": "Brand identity, visual language, event themes, social creative"},
    {"agent_id": "elevation-events-agent",   "name": "Elevation Events Agent",   "type": "specialist", "project": "elevation",      "role": "Event programming, vendor sourcing, venue walkthroughs"},
    {"agent_id": "elevation-marketing-agent","name": "Elevation Marketing Agent","type": "specialist", "project": "elevation",      "role": "Growth & Marketing — waitlist funnel, TikTok/Reels, email"},
    {"agent_id": "elevation-funding-agent",  "name": "Elevation Funding Agent",  "type": "specialist", "project": "elevation",      "role": "SBA 7(a), PeopleFund/LiftFund CDFI, angel investor outreach"},
    {"agent_id": "elevation-legal-agent",    "name": "Elevation Legal Agent",    "type": "specialist", "project": "elevation",      "role": "TX LLC filing, TABC licensing, lease negotiation"},
    # PBS Foundation
    {"agent_id": "pbs-project-lead",          "name": "PBS Project Lead",          "type": "lead",       "project": "pbs-foundation", "role": "501(c)(3) milestone tracker, board governance"},
    {"agent_id": "pbs-legal-agent",           "name": "PBS Legal Agent",           "type": "specialist", "project": "pbs-foundation", "role": "TX SOS Articles of Incorporation, IRS Form 1023-EZ, EIN"},
    {"agent_id": "pbs-fundraising-agent",     "name": "PBS Fundraising Agent",     "type": "specialist", "project": "pbs-foundation", "role": "Grant research, donor outreach, annual giving strategy"},
    {"agent_id": "pbs-communications-agent",  "name": "PBS Communications Agent",  "type": "specialist", "project": "pbs-foundation", "role": "Foundation website, newsletter, social media"},
    {"agent_id": "pbs-programs-agent",        "name": "PBS Programs Agent",        "type": "specialist", "project": "pbs-foundation", "role": "Travel assistance program framework, eligibility, disbursement"},
    {"agent_id": "pbs-board-agent",           "name": "PBS Board Agent",           "type": "specialist", "project": "pbs-foundation", "role": "Board recruitment, officer structure, Robert's Rules"},
    # Nutrue
    {"agent_id": "nutrue-project-lead",     "name": "Nutrue Project Lead",     "type": "lead",       "project": "nutrue",         "role": "Brand strategy, product roadmap, LLC formation"},
    {"agent_id": "nutrue-ecommerce-agent",  "name": "Nutrue E-Commerce Agent", "type": "specialist", "project": "nutrue",         "role": "WordPress/Shopify, Printful integration, product listings"},
    {"agent_id": "nutrue-brand-agent",      "name": "Nutrue Brand Agent",      "type": "specialist", "project": "nutrue",         "role": "Visual identity, collection concepts, lookbook creation"},
    {"agent_id": "nutrue-marketing-agent",  "name": "Nutrue Marketing Agent",  "type": "specialist", "project": "nutrue",         "role": "TikTok/Instagram, influencer outreach, email list, SEO"},
    {"agent_id": "nutrue-legal-agent",      "name": "Nutrue Legal Agent",      "type": "specialist", "project": "nutrue",         "role": "LLC registration, trademark, supplier contracts"},
    {"agent_id": "nutrue-finance-agent",    "name": "Nutrue Finance Agent",    "type": "specialist", "project": "nutrue",         "role": "Monthly P&L, COGS/margin analysis, tax prep"},
    # SmithCap
    {"agent_id": "smithcap-project-lead",          "name": "SmithCap Project Lead",          "type": "lead",       "project": "smithcap",       "role": "Portfolio oversight, deal pipeline, entity compliance"},
    {"agent_id": "smithcap-acquisitions-agent",    "name": "SmithCap Acquisitions Agent",    "type": "specialist", "project": "smithcap",       "role": "Property sourcing, LOI drafting, due diligence"},
    {"agent_id": "smithcap-communications-agent",  "name": "SmithCap Communications Agent",  "type": "specialist", "project": "smithcap",       "role": "Investor updates, partner comms, brand presence"},
    {"agent_id": "smithcap-finance-agent",         "name": "SmithCap Finance Agent",         "type": "specialist", "project": "smithcap",       "role": "Capital stack analysis, debt/equity modeling, lenders"},
    {"agent_id": "smithcap-legal-agent",           "name": "SmithCap Legal Agent",           "type": "specialist", "project": "smithcap",       "role": "Entity maintenance, contract review, TX SOS filings"},
    # S2T Designs
    {"agent_id": "s2t-project-lead",          "name": "S2T Project Lead",          "type": "lead",       "project": "s2tdesigns",     "role": "Client intake, project scoping, deliverable oversight"},
    {"agent_id": "s2t-webdev-agent",          "name": "S2T Web Dev Agent",         "type": "specialist", "project": "s2tdesigns",     "role": "WordPress builds, theme customization, DNS/hosting"},
    {"agent_id": "s2t-brand-designer-agent",  "name": "S2T Brand Designer",        "type": "specialist", "project": "s2tdesigns",     "role": "Logo, color palette, typography, brand guides, mockups"},
    {"agent_id": "s2t-seo-agent",             "name": "S2T SEO Agent",             "type": "specialist", "project": "s2tdesigns",     "role": "On-page SEO, Google Business Profile, local search"},
    {"agent_id": "s2t-maintenance-agent",     "name": "S2T Maintenance Agent",     "type": "specialist", "project": "s2tdesigns",     "role": "Plugin updates, backups, uptime monitoring, security"},
    {"agent_id": "s2t-comms-agent",           "name": "S2T Comms Agent",           "type": "specialist", "project": "s2tdesigns",     "role": "Onboarding emails, status updates, invoicing, discovery"},
    # Finance/FMO
    {"agent_id": "finance-project-lead",     "name": "Finance Project Lead (CFO)",  "type": "lead",       "project": "smithcap-finance","role": "Cross-entity financial oversight, tax strategy, capital allocation"},
    {"agent_id": "finance-cpa",              "name": "Finance CPA",                 "type": "specialist", "project": "smithcap-finance","role": "Tax filings, quarterly estimates, entity returns"},
    {"agent_id": "finance-advisor",          "name": "Finance Advisor",             "type": "specialist", "project": "smithcap-finance","role": "Investment planning, retirement strategy, wealth building"},
    {"agent_id": "finance-investment-manager","name": "Finance Investment Manager",  "type": "specialist", "project": "smithcap-finance","role": "RSU tracking, 401(k) optimization, brokerage strategy"},
    {"agent_id": "finance-bookkeeper",       "name": "Finance Bookkeeper",          "type": "specialist", "project": "smithcap-finance","role": "Transaction categorization, monthly reconciliation"},
    {"agent_id": "finance-tax-strategist",   "name": "Finance Tax Strategist",      "type": "specialist", "project": "smithcap-finance","role": "Cross-entity tax planning, deduction strategy"},
    {"agent_id": "finance-analyst",          "name": "Finance Analyst",             "type": "specialist", "project": "smithcap-finance","role": "KPI dashboards, pro forma modeling, variance analysis"},
    {"agent_id": "finance-compliance",       "name": "Finance Compliance Officer",  "type": "specialist", "project": "smithcap-finance","role": "Entity filings, franchise tax, annual reports"},
    # Solar
    {"agent_id": "solar-project-lead",    "name": "Solar Project Lead",    "type": "lead",       "project": "solar",          "role": "Business formation, licensing, client acquisition"},
    # Social Media
    {"agent_id": "social-project-lead",   "name": "Social Media Project Lead", "type": "lead",    "project": "social-media",   "role": "Cross-client social media strategy and execution"},
    # Ministry
    {"agent_id": "ministry-project-lead", "name": "Ministry Project Lead", "type": "lead",       "project": "ministry",       "role": "Ministry & preaching team coordination"},
    # Sigma Signal
    {"agent_id": "sigma-signal-project-lead","name": "Sigma Signal Project Lead","type": "lead",  "project": "sigma-signal",   "role": "Newsletter coordination, content, Constant Contact"},
    # Travel
    {"agent_id": "travel-project-lead",   "name": "Travel Project Lead",   "type": "lead",       "project": "travel",         "role": "Travel research, fare alerts, trip planning"},
    # Holdings
    {"agent_id": "holdings-project-lead", "name": "Holdings Project Lead", "type": "lead",       "project": "holdings",       "role": "Business structure, LLC formation, holding company"},
    {"agent_id": "holdings-legal-agent",  "name": "Holdings Legal Agent",  "type": "specialist", "project": "holdings",       "role": "Entity formation, operating agreements, compliance"},
    {"agent_id": "holdings-finance-agent","name": "Holdings Finance Agent","type": "specialist",  "project": "holdings",       "role": "Capital allocation, inter-entity transfers"},
    {"agent_id": "holdings-tax-agent",    "name": "Holdings Tax Agent",    "type": "specialist",  "project": "holdings",       "role": "Pass-through taxation, cross-entity tax strategy"},
    {"agent_id": "holdings-compliance-agent","name": "Holdings Compliance Agent","type": "specialist","project": "holdings",   "role": "TX SOS filings, registered agent, annual reports"},
    {"agent_id": "holdings-investor-agent","name": "Holdings Investor Agent","type": "specialist", "project": "holdings",      "role": "Investor relations, capital raise, term sheets"},
    # Business Law
    {"agent_id": "business-law-project-lead",    "name": "Business Law Project Lead",    "type": "lead",       "project": "business-law",   "role": "Legal oversight across all entities"},
    {"agent_id": "business-law-entity-agent",    "name": "Business Law Entity Agent",    "type": "specialist", "project": "business-law",   "role": "LLC/Corp formation, operating agreements"},
    {"agent_id": "business-law-contracts-agent", "name": "Business Law Contracts Agent", "type": "specialist", "project": "business-law",   "role": "Contract drafting, review, negotiation"},
    {"agent_id": "business-law-realestate-agent","name": "Business Law RE Agent",        "type": "specialist", "project": "business-law",   "role": "Real estate contracts, title, closing docs"},
    {"agent_id": "business-law-employment-agent","name": "Business Law Employment Agent","type": "specialist", "project": "business-law",   "role": "Employment agreements, HR compliance"},
    {"agent_id": "business-law-ip-agent",        "name": "Business Law IP Agent",        "type": "specialist", "project": "business-law",   "role": "Trademark, copyright, IP protection"},
    {"agent_id": "business-law-regulatory-agent","name": "Business Law Regulatory Agent","type": "specialist", "project": "business-law",   "role": "Licensing, permits, regulatory compliance"},
    # Markets
    {"agent_id": "markets-project-lead",       "name": "Markets Project Lead",       "type": "lead",       "project": "markets",        "role": "Investment intelligence coordination"},
    {"agent_id": "markets-cio",                "name": "Markets CIO",                "type": "specialist", "project": "markets",        "role": "Chief Investment Officer — portfolio strategy"},
    {"agent_id": "markets-equity-analyst",     "name": "Markets Equity Analyst",     "type": "specialist", "project": "markets",        "role": "Equity research, stock analysis, valuations"},
    {"agent_id": "markets-macro-analyst",      "name": "Markets Macro Analyst",      "type": "specialist", "project": "markets",        "role": "Macro economics, Fed policy, rates analysis"},
    {"agent_id": "markets-options-strategist", "name": "Markets Options Strategist", "type": "specialist", "project": "markets",        "role": "Options strategies, hedging, derivatives"},
    {"agent_id": "markets-quant",              "name": "Markets Quant",              "type": "specialist", "project": "markets",        "role": "Quantitative analysis, backtesting, algorithms"},
    {"agent_id": "markets-intelligence-desk",  "name": "Markets Intelligence Desk",  "type": "specialist", "project": "markets",        "role": "Market intelligence, news analysis, sector monitoring"},
    {"agent_id": "markets-cro",                "name": "Markets CRO",                "type": "specialist", "project": "markets",        "role": "Risk management, portfolio risk assessment"},
    {"agent_id": "markets-tactical-alpha",     "name": "Markets Tactical Alpha",     "type": "specialist", "project": "markets",        "role": "Short-term trade opportunities, momentum plays"},
    # Personal / Email
    {"agent_id": "productivity-coordinator",  "name": "Productivity Coordinator",  "type": "lead",       "project": "productivity",   "role": "Daily email digest, inbox triage, task routing"},
    {"agent_id": "allensmithagent",           "name": "Allen Smith Email Agent",   "type": "personal",   "project": "productivity",   "role": "Personal Outlook email management — Allen Smith"},
    {"agent_id": "smithdaiiagent",            "name": "Smith DA II Email Agent",   "type": "personal",   "project": "productivity",   "role": "Personal Gmail daily use — inbox triage"},
    {"agent_id": "communicationsdirgcr",      "name": "Communications Dir GCR",   "type": "personal",   "project": "productivity",   "role": "Org communications — GCR announcements"},
    {"agent_id": "thesigmasignal",            "name": "The Sigma Signal Agent",    "type": "personal",   "project": "sigma-signal",   "role": "Newsletter coordination — The Sigma Signal"},
    {"agent_id": "psibetasigma1914",          "name": "PBS 1914 Email Agent",      "type": "personal",   "project": "pbs-foundation", "role": "Chapter communications — Psi Beta Sigma 1914"},
    {"agent_id": "xtremeforcetrackclub",      "name": "XFTC Email Agent",          "type": "personal",   "project": "xftc",           "role": "Member comms, registration, event info — XFTC"},
    # System
    {"agent_id": "inez-chief-of-staff",       "name": "Inez — Chief of Staff",     "type": "system",     "project": "",               "role": "Portfolio orchestrator — routes tasks, manages all agents"},
    {"agent_id": "wordpressagent",            "name": "WordPress Agent",           "type": "specialist", "project": "s2tdesigns",     "role": "WordPress development — fixes, themes, plugins"},
    {"agent_id": "grant_writer_agent",        "name": "Grant Writer Agent",        "type": "specialist", "project": "pbs-foundation", "role": "Grant writing and research across projects"},
    {"agent_id": "web_dev_researcher",        "name": "Web Dev Researcher",        "type": "specialist", "project": "s2tdesigns",     "role": "Research for web development solutions and trends"},
]

# Active automations from roster.md (Project 8 — Personal Productivity)
AUTOMATIONS = [
    {
        "slug": "daily-email-digest",
        "name": "Daily Email Digest",
        "description": "Aggregate and summarize all email accounts into a morning digest",
        "project_slug": "productivity",
        "agent_id": "productivity-coordinator",
        "trigger_type": "cron",
        "trigger_config": {"cron": "0 8 * * *", "timezone": "America/Chicago"},
        "status": "active",
    },
    {
        "slug": "xftc-athlete-signup-logger",
        "name": "XFTC Athlete Signup & Payment Logger",
        "description": "Real-time logging of athlete signups and payments from Gmail connector",
        "project_slug": "xftc",
        "agent_id": "xftc-payments-agent",
        "trigger_type": "event",
        "trigger_config": {"event": "gmail.message", "filter": "xtremeforcetrackclub.org"},
        "status": "paused",
    },
    {
        "slug": "weekly-grant-digest",
        "name": "Weekly Monday Grant Digest",
        "description": "Weekly sweep of new grant opportunities across all projects",
        "project_slug": "yepc",
        "agent_id": "grant_writer_agent",
        "trigger_type": "cron",
        "trigger_config": {"cron": "0 8 * * 1", "timezone": "America/Chicago"},
        "status": "active",
    },
    {
        "slug": "sigma-signal-submission-check",
        "name": "Sigma Signal Daily Submission Check",
        "description": "Check for new newsletter submissions and format for review",
        "project_slug": "sigma-signal",
        "agent_id": "sigma-signal-project-lead",
        "trigger_type": "cron",
        "trigger_config": {"cron": "0 14 * * *", "timezone": "America/Chicago"},
        "status": "active",
    },
    {
        "slug": "weekly-travel-fare-alert",
        "name": "Weekly Travel Fare Alert",
        "description": "Monitor travel fares and alert on deals for planned trips",
        "project_slug": "travel",
        "agent_id": "travel-project-lead",
        "trigger_type": "cron",
        "trigger_config": {"cron": "30 8 * * 1", "timezone": "America/Chicago"},
        "status": "active",
    },
    {
        "slug": "markets-daily-premarket-brief",
        "name": "Markets Daily Pre-Market Brief",
        "description": "Weekday pre-market intelligence: futures, key levels, catalysts, macro watch.",
        "project_slug": "markets",
        "agent_id": "markets-project-lead",
        "trigger_type": "schedule",
        "trigger_config": {"cron": "30 8 * * 1-5", "timezone": "America/Chicago", "description": "Weekdays 8:30am CT"},
        "steps": [
            "markets-macro-analyst: pull overnight futures, pre-market movers, key economic releases today",
            "markets-project-lead: synthesize into pre-market brief with levels and action items",
            "save report to reports table as type=daily",
        ],
        "status": "active",
    },
    {
        "slug": "markets-weekly-picks-digest",
        "name": "Markets Weekly Picks Digest",
        "description": "Monday morning: top 3-5 actionable stock/options ideas with entry/exit criteria.",
        "project_slug": "markets",
        "agent_id": "markets-project-lead",
        "trigger_type": "schedule",
        "trigger_config": {"cron": "0 7 * * 1", "timezone": "America/Chicago", "description": "Mondays 7:00am CT"},
        "steps": [
            "markets-equity-analyst: screen for top 3-5 equity setups",
            "markets-options-strategist: identify income-generating options trades",
            "markets-macro-analyst: macro backdrop and sector rotation",
            "markets-project-lead: compile Weekly Picks Digest",
        ],
        "status": "active",
    },
    {
        "slug": "markets-monthly-portfolio-review",
        "name": "Markets Monthly Portfolio Review",
        "description": "First Monday of month: full P&L review, position assessment, strategy adjustment.",
        "project_slug": "markets",
        "agent_id": "markets-project-lead",
        "trigger_type": "schedule",
        "trigger_config": {"cron": "0 9 1-7 * 1", "timezone": "America/Chicago", "description": "First Monday of each month 9:00am CT"},
        "steps": [
            "markets-equity-analyst: review all open positions",
            "markets-options-strategist: review all options positions",
            "markets-cio: P&L summary and risk metrics",
            "markets-project-lead: Monthly Portfolio Review report",
        ],
        "status": "active",
    },
]

# Client registry
CLIENTS = [
    {
        "slug": "xftc-client",
        "name": "Xtreme Force Track Club",
        "business_type": "Nonprofit Sports Organization",
        "service": "WordPress custom plugin + theme, payments",
        "contact_name": "David Smith",
        "contact_email": "dsmith@xtremeforcetrackclub.org",
        "contact_role": "Owner/Operator",
        "engagement": "project",
        "status": "active",
        "project_slug": "xftc",
        "website": "xtremeforcetrackclub.org",
        "notes": "Sprint 3 — Dashboard widgets, Coach portal, Stripe live key integration. Blocker: Stripe API keys.",
    },
    {
        "slug": "pbs-1914-client",
        "name": "Psi Beta Sigma 1914",
        "business_type": "Fraternal Organization / Nonprofit",
        "service": "WordPress site (Kadence), PBS event commerce plugin, payment gateway OAuth",
        "contact_name": "David Smith",
        "contact_email": "psibetasigma1914@gmail.com",
        "contact_role": "Webmaster",
        "engagement": "retainer",
        "status": "active",
        "project_slug": "pbs-foundation",
        "website": "psibetasigma1914.org",
        "notes": "Pre-launch. Needs WordPress App Password for s2tdesignadmin to deploy CSS changes. Payment gateway OAuth implementation complete.",
    },
    {
        "slug": "lebc-client",
        "name": "Little Ebenezer Baptist Church",
        "business_type": "Religious Organization",
        "service": "WordPress rebuild (Kadence), brand refresh, social media",
        "contact_name": "Rev. Arthur L. Spence",
        "contact_email": "",
        "contact_role": "Pastor",
        "engagement": "project",
        "status": "discovery",
        "project_slug": "s2tdesigns",
        "website": "littleebenezerbaptistchurch.com",
        "notes": "Discovery phase. Current site D+ — 2 of 3 nav pages broken. Pending: discovery meeting with Pastor Spence, photography, online giving decision.",
    },
    {
        "slug": "nutrue-client",
        "name": "Nutrue Apparel",
        "business_type": "E-Commerce / Apparel Brand",
        "service": "WordPress/Printful store, brand identity, digital marketing",
        "contact_name": "David Smith",
        "contact_email": "",
        "contact_role": "Founder",
        "engagement": "retainer",
        "status": "active",
        "project_slug": "nutrue",
        "website": "nutrueapparel.com",
        "notes": "POD setup phase. Namecheap/Bosnacweb hosting — .htaccess fix required.",
    },
    {
        "slug": "smithcap-properties-client",
        "name": "Smith Capital Properties LLC",
        "business_type": "Real Estate Investment",
        "service": "Entity reactivation, portfolio management, website",
        "contact_name": "David Smith",
        "contact_email": "david.smith@smithcapitalproperties.com",
        "contact_role": "Principal",
        "engagement": "retainer",
        "status": "inactive",
        "project_slug": "smithcap",
        "website": "smithcapitalproperties.com",
        "notes": "BLOCKER: LLC INACTIVE — missed TX franchise tax/PIR filings. Steps: file past-due reports → pay penalties → Form 811 ($75) → Certificate of Good Standing.",
    },
]


def _conn():
    import sqlite3
    from hub_db import DB_PATH, get_conn
    return get_conn()


def import_projects() -> int:
    """Seed all 17 projects from roster."""
    count = 0
    now = _now()
    with _conn() as conn:
        for p in ROSTER_PROJECTS:
            existing = conn.execute("SELECT id FROM projects WHERE slug = ?", (p["slug"],)).fetchone()
            if existing:
                conn.execute(
                    """UPDATE projects SET name=?, status=?, lead_agent=?, url=?, platform=?, updated_at=?
                       WHERE slug=?""",
                    (p["name"], p["status"], p["lead"], p.get("url",""), p.get("platform",""), now, p["slug"]),
                )
            else:
                conn.execute(
                    """INSERT INTO projects (id,slug,name,description,status,lead_agent,url,platform,tags,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?,?,'[]',?,?)""",
                    (_uid(), p["slug"], p["name"], "", p["status"], p["lead"],
                     p.get("url",""), p.get("platform",""), now, now),
                )
                count += 1
    return count


def import_agents() -> int:
    """Seed all agents from roster into agent_registry."""
    count = 0
    now = _now()
    with _conn() as conn:
        for a in ROSTER_AGENTS:
            # Try to load system_prompt from skill file
            system_prompt = _load_agent_skill_file(a["agent_id"])
            existing = conn.execute(
                "SELECT id FROM agent_registry WHERE agent_id = ?", (a["agent_id"],)
            ).fetchone()
            if existing:
                conn.execute(
                    """UPDATE agent_registry SET name=?,type=?,role=?,project_slug=?,
                       system_prompt=?,updated_at=? WHERE agent_id=?""",
                    (a["name"], a["type"], a["role"], a.get("project",""),
                     system_prompt or "", now, a["agent_id"]),
                )
            else:
                conn.execute(
                    """INSERT INTO agent_registry
                       (id,agent_id,name,type,role,description,project_slug,
                        capabilities,integrations,status,system_prompt,config,metadata,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (_uid(), a["agent_id"], a["name"], a["type"], a["role"],
                     a.get("description",""), a.get("project",""),
                     "[]", "[]", "active", system_prompt or "",
                     "{}", "{}", now, now),
                )
                count += 1
    return count


def _load_agent_skill_file(agent_id: str) -> str:
    """Try to find and read the skill markdown file for an agent."""
    # Search pattern: agents/projects/<project>/<agent_id>.md
    for path in AGENT_PROJECTS.rglob(f"{agent_id}.md"):
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            pass
    # Also check root agents dir
    for path in (AGENTS / "agents").rglob(f"{agent_id}.md"):
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            pass
    return ""


def import_automations() -> int:
    """Seed all defined automations."""
    count = 0
    now = _now()
    with _conn() as conn:
        for a in AUTOMATIONS:
            existing = conn.execute("SELECT id FROM automations WHERE slug = ?", (a["slug"],)).fetchone()
            if existing:
                conn.execute(
                    """UPDATE automations SET name=?,status=?,updated_at=? WHERE slug=?""",
                    (a["name"], a["status"], now, a["slug"]),
                )
            else:
                conn.execute(
                    """INSERT INTO automations
                       (id,slug,name,description,project_slug,agent_id,trigger_type,
                        trigger_config,steps,status,run_count,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,0,?,?)""",
                    (_uid(), a["slug"], a["name"], a.get("description",""),
                     a.get("project_slug",""), a.get("agent_id",""),
                     a.get("trigger_type","manual"),
                     json.dumps(a.get("trigger_config",{})),
                     "[]", a.get("status","active"), now, now),
                )
                count += 1
    return count


def import_clients() -> int:
    """Seed client records."""
    count = 0
    now = _now()
    with _conn() as conn:
        for c in CLIENTS:
            existing = conn.execute("SELECT id FROM clients WHERE slug = ?", (c["slug"],)).fetchone()
            if existing:
                conn.execute(
                    """UPDATE clients SET name=?,business_type=?,service=?,contact_name=?,
                       contact_email=?,contact_role=?,engagement=?,status=?,project_slug=?,
                       website=?,notes=?,updated_at=? WHERE slug=?""",
                    (c["name"], c.get("business_type",""), c.get("service",""),
                     c.get("contact_name",""), c.get("contact_email",""),
                     c.get("contact_role",""), c.get("engagement","retainer"),
                     c.get("status","active"), c.get("project_slug",""),
                     c.get("website",""), c.get("notes",""), now, c["slug"]),
                )
            else:
                conn.execute(
                    """INSERT INTO clients
                       (id,slug,name,business_type,service,contact_name,contact_email,
                        contact_role,engagement,status,project_slug,website,notes,
                        tags,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'[]',?,?)""",
                    (_uid(), c["slug"], c["name"], c.get("business_type",""),
                     c.get("service",""), c.get("contact_name",""),
                     c.get("contact_email",""), c.get("contact_role",""),
                     c.get("engagement","retainer"), c.get("status","active"),
                     c.get("project_slug",""), c.get("website",""),
                     c.get("notes",""), now, now),
                )
                count += 1
    return count


def import_knowledge_from_files() -> int:
    """Scan all project folders for markdown files and import into knowledge_base."""
    count = 0
    now = _now()

    def _upsert_kb(title: str, content: str, source: str, category: str, project_slug: str, agent_id: str = "") -> None:
        nonlocal count
        if not content.strip():
            return
        with _conn() as conn:
            existing = conn.execute(
                "SELECT id FROM knowledge_base WHERE source = ? AND category = ?",
                (source, category)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE knowledge_base SET title=?,content=?,updated_at=? WHERE id=?",
                    (title, content, now, existing["id"]),
                )
            else:
                conn.execute(
                    """INSERT INTO knowledge_base
                       (id,title,content,source,source_type,category,tags,
                        project_slug,agent_id,is_active,created_at,updated_at)
                       VALUES (?,?,?,?,'file','project','[]',?,?,1,?,?)""",
                    (_uid(), title, content, source, project_slug, agent_id, now, now),
                )
                count += 1

    # Import agent skill files as knowledge
    for md_file in AGENT_PROJECTS.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            project_slug = md_file.parent.name
            agent_id = md_file.stem
            title = f"Agent Skill: {agent_id}"
            _upsert_kb(title, content, str(md_file.relative_to(AGENTS)), "agent", project_slug, agent_id)
        except Exception:
            pass

    # Import root agent markdown files
    for md_file in (AGENTS / "agents").glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            title = md_file.stem.replace("-", " ").replace("_", " ").title()
            _upsert_kb(title, content, str(md_file.relative_to(AGENTS)), "agent", "")
        except Exception:
            pass

    # Import project folder markdown files
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir() or project_dir.name.startswith("."):
            continue
        project_slug = project_dir.name
        for md_file in project_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                filename = md_file.stem.upper()
                title = f"{project_slug.upper()} — {filename}"
                cat = _categorize_doc(md_file.stem)
                _upsert_kb(title, content, str(md_file.relative_to(AGENTS)), cat, project_slug)
            except Exception:
                pass

    return count


def _categorize_doc(stem: str) -> str:
    stem_l = stem.lower()
    if "brand" in stem_l:         return "brand"
    if "project" in stem_l:       return "project"
    if "client" in stem_l or "roster" in stem_l: return "client"
    if "intake" in stem_l or "proposal" in stem_l or "discovery" in stem_l: return "proposal"
    if "sprint" in stem_l:        return "sprint"
    if "workflow" in stem_l or "platform" in stem_l or "guide" in stem_l: return "process"
    return "reference"


def import_documents_from_files() -> int:
    """Import key structured markdown files into the documents table."""
    count = 0
    now = _now()

    def _upsert_doc(title: str, content: str, doc_type: str, project_slug: str, client_id: str = "") -> None:
        nonlocal count
        if not content.strip():
            return
        with _conn() as conn:
            existing = conn.execute(
                "SELECT id FROM documents WHERE title = ? AND project_slug = ?",
                (title, project_slug)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE documents SET content=?,updated_at=? WHERE id=?",
                    (content, now, existing["id"]),
                )
            else:
                conn.execute(
                    """INSERT INTO documents
                       (id,title,doc_type,content,format,project_slug,client_id,
                        tags,version,status,created_by,created_at,updated_at)
                       VALUES (?,?,?,?,'markdown',?,?,'[]',1,'active','import',?,?)""",
                    (_uid(), title, doc_type, content, project_slug, client_id, now, now),
                )
                count += 1

    doc_type_map = {
        "PROJECT": "plan",
        "BRAND-GUIDE": "brand-guide",
        "INTAKE": "intake",
        "PROPOSAL": "proposal",
        "DISCOVERY-PREP": "intake",
        "WORKFLOW": "process",
        "SERVICES": "reference",
        "CLIENT-ROSTER": "client",
        "PLATFORM-GUIDE": "process",
        "CLIENT-INTAKE-SYSTEM": "process",
        "SPRINT-1": "sprint",
        "SPRINT-2": "sprint",
        "SPRINT-3": "sprint",
        "MEDIA-CAMPAIGN-PLAN": "plan",
    }

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir() or project_dir.name.startswith("."):
            continue
        slug = project_dir.name
        for md_file in project_dir.rglob("*.md"):
            stem = md_file.stem.upper()
            if stem not in doc_type_map:
                continue
            try:
                content = md_file.read_text(encoding="utf-8")
                title = f"{slug.upper()} — {stem}"
                _upsert_doc(title, content, doc_type_map[stem], slug)
                count += 1
            except Exception:
                pass

    # Import the main roster and profiles
    for md_file in [ROSTER_MD, PROFILES_MD]:
        try:
            if md_file.exists():
                content = md_file.read_text(encoding="utf-8")
                _upsert_doc(md_file.stem.replace("-", " ").title(), content, "reference", "")
        except Exception:
            pass

    return count


def import_trips_from_files() -> int:
    """
    Scan .agents/projects/travel/trips/*.md and seed travel_trips table.
    Parses: trip name, destination, depart/return dates, status, budget, notes.
    Idempotent — skips existing trips by name.
    """
    trips_dir = PROJECTS_DIR / "travel" / "trips"
    if not trips_dir.exists():
        return 0

    # Map markdown status emoji → DB status
    status_map = {
        "researching": "planning",
        "planning":    "planning",
        "booked":      "booked",
        "confirmed":   "booked",
        "in progress": "in_progress",
        "in_progress": "in_progress",
        "active":      "in_progress",
        "complete":    "complete",
        "completed":   "complete",
        "done":        "complete",
        "cancelled":   "cancelled",
    }

    def _parse_date(raw: str) -> str:
        """Try to parse partial dates like 'June 2, 2026' or '2026-06-02'."""
        raw = raw.strip().strip("*").rstrip(")")
        for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%B %d %Y"):
            try:
                return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass
        return raw

    def _parse_trip_file(path: Path) -> dict | None:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            return None

        data: dict[str, Any] = {
            "name":        "",
            "destination": "",
            "depart_date": "",
            "return_date": "",
            "status":      "planning",
            "budget":      0.0,
            "notes":       "",
        }

        # --- Name: first H1 line ---
        m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        if m:
            name = m.group(1).strip()
            # "Trip Brief — Austin (AUS) → Atlanta (ATL)" → clean it
            name = re.sub(r"Trip Brief\s*[—–-]\s*", "", name).strip()
            data["name"] = name or path.stem

        # --- Destination: extract arrow-separated cities or "Destination:" field ---
        dest_m = re.search(r"→\s*(.+?)(?:\s*\(|$)", data["name"])
        if dest_m:
            data["destination"] = dest_m.group(1).strip()

        # Fallback: look for "Destination:" line
        dest_line = re.search(r"\*\*Destination\*\*[:\s]+(.+)", text)
        if dest_line:
            data["destination"] = dest_line.group(1).strip()

        # --- Dates: "**Dates:** June 2–7, 2026 (5 nights)" ---
        date_line = re.search(r"\*\*Dates[:\*]+\s*(.+)", text)
        if date_line:
            raw = date_line.group(1)
            # Range like "June 2–7, 2026"
            range_m = re.search(r"([A-Za-z]+ \d+)[–—-](\d+),\s*(\d{4})", raw)
            if range_m:
                month_day1 = range_m.group(1)
                day2 = range_m.group(2)
                year = range_m.group(3)
                depart_str = f"{month_day1}, {year}"
                # Extract month name
                month_m = re.match(r"([A-Za-z]+)", month_day1)
                month_name = month_m.group(1) if month_m else ""
                return_str = f"{month_name} {day2}, {year}"
                data["depart_date"] = _parse_date(depart_str)
                data["return_date"] = _parse_date(return_str)
            else:
                # Two explicit dates "Jun 2 → Jun 7, 2026"
                two_m = re.search(r"([A-Za-z]+ \d+,?\s*\d{4})[^A-Za-z0-9]+([A-Za-z]+ \d+,?\s*\d{4})", raw)
                if two_m:
                    data["depart_date"] = _parse_date(two_m.group(1))
                    data["return_date"] = _parse_date(two_m.group(2))

        # --- Status ---
        status_line = re.search(r"\*\*Status[:\*]+\s*(.+)", text)
        if status_line:
            raw_status = re.sub(r"[🟡🟢🔴⬜✅🔵🟠]", "", status_line.group(1)).strip().lower()
            data["status"] = status_map.get(raw_status, "planning")

        # --- Budget: look for TOTAL row in budget table ---
        # "| **TOTAL** | **$1,304** | **$1,669** | **$1,913** |"
        budget_m = re.search(r"\*\*TOTAL\*\*[^|]*\|[^|]*\|\s*\*?\*?\$?([\d,]+)", text)
        if budget_m:
            try:
                data["budget"] = float(budget_m.group(1).replace(",", ""))
            except ValueError:
                pass

        # Fallback: "**Budget:** $X,XXX" line
        bline = re.search(r"\*\*Budget[:\*]+\s*\$?([\d,]+)", text)
        if bline and not data["budget"]:
            try:
                data["budget"] = float(bline.group(1).replace(",", ""))
            except ValueError:
                pass

        # --- Notes: use the PURPOSE line or first paragraph after H1 ---
        purpose_m = re.search(r"\*\*Purpose[:\*]+\s*(.+)", text)
        if purpose_m:
            data["notes"] = purpose_m.group(1).strip()

        # If name is still empty, use file stem
        if not data["name"]:
            data["name"] = path.stem

        return data

    count = 0
    with db.get_conn() as conn:
        for md_file in sorted(trips_dir.glob("*.md")):
            trip = _parse_trip_file(md_file)
            if not trip or not trip["name"]:
                continue
            existing = conn.execute(
                "SELECT id FROM travel_trips WHERE name = ?", (trip["name"],)
            ).fetchone()
            if existing:
                # Update in case fields changed
                conn.execute(
                    """UPDATE travel_trips
                       SET destination=?, depart_date=?, return_date=?,
                           status=?, budget=?, notes=?, updated_at=?
                       WHERE id=?""",
                    (trip["destination"], trip["depart_date"], trip["return_date"],
                     trip["status"], trip["budget"], trip["notes"],
                     _now(), existing["id"]),
                )
            else:
                conn.execute(
                    """INSERT INTO travel_trips
                       (id, name, destination, depart_date, return_date,
                        status, budget, spent, notes, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?,0,?,?,?)""",
                    (_uid(), trip["name"], trip["destination"],
                     trip["depart_date"], trip["return_date"], trip["status"],
                     trip["budget"], trip["notes"], _now(), _now()),
                )
                count += 1
    return count


def import_todos_from_files() -> int:
    """
    Parse all PROJECT.md, SPRINT-*.md, and checklist files for unchecked
    `- [ ]` tasks and seed them into the todos table.
    Completed `- [x]` tasks are skipped (they're already done).
    """
    count = 0
    now = _now()

    # Map directory names to project slugs (overrides where dir name differs)
    dir_to_slug = {
        "xftc-redevelopment":        "xftc",
        "xftc-plugin-product":       "xftc",
        "wordpress-membership-plugin":"xftc",
        "rowdy-crown":               "elevation",
        "pbs-foundation":            "pbs-foundation",
        "smithcap":                  "smithcap",
        "smithcap-finance":          "smithcap-finance",
        "s2tdesigns":                "s2tdesigns",
        "sigma-signal":              "sigma-signal",
        "social-media":              "social-media",
        "solar-repair":              "solar",
        "yepc":                      "yepc",
        "travel":                    "travel",
        "holdings":                  "holdings",
        "business-law":              "business-law",
        "markets":                   "markets",
        "ministry":                  "ministry",
        "nightking":                 "nightking",
        "grants":                    "yepc",
        "agentharness":              "",
        "local-dev-setup":           "",
    }

    # Priority keywords in section headers
    def _priority_from_header(header: str) -> str:
        h = header.lower()
        if any(w in h for w in ("urgent", "immediate", "blocker", "critical", "asap")):
            return "urgent"
        if any(w in h for w in ("phase 1", "sprint 3", "current", "next", "high")):
            return "high"
        if any(w in h for w in ("phase 2", "sprint", "backlog", "medium")):
            return "medium"
        return "low"

    def _extract_tasks(text: str, project_slug: str, file_label: str) -> list[dict]:
        """Extract unchecked tasks from markdown text."""
        tasks = []
        current_section = ""
        current_h2 = ""
        lines = text.splitlines()
        for line in lines:
            # Track section headers
            h_match = re.match(r"^(#{1,4})\s+(.+)$", line)
            if h_match:
                level = len(h_match.group(1))
                header_text = h_match.group(2).strip()
                if level <= 2:
                    current_h2 = header_text
                    current_section = header_text
                else:
                    current_section = f"{current_h2} › {header_text}"
                continue

            # Match unchecked tasks only
            task_match = re.match(r"^\s*-\s+\[ \]\s+(.+)$", line)
            if not task_match:
                continue

            title = task_match.group(1).strip()
            # Strip markdown formatting
            title = re.sub(r"`([^`]+)`", r"\1", title)
            title = re.sub(r"\*\*([^*]+)\*\*", r"\1", title)
            title = title[:200]

            if not title:
                continue

            priority = _priority_from_header(current_section)
            tasks.append({
                "title": title,
                "description": f"From: {file_label} › {current_section}",
                "priority": priority,
                "project": project_slug,
                "source": "import",
            })
        return tasks

    def _upsert_todo(title: str, description: str, priority: str, project: str) -> bool:
        nonlocal count
        with _conn() as conn:
            # Avoid duplicates by title+project
            existing = conn.execute(
                "SELECT id FROM todos WHERE title = ? AND project = ?",
                (title, project)
            ).fetchone()
            if existing:
                return False
            conn.execute(
                """INSERT INTO todos
                   (id, title, description, priority, status, project,
                    due_date, tags, source, created_at, updated_at)
                   VALUES (?,?,?,?,'pending',?,'','[]',?,?,?)""",
                (_uid(), title, description, priority, project, "import", now, now),
            )
            count += 1
            return True

    # Files to scan (in priority order)
    scan_patterns = [
        ("PROJECT.md", "project"),
        ("SPRINT-3.md", "sprint"),
        ("SPRINT-2.md", "sprint"),
        ("SPRINT-1.md", "sprint"),
        ("*CHECKLIST*.md", "checklist"),
        ("*BACKLOG*.md", "backlog"),
        ("*ROADMAP*.md", "roadmap"),
    ]

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir() or project_dir.name.startswith("."):
            continue
        dir_name = project_dir.name
        project_slug = dir_to_slug.get(dir_name, dir_name)
        if not project_slug:
            continue

        # Scan matching files
        scanned: set[Path] = set()
        for pattern, label in scan_patterns:
            for md_file in project_dir.rglob(pattern):
                if md_file in scanned:
                    continue
                scanned.add(md_file)
                try:
                    content = md_file.read_text(encoding="utf-8")
                    file_label = f"{dir_name}/{md_file.name}"
                    tasks = _extract_tasks(content, project_slug, file_label)
                    for t in tasks:
                        _upsert_todo(t["title"], t["description"], t["priority"], t["project"])
                except Exception:
                    pass

    # Also scan the formation checklists in holdings/rowdy-crown
    for extra_dir in [PROJECTS_DIR / "holdings", PROJECTS_DIR / "rowdy-crown"]:
        if not extra_dir.exists():
            continue
        slug = dir_to_slug.get(extra_dir.name, extra_dir.name)
        for md_file in extra_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                tasks = _extract_tasks(content, slug, f"{extra_dir.name}/{md_file.name}")
                for t in tasks:
                    _upsert_todo(t["title"], t["description"], t["priority"], t["project"])
            except Exception:
                pass

    return count


def import_all(verbose: bool = False) -> dict[str, int]:
    """Run all importers. Returns counts of records created."""
    db.init_schema()

    results: dict[str, int] = {}

    results["projects"]   = import_projects()
    results["agents"]     = import_agents()
    results["automations"]= import_automations()
    results["clients"]    = import_clients()
    results["knowledge"]  = import_knowledge_from_files()
    results["documents"]  = import_documents_from_files()
    results["todos"]      = import_todos_from_files()
    results["trips"]      = import_trips_from_files()

    if verbose:
        print("ArchonHub Data Import Complete:")
        for k, v in results.items():
            print(f"  {k:15s}: {v} new records")
        total = sum(results.values())
        print(f"  {'TOTAL':15s}: {total} new records")

    return results


if __name__ == "__main__":
    args = set(sys.argv[1:])
    db.init_schema()

    if not args or "--all" in args:
        import_all(verbose=True)
    else:
        if "--projects"    in args: print(f"Projects:    {import_projects()}")
        if "--agents"      in args: print(f"Agents:      {import_agents()}")
        if "--automations" in args: print(f"Automations: {import_automations()}")
        if "--clients"     in args: print(f"Clients:     {import_clients()}")
        if "--todos"       in args: print(f"Todos:       {import_todos_from_files()}")
        if "--trips"       in args: print(f"Trips:       {import_trips_from_files()}")
        if "--docs"        in args:
            print(f"Knowledge:   {import_knowledge_from_files()}")
            print(f"Documents:   {import_documents_from_files()}")
