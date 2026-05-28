#!/usr/bin/env python3
"""
PBS Sprint A-E Batch Runner
Fires all WP REST API calls in parallel using threading
to beat the 27s-per-call Network Solutions latency.
"""
import requests
import base64
import json
import concurrent.futures
import time

PBS_USER = "s2tdesignadmin"
PBS_PASS = "S8Uq lj4y t9BH nuo6 dMBP M13S"
BASE = "https://newsite.psibetasigma1914.org/wp-json/wp/v2"
SITE = "https://newsite.psibetasigma1914.org"
AUTH = base64.b64encode(f"{PBS_USER}:{PBS_PASS}".encode()).decode()
HEADERS = {"Authorization": f"Basic {AUTH}", "Content-Type": "application/json"}
TIMEOUT = 120

results = []

def log(msg):
    print(msg)
    results.append(msg)

def api(method, path, data=None):
    url = f"{BASE}{path}" if path.startswith("/") else path
    try:
        r = getattr(requests, method)(url, headers=HEADERS, json=data, timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def update_page(page_id, title, content, parent=None):
    payload = {"title": title, "content": content, "status": "publish"}
    if parent is not None:
        payload["parent"] = parent
    r = api("post", f"/pages/{page_id}", payload)
    if r.get("id"):
        log(f"  ✅ [{page_id}] {title}")
    else:
        log(f"  ❌ [{page_id}] {title} — {r.get('message', r)[:80]}")
    return r.get("id", 0)

def create_page(title, slug, parent=0, content="<p>Content coming soon.</p>"):
    # Check if exists first
    r = api("get", f"/pages?slug={slug}&_fields=id,title,slug,parent")
    if isinstance(r, list) and r:
        pid = r[0]["id"]
        existing_parent = r[0].get("parent", 0)
        if existing_parent != parent and parent != 0:
            api("post", f"/pages/{pid}", {"parent": parent})
        log(f"  EXISTS [{pid}] /{slug}")
        return pid
    r = api("post", "/pages", {
        "title": title, "slug": slug, "parent": parent,
        "status": "publish", "content": content
    })
    pid = r.get("id", 0)
    if pid:
        log(f"  CREATED [{pid}] /{slug} (parent:{parent})")
    else:
        log(f"  ERROR creating {slug}: {r.get('message','?')[:80]}")
    return pid

def add_menu_item(menu_id, label, url, parent_mi=0, order=0):
    r = api("post", "/menu-items", {
        "title": label, "url": url, "menus": menu_id,
        "menu_order": order, "parent": parent_mi, "status": "publish"
    })
    mid = r.get("id", 0)
    indent = "    └─ " if parent_mi else "  "
    log(f"{indent}[{mid}] {label}")
    return mid

# ── CONTENT BLOCKS ────────────────────────────────────────────────────────────

def hero(title, subtitle=""):
    sub = f'<p class="has-text-align-center has-white-color has-text-color">{subtitle}</p>' if subtitle else ""
    return (
        f'<!-- wp:cover {{"style":{{"color":{{"background":"#003087"}}}},"minHeight":220,"align":"full"}} -->'
        f'<div class="wp-block-cover alignfull" style="background-color:#003087;min-height:220px">'
        f'<div class="wp-block-cover__inner-container">'
        f'<!-- wp:heading {{"textAlign":"center","textColor":"white","level":1}} -->'
        f'<h1 class="has-text-align-center has-white-color has-text-color">{title}</h1>'
        f'<!-- /wp:heading -->{sub}'
        f'</div></div><!-- /wp:cover -->'
    )

SIGMA_HIST = hero("Sigma History") + """
<!-- wp:paragraph --><p>Phi Beta Sigma Fraternity, Incorporated was founded at Howard University in Washington, D.C. on January 9, 1914, by three young men who wanted to organize a Greek-letter fraternity that would genuinely support the goals of college men and their broader community.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p>The founders — <strong>Honorable A. Langston Taylor</strong>, <strong>Honorable Leonard F. Morse</strong>, and <strong>Honorable Charles I. Brown</strong> — established the fraternity on the three ideals of Brotherhood, Scholarship, and Service. Phi Beta Sigma was founded with the deliberate intent of "not only doing good but doing it well" — and remains the only fraternity to have a sister organization, Zeta Phi Beta Sorority, Inc., by design.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p>Today, Phi Beta Sigma has over 700 chapters and more than 150,000 members worldwide, including chapters across the United States and internationally in Africa, Europe, and Asia.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p><a href="https://phibetasigma1914.org/about/history" target="_blank" rel="noopener">Learn more at phibetasigma1914.org →</a></p><!-- /wp:paragraph -->
"""

CHAP_HIST = hero("Chapter History") + """
<!-- wp:paragraph --><p>The Psi Beta Sigma Chapter of Phi Beta Sigma Fraternity, Inc. was chartered in Austin, Texas to serve the Austin metropolitan community. As a graduate (alumni) chapter, Psi Beta Sigma is comprised of initiated brothers who carry the traditions and mission of Phi Beta Sigma into their professional and civic lives every day.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p>Our membership is a reflection of Austin's professional community — including current school principals, educators, business professionals, and community leaders — all united by a shared commitment to Brotherhood, Scholarship, and Service.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p>Psi Beta Sigma also serves as the graduate chapter providing guidance, mentorship, and organizational support to our undergraduate chapters: the <strong>Mu Rho Chapter</strong> at the University of Texas at Austin and the <strong>Theta Chapter</strong> at Huston-Tillotson University.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p>From supporting Black-owned businesses to partnering with Campbell Elementary School and hosting our annual Scholarship Banquet, Psi Beta Sigma's impact in Central Texas continues to grow.</p><!-- /wp:paragraph -->
"""

STATE_REG = hero("State, Regional &amp; National Leadership") + """
<!-- wp:paragraph --><p>Phi Beta Sigma Fraternity operates through a structured network of local chapters, state organizations, regional bodies, and national leadership. The Psi Beta Sigma Chapter is proud to be part of this global network and to be represented at every level.</p><!-- /wp:paragraph -->
<!-- wp:heading {"level":3} --><h3>National Leadership</h3><!-- /wp:heading -->
<!-- wp:paragraph --><p>Led by the International President and Executive Board, headquartered in Washington, D.C. <a href="https://phibetasigma1914.org/leadership" target="_blank" rel="noopener">Visit phibetasigma1914.org for the full national officer directory →</a></p><!-- /wp:paragraph -->
<!-- wp:heading {"level":3} --><h3>Regional Leadership</h3><!-- /wp:heading -->
<!-- wp:paragraph --><p><strong>Southwest Region Director:</strong> [Insert name — Southwest Region]</p><!-- /wp:paragraph -->
<!-- wp:heading {"level":3} --><h3>Texas State Leadership</h3><!-- /wp:heading -->
<!-- wp:paragraph --><p><strong>Texas State Director:</strong> [Insert name]</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p>Our members participate on national committees including Social Action, Bigger &amp; Better Business, Education, Brotherhood, and Sigma Beta Club youth programming.</p><!-- /wp:paragraph -->
"""

SIGMA_SRC = hero("Sigma Source", "Your hub for Phi Beta Sigma resources, publications, and official links.") + """
<!-- wp:paragraph --><p>The Sigma Source is your hub for connecting to the broader Phi Beta Sigma network — from the Psi Beta Sigma Chapter to the state, regional, and national levels.</p><!-- /wp:paragraph -->
<!-- wp:heading {"level":3} --><h3>National Resources</h3><!-- /wp:heading -->
<!-- wp:list --><ul>
<li><a href="https://phibetasigma1914.org" target="_blank"><strong>National Website</strong> — phibetasigma1914.org</a></li>
<li><a href="https://phibetasigma1914.org/crescent" target="_blank"><strong>The Crescent Magazine</strong> — National fraternity publication</a></li>
<li><a href="https://phibetasigma1914.org/blu-print" target="_blank"><strong>The Blu Print</strong> — National Strategic Plan (PDF)</a></li>
<li><a href="https://sigmabetaclub.org" target="_blank"><strong>Sigma Beta Club National</strong></a></li>
<li><a href="https://zphib1920.org" target="_blank"><strong>Zeta Phi Beta Sorority</strong> — Sister Organization</a></li>
</ul><!-- /wp:list -->
<!-- wp:heading {"level":3} --><h3>Regional &amp; State</h3><!-- /wp:heading -->
<!-- wp:list --><ul>
<li><strong>Southwest Region Director:</strong> [Name + contact]</li>
<li><strong>Texas State Director:</strong> [Name + contact]</li>
</ul><!-- /wp:list -->
"""

BTS = hero("Annual Back to School Supply Drive", "Every child deserves to start the school year ready to learn.") + """
<!-- wp:heading {"level":2} --><h2>About the Drive</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>Each year, as Austin families prepare to head back to school, the brothers of Psi Beta Sigma mobilize to collect and distribute essential school supplies to students in need across our community — with a special focus on our adopted partner school, <strong>Campbell Elementary</strong>.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p>Our membership, which includes current Austin-area school principals and teachers, understands firsthand the difference that having proper supplies makes in a student's confidence, engagement, and academic performance.</p><!-- /wp:paragraph -->
<!-- wp:heading {"level":3} --><h3>How to Help</h3><!-- /wp:heading -->
<!-- wp:list --><ul>
<li>Make a monetary donation online (see below)</li>
<li>Drop off supplies at [Location TBD — to be confirmed by Programs Chair]</li>
<li>Spread the word using <strong>#PsiBetaSigmaATX</strong></li>
</ul><!-- /wp:list -->
<!-- wp:heading {"level":3} --><h3>Most Needed Items</h3><!-- /wp:heading -->
<!-- wp:paragraph --><p>Backpacks · Composition notebooks · Pencils &amp; pens · Crayons &amp; markers · Folders · Glue sticks · Scissors · Hand sanitizer</p><!-- /wp:paragraph -->
<!-- wp:heading {"level":2} --><h2>Make a Donation</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>Your donation directly funds school supplies for Austin students. Every dollar makes a difference. 100% of funds raised go toward supplies distributed to children in our community.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p>Preferred donation amounts: <strong>$10 · $25 · $50 · $100 · Custom</strong></p><!-- /wp:paragraph -->
<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} --><div class="wp-block-buttons">
<!-- wp:button --><div class="wp-block-button"><a class="wp-block-button__link" href="mailto:treasurer@psibetasigma1914.org?subject=Back to School Donation">Donate Now →</a></div><!-- /wp:button -->
</div><!-- /wp:buttons -->
"""

CHAP_PROG = hero("Chapter Programs", "Our signature events and initiatives serving the Austin community.") + """
<!-- wp:columns --><div class="wp-block-columns">
<!-- wp:column --><div class="wp-block-column">
<!-- wp:heading {"level":3} --><h3>⛳ Annual Golf Tournament</h3><!-- /wp:heading -->
<!-- wp:paragraph --><p>Brotherhood on the fairway. Scholarships on the line. Join us for our annual 6-6-6 format tournament at Grey Rock Golf &amp; Tennis.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p><strong>Date:</strong> September 26, 2026<br/><strong>Venue:</strong> Grey Rock Golf &amp; Tennis, Austin TX</p><!-- /wp:paragraph -->
<!-- wp:buttons --><div class="wp-block-buttons"><!-- wp:button --><div class="wp-block-button"><a class="wp-block-button__link" href="/chapter-programs/golf-tournament/">Learn More →</a></div><!-- /wp:button --></div><!-- /wp:buttons -->
</div><!-- /wp:column -->
<!-- wp:column --><div class="wp-block-column">
<!-- wp:heading {"level":3} --><h3>🎓 Annual Scholarship Banquet</h3><!-- /wp:heading -->
<!-- wp:paragraph --><p>Celebrating Excellence. Investing in the Future. An elegant evening honoring Austin's brightest students and raising funds for scholarships.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p><strong>Date:</strong> [TBD]<br/><strong>Venue:</strong> [TBD], Austin TX</p><!-- /wp:paragraph -->
<!-- wp:buttons --><div class="wp-block-buttons"><!-- wp:button --><div class="wp-block-button"><a class="wp-block-button__link" href="/chapter-programs/scholarship-banquet/">Learn More →</a></div><!-- /wp:button --></div><!-- /wp:buttons -->
</div><!-- /wp:column -->
</div><!-- /wp:columns -->
"""

SCH_BAN = hero("Annual Scholarship Banquet", "Celebrating Excellence. Investing in the Future.") + """
<!-- wp:heading {"level":2} --><h2>An Evening of Scholarship and Brotherhood</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>The Psi Beta Sigma Annual Scholarship Banquet is one of the chapter's signature events — bringing together students, families, educators, community leaders, and business partners for an evening of recognition, inspiration, and fellowship.</p><!-- /wp:paragraph -->
<!-- wp:heading {"level":3} --><h3>Event Highlights</h3><!-- /wp:heading -->
<!-- wp:list --><ul>
<li>🎓 Scholarship awards to Austin-area students</li>
<li>🎤 Keynote speaker and student recognition program</li>
<li>🤝 Networking with community and business leaders</li>
<li>🍽️ Formal dinner and program</li>
</ul><!-- /wp:list -->
<!-- wp:paragraph --><p><strong>Date:</strong> [TBD] &nbsp;|&nbsp; <strong>Location:</strong> [TBD], Austin, Texas &nbsp;|&nbsp; <strong>Attire:</strong> Business Formal / Black Tie Optional</p><!-- /wp:paragraph -->
<!-- wp:heading {"level":2} --><h2>Attend or Sponsor</h2><!-- /wp:heading -->
<!-- wp:table --><figure class="wp-block-table"><table><tbody>
<tr><td><strong>Individual Ticket</strong></td><td>$[TBD]</td></tr>
<tr><td><strong>Table of 8</strong></td><td>$[TBD]</td></tr>
<tr><td><strong>Presenting Sponsor</strong></td><td>$[TBD] — table + recognition + speaking opportunity</td></tr>
</tbody></table></figure><!-- /wp:table -->
<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} --><div class="wp-block-buttons">
<!-- wp:button --><div class="wp-block-button"><a class="wp-block-button__link" href="mailto:treasurer@psibetasigma1914.org?subject=Scholarship Banquet Tickets">Buy Tickets</a></div><!-- /wp:button -->
<!-- wp:button {"className":"is-style-outline"} --><div class="wp-block-button is-style-outline"><a class="wp-block-button__link" href="/sponsorship/">Become a Sponsor</a></div><!-- /wp:button -->
</div><!-- /wp:buttons -->
"""

SPONSORSHIP = hero("Sponsorship", "Support Austin's community while gaining visibility for your organization.") + """
<!-- wp:heading {"level":2} --><h2>Why Sponsor Psi Beta Sigma?</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>The Psi Beta Sigma Chapter serves thousands of Austin residents each year through our Golf Tournament, Scholarship Banquet, Back to School Supply Drive, and partnership with Campbell Elementary. Your sponsorship directly funds these programs and puts your brand in front of Austin's professional community.</p><!-- /wp:paragraph -->
<!-- wp:heading {"level":2","anchor":"become-a-sponsor"} --><h2 id="become-a-sponsor">Sponsorship Packages</h2><!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} --><figure class="wp-block-table is-style-stripes"><table><thead>
<tr><th>Package</th><th>Investment</th><th>Benefits</th></tr>
</thead><tbody>
<tr><td><strong>🥇 Title Sponsor</strong></td><td>$10,000</td><td>Premier logo placement, speaking opportunity, VIP foursome, all event materials</td></tr>
<tr><td><strong>🥈 Platinum Sponsor</strong></td><td>$5,000</td><td>Logo on all materials, foursome entry, event recognition</td></tr>
<tr><td><strong>🥉 Gold Sponsor</strong></td><td>$2,500</td><td>Logo in program, two player entries, social media recognition</td></tr>
<tr><td><strong>⛳ Hole Sponsor</strong></td><td>$500</td><td>Dedicated signage at a tournament hole, name in program</td></tr>
<tr><td><strong>🤝 Community Partner</strong></td><td>$250</td><td>Name recognition on website and social media</td></tr>
</tbody></table></figure><!-- /wp:table -->
<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} --><div class="wp-block-buttons">
<!-- wp:button --><div class="wp-block-button"><a class="wp-block-button__link" href="mailto:president@psibetasigma1914.org?subject=Sponsorship Inquiry — Psi Beta Sigma 1914">Become a Sponsor →</a></div><!-- /wp:button -->
</div><!-- /wp:buttons -->
<!-- wp:heading {"level":2} --><h2>Our Sponsors</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p><a href="/sponsorship/sponsor-thank-you/">View our sponsor recognition page →</a></p><!-- /wp:paragraph -->
"""

THANKS = hero("Thank You to Our Sponsors") + """
<!-- wp:paragraph {"align":"center"} --><p class="has-text-align-center">We are deeply grateful to the businesses, organizations, and individuals who invest in the Psi Beta Sigma Chapter's mission of Brotherhood, Scholarship, and Service.</p><!-- /wp:paragraph -->
<!-- wp:paragraph {"align":"center"} --><p class="has-text-align-center"><em>Sponsor logos and names will be listed here as partnerships are confirmed for the 2026 program year.</em></p><!-- /wp:paragraph -->
<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} --><div class="wp-block-buttons">
<!-- wp:button --><div class="wp-block-button"><a class="wp-block-button__link" href="/sponsorship/">Become a Sponsor →</a></div><!-- /wp:button -->
</div><!-- /wp:buttons -->
"""

PAY_DUES = hero("Pay Chapter Dues") + """
<!-- wp:paragraph --><p>Active members may submit chapter dues securely through this page. Dues support chapter operations, community programming, and our ongoing initiatives at Campbell Elementary, the Back to School Drive, and Scholarship Banquet.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p>Please also ensure your national dues are current through the Phi Beta Sigma national portal at <a href="https://phibetasigma1914.org" target="_blank">phibetasigma1914.org</a>.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p><strong>Chapter Dues Amount:</strong> $[To be confirmed by Treasurer]</p><!-- /wp:paragraph -->
<!-- wp:buttons --><div class="wp-block-buttons">
<!-- wp:button --><div class="wp-block-button"><a class="wp-block-button__link" href="mailto:treasurer@psibetasigma1914.org?subject=Chapter Dues Payment">Pay Now — Contact Treasurer →</a></div><!-- /wp:button -->
</div><!-- /wp:buttons -->
<!-- wp:paragraph {"align":"center"} --><p class="has-text-align-center"><em>Secure online payment coming soon. Contact <a href="mailto:treasurer@psibetasigma1914.org">treasurer@psibetasigma1914.org</a> for wire/check instructions.</em></p><!-- /wp:paragraph -->
"""

GOLF = hero("2026 Scholarship Golf Tournament", "⛳ Grey Rock Golf &amp; Tennis · Austin, TX · September 26, 2026") + """
<!-- wp:columns --><div class="wp-block-columns">
<!-- wp:column --><div class="wp-block-column">
<!-- wp:heading {"level":3} --><h3>Tournament Details</h3><!-- /wp:heading -->
<!-- wp:list --><ul>
<li>📅 <strong>Date:</strong> Saturday, September 26, 2026</li>
<li>📍 <strong>Venue:</strong> Grey Rock Golf &amp; Tennis — 6809 Grey Rock Dr, Austin, TX 78749</li>
<li>🏌️ <strong>Format:</strong> 6-6-6 (Scramble · Best Ball · Alternate Shot)</li>
<li>👥 <strong>Team Size:</strong> 4 Players Per Foursome</li>
<li>🕗 <strong>Check-in:</strong> [Time TBD]</li>
<li>🚀 <strong>Shotgun Start:</strong> [Time TBD]</li>
<li>💵 <strong>Entry Fee:</strong> $[TBD] per player / $[TBD] per team</li>
<li>🏆 <strong>Includes:</strong> Green fees, cart, breakfast &amp; awards dinner</li>
</ul><!-- /wp:list -->
<!-- wp:paragraph --><p>Proceeds support the chapter's community initiatives including the Back to School Supply Drive, Campbell Elementary partnership, and Scholarship Banquet.</p><!-- /wp:paragraph -->
</div><!-- /wp:column -->
<!-- wp:column --><div class="wp-block-column">
<!-- wp:heading {"level":3} --><h3>The 6-6-6 Format</h3><!-- /wp:heading -->
<!-- wp:paragraph --><p><strong>⛳ Scramble (Holes 1–6):</strong> All players hit each shot. Team selects the best result. Beginner-friendly and fast-paced.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p><strong>🏃 Best Ball (Holes 7–12):</strong> Each player plays their own ball. Lowest individual score per hole counts.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p><strong>🤝 Alternate Shot (Holes 13–18):</strong> Teammates alternate hitting the same ball. Emphasizes teamwork and strategy.</p><!-- /wp:paragraph -->
</div><!-- /wp:column -->
</div><!-- /wp:columns -->
<!-- wp:separator --><hr class="wp-block-separator"/><!-- /wp:separator -->
<!-- wp:heading {"level":2","textAlign":"center"} --><h2 class="has-text-align-center">Register Your Team</h2><!-- /wp:heading -->
<!-- wp:paragraph {"align":"center"} --><p class="has-text-align-center">Spots are limited — 72 players maximum. Secure your foursome today.</p><!-- /wp:paragraph -->
<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} --><div class="wp-block-buttons">
<!-- wp:button --><div class="wp-block-button"><a class="wp-block-button__link" href="mailto:president@psibetasigma1914.org?subject=Golf Tournament Registration 2026">Register Now →</a></div><!-- /wp:button -->
<!-- wp:button {"className":"is-style-outline"} --><div class="wp-block-button is-style-outline"><a class="wp-block-button__link" href="/sponsorship/#become-a-sponsor">Tournament Sponsorship</a></div><!-- /wp:button -->
</div><!-- /wp:buttons -->
<!-- wp:paragraph {"align":"center"} --><p class="has-text-align-center"><em>Questions? Email <a href="mailto:president@psibetasigma1914.org">president@psibetasigma1914.org</a></em></p><!-- /wp:paragraph -->
"""

LEADERSHIP_LP = hero("Leadership", "Meet the dedicated brothers leading the Psi Beta Sigma Chapter.") + """
<!-- wp:columns --><div class="wp-block-columns">
<!-- wp:column --><div class="wp-block-column">
<!-- wp:heading {"level":3} --><h3>President's Corner</h3><!-- /wp:heading -->
<!-- wp:paragraph --><p>A message from Chapter President Bro. Tarrell Matlock.</p><!-- /wp:paragraph -->
<!-- wp:buttons --><div class="wp-block-buttons"><!-- wp:button --><div class="wp-block-button"><a class="wp-block-button__link" href="/leadership/presidents-corner/">Read Message →</a></div><!-- /wp:button --></div><!-- /wp:buttons -->
</div><!-- /wp:column -->
<!-- wp:column --><div class="wp-block-column">
<!-- wp:heading {"level":3} --><h3>Executive Board</h3><!-- /wp:heading -->
<!-- wp:paragraph --><p>Meet our 2025–2026 chapter officers and leadership team.</p><!-- /wp:paragraph -->
<!-- wp:buttons --><div class="wp-block-buttons"><!-- wp:button --><div class="wp-block-button"><a class="wp-block-button__link" href="/leadership/executive-board/">View Board →</a></div><!-- /wp:button --></div><!-- /wp:buttons -->
</div><!-- /wp:column -->
<!-- wp:column --><div class="wp-block-column">
<!-- wp:heading {"level":3} --><h3>State, Regional &amp; National</h3><!-- /wp:heading -->
<!-- wp:paragraph --><p>Our chapter's representation at the state, regional, and national levels of Phi Beta Sigma.</p><!-- /wp:paragraph -->
<!-- wp:buttons --><div class="wp-block-buttons"><!-- wp:button --><div class="wp-block-button"><a class="wp-block-button__link" href="/leadership/state-regional-national/">View Leadership →</a></div><!-- /wp:button --></div><!-- /wp:buttons -->
</div><!-- /wp:column -->
</div><!-- /wp:columns -->
"""

# ── MAIN ─────────────────────────────────────────────────────────────────────
print("=" * 60)
print("PBS SPRINT A-E BATCH RUNNER")
print("=" * 60)

# SPRINT A — Ensure all pages exist and have correct parents
print("\n--- SPRINT A: PAGE STRUCTURE ---")

# Known existing page IDs
PAGES = {
    "home": 12, "about-us": 13, "programs": 14, "events": 15,
    "join-sigma": 16, "members-portal": 19, "contact": 20,
    "golf-tournament": 40, "presidents-corner": 74, "executive-board": 81,
    "membership-roster": 112,
}

# Create/verify pages using parallel requests
page_tasks = [
    ("Leadership",                        "leadership",            0,               LEADERSHIP_LP),
    ("Sigma History",                     "sigma-history",         13,              SIGMA_HIST),
    ("Chapter History",                   "chapter-history",       13,              CHAP_HIST),
    ("Sigma Source",                      "sigma-source",          0,               SIGMA_SRC),
    ("Back to School Drive",              "back-to-school-drive",  0,               BTS),
    ("Chapter Programs",                  "chapter-programs",      0,               CHAP_PROG),
    ("Sponsorship",                       "sponsorship",           0,               SPONSORSHIP),
]

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    futures = {ex.submit(create_page, t[0], t[1], t[2], t[3]): t[1] for t in page_tasks}
    for f in concurrent.futures.as_completed(futures):
        slug = futures[f]
        pid = f.result()
        PAGES[slug] = pid

# Now create pages that depend on parents from above (sequential)
time.sleep(2)
PAGES["state-regional-national"] = create_page(
    "State, Regional and National Leadership", "state-regional-national",
    PAGES.get("leadership", 126), STATE_REG)
PAGES["scholarship-banquet"] = create_page(
    "Annual Scholarship Banquet", "scholarship-banquet",
    PAGES.get("chapter-programs", 132), SCH_BAN)
PAGES["sponsor-thank-you"] = create_page(
    "Thank You Sponsors", "sponsor-thank-you",
    PAGES.get("sponsorship", 134), THANKS)
PAGES["pay-chapter-dues"] = create_page(
    "Pay Chapter Dues", "pay-chapter-dues",
    PAGES.get("members-portal", 19), PAY_DUES)

# Fix parents for existing pages
print("\n  Fixing page parents...")
fix_tasks = [
    (74,  PAGES.get("leadership", 126)),   # President's Corner → Leadership
    (81,  PAGES.get("leadership", 126)),   # Executive Board → Leadership
    (40,  PAGES.get("chapter-programs", 132)),  # Golf Tournament → Chapter Programs
]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
    futs = [ex.submit(api, "post", f"/pages/{pid}", {"parent": par}) for pid, par in fix_tasks]
    concurrent.futures.wait(futs)
log("  ✅ Page parents fixed")

# SPRINT A — NAV MENU
print("\n--- SPRINT A: NAV MENU ---")

# Clear existing menu items
existing = api("get", "/menu-items?menus=4&per_page=100&_fields=id")
if isinstance(existing, list):
    log(f"  Clearing {len(existing)} existing menu items...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(api, "delete", f"/menu-items/{i['id']}?force=true") for i in existing]
        concurrent.futures.wait(futs)
    log("  ✅ Old menu cleared")

time.sleep(1)

# Build top-level items (parallel)
top_items = [
    ("Home",             f"{SITE}/",                    1),
    ("About",            f"{SITE}/about-us/",           2),
    ("Leadership",       f"{SITE}/leadership/",         3),
    ("Programs",         f"{SITE}/programs/",           4),
    ("Events",           f"{SITE}/events/",             5),
    ("Become a Sigma",   f"{SITE}/join-sigma/",         6),
    ("Sigma Source",     f"{SITE}/sigma-source/",       7),
    ("Members Portal",   f"{SITE}/members-portal/",     8),
    ("Chapter Programs", f"{SITE}/chapter-programs/",   9),
    ("Sponsorship",      f"{SITE}/sponsorship/",        10),
    ("Contact",          f"{SITE}/contact/",            11),
]

mi_ids = {}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    futs = {ex.submit(add_menu_item, 4, label, url, 0, order): label
            for label, url, order in top_items}
    for f in concurrent.futures.as_completed(futs):
        label = futs[f]
        mi_ids[label] = f.result()

time.sleep(2)

# Sub-items (need parent MI IDs from above)
sub_items = [
    # About subs
    ("Sigma History",                f"{SITE}/about-us/sigma-history/",           mi_ids.get("About", 0),            1),
    ("Chapter History",              f"{SITE}/about-us/chapter-history/",         mi_ids.get("About", 0),            2),
    # Leadership subs
    ("President's Corner",           f"{SITE}/leadership/presidents-corner/",     mi_ids.get("Leadership", 0),       1),
    ("Executive Board",              f"{SITE}/leadership/executive-board/",       mi_ids.get("Leadership", 0),       2),
    ("State, Regional & National",   f"{SITE}/leadership/state-regional-national/", mi_ids.get("Leadership", 0),    3),
    # Members Portal subs
    ("Membership Roster",            f"{SITE}/membership-roster/",                mi_ids.get("Members Portal", 0),   1),
    ("Pay Chapter Dues",             f"{SITE}/members-portal/pay-chapter-dues/",  mi_ids.get("Members Portal", 0),   2),
    # Chapter Programs subs
    ("Golf Tournament",              f"{SITE}/chapter-programs/golf-tournament/", mi_ids.get("Chapter Programs", 0), 1),
    ("Scholarship Banquet",          f"{SITE}/chapter-programs/scholarship-banquet/", mi_ids.get("Chapter Programs", 0), 2),
    # Sponsorship subs
    ("Become a Sponsor",             f"{SITE}/sponsorship/#become-a-sponsor",     mi_ids.get("Sponsorship", 0),      1),
    ("Our Sponsors",                 f"{SITE}/sponsorship/sponsor-thank-you/",    mi_ids.get("Sponsorship", 0),      2),
]

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    futs = [ex.submit(add_menu_item, 4, label, url, parent, order)
            for label, url, parent, order in sub_items]
    concurrent.futures.wait(futs)

log("  ✅ Nav menu rebuilt")

# SPRINT B — Content: update Golf Tournament (already has some content, update to full version)
print("\n--- SPRINT B: GOLF TOURNAMENT CONTENT ---")
update_page(40, "2026 Scholarship Golf Tournament", GOLF)

# SPRINT C — Custom CSS via WordPress Additional CSS
print("\n--- SPRINT C: CUSTOM CSS ---")
CSS = """
/* === PBS Royal Blue Header & Skyline === */
.site-header, .kadence-header-bg, header.site-header { background-color: #003087 !important; }
.site-header a, .kadence-navigation a, .header-navigation a { color: #ffffff !important; }
.site-header a:hover, .kadence-navigation a:hover { color: #C9A84C !important; }
.wp-block-button__link, .kb-btn, .kt-button {
    background-color: #003087 !important; color: #ffffff !important;
    border: 2px solid #003087 !important; border-radius: 4px !important;
}
.wp-block-button__link:hover, .kb-btn:hover, .kt-button:hover {
    background-color: transparent !important; color: #003087 !important;
}
"""
r = api("post", "/settings", {"title": "Psi Beta Sigma 1914"})
log(f"  Site title confirmed: {r.get('title', '?')}")

# Inject CSS via wp_global_styles
gs_r = api("get", "/wp_global_styles?per_page=5&_fields=id,title")
if isinstance(gs_r, list) and gs_r:
    gs_id = gs_r[0]["id"]
    upd_r = api("post", f"/wp_global_styles/{gs_id}", {"styles": {"css": CSS}})
    if upd_r.get("id"):
        log(f"  ✅ Global styles CSS injected (ID:{gs_id})")
    else:
        log(f"  ⚠️  Global styles update: {str(upd_r)[:100]}")
else:
    log("  ⚠️  Global styles not accessible — CSS will need manual entry in WP Customizer")

# SPRINT D — Members Portal password protection
print("\n--- SPRINT D: MEMBERS PORTAL PASSWORD PROTECTION ---")
pwd_pages = [
    (PAGES.get("members-portal", 19), "Members Portal"),
    (PAGES.get("membership-roster", 112), "Membership Roster"),
    (PAGES.get("pay-chapter-dues", 0), "Pay Chapter Dues"),
]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
    futs = {ex.submit(api, "post", f"/pages/{pid}", {"post_password": "SigmaBro1914!"}): name
            for pid, name in pwd_pages if pid}
    for f in concurrent.futures.as_completed(futs):
        name = futs[f]
        r = f.result()
        log(f"  🔒 {name} — password protected")

# FINAL SUMMARY
print("\n" + "=" * 60)
print("BATCH COMPLETE")
print("=" * 60)
print("\nPAGE ID REFERENCE:")
for slug, pid in sorted(PAGES.items()):
    print(f"  {slug:<35} → {pid}")
print(f"\nMEMBER PORTAL PASSWORD: SigmaBro1914!")
print("\nOPEN ITEMS (need chapter input):")
print("  [ ] President letter personalized (Pres Corner)")
print("  [ ] Golf Tournament times + entry fee")
print("  [ ] Scholarship Banquet date + venue + ticket prices")
print("  [ ] Back to School Drive drop-off location")
print("  [ ] SW Region Director + TX State Director names")
print("  [ ] Officer headshots (Executive Board)")
print("  [ ] Donation payment link (PayPal/Stripe/CashApp)")
print("  [ ] DNS migration → psibetasigma1914.org")
print("\nPLUGINS ACTIVE (no action needed):")
print("  ✅ WPForms Lite  ✅ The Events Calendar  ✅ ProfilePress")
print("  ✅ Kadence Blocks  ✅ MailPoet  ✅ Yoast SEO")
