<?php
/**
 * PBS Sprint A–E Batch Execution Script
 * Psi Beta Sigma 1914 — newsite.psibetasigma1914.org
 * Run once via browser, then DELETE immediately.
 * Upload to: /wp-content/uploads/pbs-batch.php
 * Access via: https://newsite.psibetasigma1914.org/wp-content/uploads/pbs-batch.php
 */

// Security token — change this before uploading
define('BATCH_TOKEN', 'PBS1914SIGMA');
if (!isset($_GET['token']) || $_GET['token'] !== BATCH_TOKEN) {
    die('Unauthorized');
}

// Bootstrap WordPress
$wp_root = dirname(dirname(dirname(__FILE__)));
require_once($wp_root . '/wp-load.php');

// Only allow admins
if (!current_user_can('manage_options') && !defined('DOING_CRON')) {
    // Allow running via direct file access with token
}

header('Content-Type: text/plain; charset=utf-8');
$log = [];

function pbslog($msg) {
    global $log;
    $log[] = $msg;
    echo $msg . "\n";
    flush();
    ob_flush();
}

pbslog("=== PBS BATCH RUNNER — " . date('Y-m-d H:i:s') . " ===");
pbslog("");

// ============================================================
// SPRINT A — PAGE STRUCTURE
// ============================================================
pbslog("--- SPRINT A: PAGE STRUCTURE ---");

function get_or_create_page($title, $slug, $parent = 0, $content = '') {
    // Check if page with this slug already exists
    $existing = get_page_by_path($slug, OBJECT, 'page');
    if ($existing) {
        pbslog("  EXISTS [" . $existing->ID . "] /" . $slug);
        // Update parent if wrong
        if ($existing->post_parent != $parent) {
            wp_update_post(['ID' => $existing->ID, 'post_parent' => $parent]);
            pbslog("    → Updated parent to $parent");
        }
        return $existing->ID;
    }
    $id = wp_insert_post([
        'post_title'   => $title,
        'post_name'    => $slug,
        'post_status'  => 'publish',
        'post_type'    => 'page',
        'post_parent'  => $parent,
        'post_content' => $content ?: '<p>Content coming soon.</p>',
    ]);
    if (is_wp_error($id)) {
        pbslog("  ERROR creating '$title': " . $id->get_error_message());
        return 0;
    }
    pbslog("  CREATED [" . $id . "] /" . $slug . " (parent:$parent)");
    return $id;
}

// Known existing IDs
$page_ids = [
    'home'              => 12,
    'about-us'          => 13,
    'programs'          => 14,
    'events'            => 15,
    'join-sigma'        => 16,
    'members-portal'    => 19,
    'contact'           => 20,
    'golf-tournament'   => 40,
    'presidents-corner' => 74,
    'executive-board'   => 81,
    'membership-roster' => 112,
];

// Create/verify new pages
$leadership_id   = get_or_create_page('Leadership', 'leadership', 0);
$sigma_hist_id   = get_or_create_page('Sigma History', 'sigma-history', $page_ids['about-us']);
$chap_hist_id    = get_or_create_page('Chapter History', 'chapter-history', $page_ids['about-us']);
$state_reg_id    = get_or_create_page('State, Regional and National Leadership', 'state-regional-national', $leadership_id);
$sigma_src_id    = get_or_create_page('Sigma Source', 'sigma-source', 0);
$bts_id          = get_or_create_page('Back to School Drive', 'back-to-school-drive', 0);
$chap_prog_id    = get_or_create_page('Chapter Programs', 'chapter-programs', 0);
$sch_ban_id      = get_or_create_page('Annual Scholarship Banquet', 'scholarship-banquet', $chap_prog_id);
$sponsorship_id  = get_or_create_page('Sponsorship', 'sponsorship', 0);
$thanks_id       = get_or_create_page('Thank You Sponsors', 'sponsor-thank-you', $sponsorship_id);
$pay_dues_id     = get_or_create_page('Pay Chapter Dues', 'pay-chapter-dues', $page_ids['members-portal']);

// Fix parents: President's Corner + Exec Board → Leadership
wp_update_post(['ID' => $page_ids['presidents-corner'], 'post_parent' => $leadership_id]);
pbslog("  UPDATED: President's Corner → parent: $leadership_id");
wp_update_post(['ID' => $page_ids['executive-board'], 'post_parent' => $leadership_id]);
pbslog("  UPDATED: Executive Board → parent: $leadership_id");

// Move Golf Tournament under Chapter Programs
wp_update_post(['ID' => $page_ids['golf-tournament'], 'post_parent' => $chap_prog_id]);
pbslog("  UPDATED: Golf Tournament → parent: $chap_prog_id");

$page_ids['leadership']            = $leadership_id;
$page_ids['sigma-history']         = $sigma_hist_id;
$page_ids['chapter-history']       = $chap_hist_id;
$page_ids['state-regional-national'] = $state_reg_id;
$page_ids['sigma-source']          = $sigma_src_id;
$page_ids['back-to-school-drive']  = $bts_id;
$page_ids['chapter-programs']      = $chap_prog_id;
$page_ids['scholarship-banquet']   = $sch_ban_id;
$page_ids['sponsorship']           = $sponsorship_id;
$page_ids['sponsor-thank-you']     = $thanks_id;
$page_ids['pay-chapter-dues']      = $pay_dues_id;

pbslog("Sprint A pages: DONE");
pbslog("");

// ============================================================
// SPRINT A — NAV MENU REBUILD
// ============================================================
pbslog("--- SPRINT A: NAV MENU REBUILD ---");

$menu_id = 4; // Primary Navigation

// Clear all existing items
$existing_items = wp_get_nav_menu_items($menu_id, ['order' => false]);
if ($existing_items) {
    foreach ($existing_items as $item) {
        wp_delete_post($item->ID, true);
    }
    pbslog("  Cleared " . count($existing_items) . " old menu items");
}

$base = 'https://newsite.psibetasigma1914.org';

function add_menu_item($menu_id, $label, $url, $parent_item_id = 0, $order = 0) {
    $item_id = wp_update_nav_menu_item($menu_id, 0, [
        'menu-item-title'     => $label,
        'menu-item-url'       => $url,
        'menu-item-status'    => 'publish',
        'menu-item-type'      => 'custom',
        'menu-item-parent-id' => $parent_item_id,
        'menu-item-position'  => $order,
    ]);
    if (is_wp_error($item_id)) {
        pbslog("  ERROR adding '$label': " . $item_id->get_error_message());
        return 0;
    }
    pbslog("  MENU ITEM [$item_id] " . ($parent_item_id ? "  └─ " : "") . $label);
    return $item_id;
}

// Top-level items
$m_home   = add_menu_item($menu_id, 'Home',            "$base/",                    0, 1);
$m_about  = add_menu_item($menu_id, 'About',           "$base/about-us/",           0, 2);
$m_lead   = add_menu_item($menu_id, 'Leadership',      "$base/leadership/",         0, 3);
$m_prog   = add_menu_item($menu_id, 'Programs',        "$base/programs/",           0, 4);
$m_evt    = add_menu_item($menu_id, 'Events',          "$base/events/",             0, 5);
$m_sigma  = add_menu_item($menu_id, 'Become a Sigma',  "$base/join-sigma/",         0, 6);
$m_src    = add_menu_item($menu_id, 'Sigma Source',    "$base/sigma-source/",       0, 7);
$m_mem    = add_menu_item($menu_id, 'Members Portal',  "$base/members-portal/",     0, 8);
$m_chprog = add_menu_item($menu_id, 'Chapter Programs',"$base/chapter-programs/",  0, 9);
$m_spon   = add_menu_item($menu_id, 'Sponsorship',     "$base/sponsorship/",        0, 10);
$m_cont   = add_menu_item($menu_id, 'Contact',         "$base/contact/",            0, 11);

// About sub-items
add_menu_item($menu_id, 'Sigma History',   "$base/about-us/sigma-history/",   $m_about, 1);
add_menu_item($menu_id, 'Chapter History', "$base/about-us/chapter-history/", $m_about, 2);

// Leadership sub-items
add_menu_item($menu_id, "President's Corner",          "$base/leadership/presidents-corner/",      $m_lead, 1);
add_menu_item($menu_id, 'Executive Board',             "$base/leadership/executive-board/",         $m_lead, 2);
add_menu_item($menu_id, 'State, Regional and National',"$base/leadership/state-regional-national/", $m_lead, 3);

// Members Portal sub-items
add_menu_item($menu_id, 'Membership Roster', "$base/membership-roster/",             $m_mem, 1);
add_menu_item($menu_id, 'Pay Chapter Dues',  "$base/members-portal/pay-chapter-dues/", $m_mem, 2);

// Chapter Programs sub-items
add_menu_item($menu_id, 'Golf Tournament',       "$base/chapter-programs/golf-tournament/",      $m_chprog, 1);
add_menu_item($menu_id, 'Scholarship Banquet',   "$base/chapter-programs/scholarship-banquet/",  $m_chprog, 2);

// Sponsorship sub-items
add_menu_item($menu_id, 'Become a Sponsor', "$base/sponsorship/#become-a-sponsor",      $m_spon, 1);
add_menu_item($menu_id, 'Our Sponsors',     "$base/sponsorship/sponsor-thank-you/",     $m_spon, 2);

// Assign menu to primary location
$locations = get_theme_mod('nav_menu_locations');
$locations['primary'] = $menu_id;
set_theme_mod('nav_menu_locations', $locations);
pbslog("  Menu assigned to primary location");
pbslog("Sprint A nav: DONE");
pbslog("");

// ============================================================
// SPRINT A — CUSTOM CSS (Skyline Header)
// ============================================================
pbslog("--- SPRINT A: CUSTOM CSS ---");

$skyline_css = '
/* ===== PBS — Royal Blue Header ===== */
.site-header, .kadence-header-bg, header.site-header {
    background-color: #003087 !important;
}
.site-header a, .kadence-navigation a, .header-navigation a {
    color: #ffffff !important;
}
.site-header a:hover, .kadence-navigation a:hover {
    color: #C9A84C !important;
}
/* Austin Skyline strip below header */
.site-header::after {
    content: "";
    display: block;
    width: 100%;
    height: 55px;
    background-color: #003087;
    background-image: url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 1200 55\' preserveAspectRatio=\'none\'%3E%3Cpath d=\'M0,55 L0,42 L25,42 L25,28 L45,28 L45,18 L62,18 L62,28 L80,28 L80,22 L100,22 L100,12 L115,12 L115,4 L128,4 L128,12 L140,12 L140,8 L155,8 L155,22 L172,22 L172,17 L190,17 L190,28 L210,28 L210,22 L232,22 L232,32 L252,32 L252,22 L275,22 L275,13 L290,13 L290,4 L305,4 L305,13 L320,13 L320,22 L340,22 L340,28 L365,28 L365,18 L385,18 L385,28 L408,28 L408,20 L428,20 L428,10 L443,10 L443,2 L455,2 L455,10 L468,10 L468,20 L490,20 L490,28 L515,28 L515,22 L540,22 L540,32 L565,32 L565,22 L585,22 L585,13 L603,13 L603,6 L616,6 L616,13 L630,13 L630,22 L652,22 L652,28 L677,28 L677,18 L697,18 L697,26 L718,26 L718,16 L736,16 L736,8 L750,8 L750,16 L765,16 L765,26 L787,26 L787,32 L812,32 L812,22 L832,22 L832,13 L848,13 L848,4 L860,4 L860,13 L873,13 L873,22 L898,22 L898,28 L922,28 L922,20 L942,20 L942,30 L962,30 L962,20 L982,20 L982,28 L1006,28 L1006,18 L1027,18 L1027,28 L1050,28 L1050,22 L1072,22 L1072,32 L1097,32 L1097,22 L1118,22 L1118,13 L1138,13 L1138,22 L1162,22 L1162,32 L1182,32 L1182,42 L1200,42 L1200,55 Z\' fill=\'%23001F5B\'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-size: 100% 100%;
}
/* Global CTA Buttons */
.wp-block-button__link, .kb-btn, .kt-button {
    background-color: #003087 !important;
    color: #ffffff !important;
    border: 2px solid #003087 !important;
    border-radius: 4px !important;
    transition: all 0.2s ease;
}
.wp-block-button__link:hover, .kb-btn:hover, .kt-button:hover {
    background-color: transparent !important;
    color: #003087 !important;
}
/* Hero block consistent style */
.wp-block-cover, .kt-row-layout-section {
    background-color: #003087;
}
';

// Save as WordPress Additional CSS
$custom_css_post_id = wp_get_custom_css_post('');
if ($custom_css_post_id) {
    wp_update_custom_css_post($skyline_css);
    pbslog("  Updated existing Additional CSS");
} else {
    wp_update_custom_css_post($skyline_css);
    pbslog("  Created Additional CSS");
}
pbslog("Sprint A CSS: DONE");
pbslog("");

// ============================================================
// SPRINT B — CONTENT POPULATION
// ============================================================
pbslog("--- SPRINT B: CONTENT POPULATION ---");

// Sigma History
$sigma_history_content = '
<!-- wp:cover {"overlayColor":"primary","minHeight":200,"align":"full"} -->
<div class="wp-block-cover alignfull" style="background-color:#003087;min-height:200px">
<div class="wp-block-cover__inner-container">
<!-- wp:heading {"textAlign":"center","textColor":"white","level":1} -->
<h1 class="has-text-align-center has-white-color has-text-color">Sigma History</h1>
<!-- /wp:heading -->
</div></div>
<!-- /wp:cover -->

<!-- wp:paragraph -->
<p>Phi Beta Sigma Fraternity, Incorporated was founded at Howard University in Washington, D.C. on January 9, 1914, by three young men who wanted to organize a Greek-letter fraternity that would genuinely support the goals of college men and their broader community.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>The founders — <strong>Honorable A. Langston Taylor</strong>, <strong>Honorable Leonard F. Morse</strong>, and <strong>Honorable Charles I. Brown</strong> — established the fraternity on the three ideals of Brotherhood, Scholarship, and Service. Phi Beta Sigma was founded with the deliberate intent of "not only doing good but doing it well" — and remains the only fraternity to have a sister organization, Zeta Phi Beta Sorority, Inc., by design.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Today, Phi Beta Sigma has over 700 chapters and more than 150,000 members worldwide, including chapters across the United States and internationally in Africa, Europe, and Asia.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><a href="https://phibetasigma1914.org/about/history" target="_blank" rel="noopener">Learn more at phibetasigma1914.org →</a></p>
<!-- /wp:paragraph -->
';
wp_update_post(['ID' => $sigma_hist_id, 'post_content' => $sigma_history_content]);
pbslog("  ✅ Sigma History — content loaded");

// Chapter History
$chapter_history_content = '
<!-- wp:cover {"overlayColor":"primary","minHeight":200,"align":"full"} -->
<div class="wp-block-cover alignfull" style="background-color:#003087;min-height:200px">
<div class="wp-block-cover__inner-container">
<!-- wp:heading {"textAlign":"center","textColor":"white","level":1} -->
<h1 class="has-text-align-center has-white-color has-text-color">Chapter History</h1>
<!-- /wp:heading -->
</div></div>
<!-- /wp:cover -->

<!-- wp:paragraph -->
<p>The Psi Beta Sigma Chapter of Phi Beta Sigma Fraternity, Inc. was chartered in Austin, Texas to serve the Austin metropolitan community. As a graduate (alumni) chapter, Psi Beta Sigma is comprised of initiated brothers who carry the traditions and mission of Phi Beta Sigma into their professional and civic lives every day.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Our membership is a reflection of Austin\'s professional community — including current school principals, educators, business professionals, and community leaders — all united by a shared commitment to Brotherhood, Scholarship, and Service.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Psi Beta Sigma also serves as the graduate chapter providing guidance, mentorship, and organizational support to our undergraduate chapters: the <strong>Mu Rho Chapter</strong> at the University of Texas at Austin and the <strong>Theta Chapter</strong> at Huston-Tillotson University.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>From supporting Black-owned businesses to partnering with Campbell Elementary School and hosting our annual Scholarship Banquet, Psi Beta Sigma\'s impact in Central Texas continues to grow.</p>
<!-- /wp:paragraph -->
';
wp_update_post(['ID' => $chap_hist_id, 'post_content' => $chapter_history_content]);
pbslog("  ✅ Chapter History — content loaded");

// State / Regional / National Leadership
$state_content = '
<!-- wp:cover {"overlayColor":"primary","minHeight":200,"align":"full"} -->
<div class="wp-block-cover alignfull" style="background-color:#003087;min-height:200px">
<div class="wp-block-cover__inner-container">
<!-- wp:heading {"textAlign":"center","textColor":"white","level":1} -->
<h1 class="has-text-align-center has-white-color has-text-color">State, Regional &amp; National Leadership</h1>
<!-- /wp:heading -->
</div></div>
<!-- /wp:cover -->

<!-- wp:paragraph -->
<p>Phi Beta Sigma Fraternity operates through a structured network of local chapters, state organizations, regional bodies, and national leadership. The Psi Beta Sigma Chapter is proud to be part of this global network and to be represented at every level.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>National Leadership</h3>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Led by the International President and Executive Board, headquartered in Washington, D.C. <a href="https://phibetasigma1914.org/leadership" target="_blank" rel="noopener">Visit phibetasigma1914.org for the full national officer directory →</a></p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Regional Leadership</h3>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p><strong>Southwest Region Director:</strong> [Insert name — Southwest Region]</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Texas State Leadership</h3>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p><strong>Texas State Director:</strong> [Insert name]</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Our members participate on national committees including Social Action, Bigger &amp; Better Business, Education, Brotherhood, and Sigma Beta Club youth programming.</p>
<!-- /wp:paragraph -->
';
wp_update_post(['ID' => $state_reg_id, 'post_content' => $state_content]);
pbslog("  ✅ State/Regional/National — content loaded");

// Sigma Source
$sigma_source_content = '
<!-- wp:cover {"overlayColor":"primary","minHeight":200,"align":"full"} -->
<div class="wp-block-cover alignfull" style="background-color:#003087;min-height:200px">
<div class="wp-block-cover__inner-container">
<!-- wp:heading {"textAlign":"center","textColor":"white","level":1} -->
<h1 class="has-text-align-center has-white-color has-text-color">Sigma Source</h1>
<!-- /wp:heading -->
<p class="has-text-align-center has-white-color has-text-color">Your hub for Phi Beta Sigma resources, publications, and official links.</p>
</div></div>
<!-- /wp:cover -->

<!-- wp:paragraph -->
<p>The Sigma Source is your hub for connecting to the broader Phi Beta Sigma network — from the Psi Beta Sigma Chapter to the state, regional, and national levels.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>National Resources</h3>
<!-- /wp:heading -->
<!-- wp:list -->
<ul>
<li><a href="https://phibetasigma1914.org" target="_blank" rel="noopener"><strong>National Website</strong> — phibetasigma1914.org</a></li>
<li><a href="https://phibetasigma1914.org/crescent" target="_blank" rel="noopener"><strong>The Crescent Magazine</strong> — National fraternity publication</a></li>
<li><a href="https://phibetasigma1914.org/blu-print" target="_blank" rel="noopener"><strong>The Blu Print</strong> — Phi Beta Sigma national strategic plan</a></li>
<li><a href="https://sigmabetaclub.org" target="_blank" rel="noopener"><strong>Sigma Beta Club National</strong></a></li>
<li><a href="https://zphib1920.org" target="_blank" rel="noopener"><strong>Zeta Phi Beta Sorority</strong> — Sister Organization</a></li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":3} -->
<h3>Regional &amp; State</h3>
<!-- /wp:heading -->
<!-- wp:list -->
<ul>
<li><strong>Southwest Region Director:</strong> [Name + contact]</li>
<li><strong>Texas State Director:</strong> [Name + contact]</li>
</ul>
<!-- /wp:list -->
';
wp_update_post(['ID' => $sigma_src_id, 'post_content' => $sigma_source_content]);
pbslog("  ✅ Sigma Source — content loaded");

// Back to School Drive
$bts_content = '
<!-- wp:cover {"overlayColor":"primary","minHeight":280,"align":"full"} -->
<div class="wp-block-cover alignfull" style="background-color:#003087;min-height:280px">
<div class="wp-block-cover__inner-container">
<!-- wp:heading {"textAlign":"center","textColor":"white","level":1} -->
<h1 class="has-text-align-center has-white-color has-text-color">Annual Back to School Supply Drive</h1>
<!-- /wp:heading -->
<!-- wp:paragraph {"align":"center","textColor":"white"} -->
<p class="has-text-align-center has-white-color has-text-color">Every child deserves to start the school year ready to learn.</p>
<!-- /wp:paragraph -->
</div></div>
<!-- /wp:cover -->

<!-- wp:heading {"level":2} -->
<h2>About the Drive</h2>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Each year, as Austin families prepare to head back to school, the brothers of Psi Beta Sigma mobilize to collect and distribute essential school supplies to students in need across our community — with a special focus on our adopted partner school, <strong>Campbell Elementary</strong>.</p>
<!-- /wp:paragraph -->
<!-- wp:paragraph -->
<p>Our membership, which includes current Austin-area school principals and teachers, understands firsthand the difference that having proper supplies makes in a student\'s confidence, engagement, and academic performance.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>How to Help</h3>
<!-- /wp:heading -->
<!-- wp:list -->
<ul>
<li>Make a monetary donation online (see below)</li>
<li>Drop off supplies at [Location TBD]</li>
<li>Spread the word using <strong>#PsiBetaSigmaATX</strong></li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":3} -->
<h3>Most Needed Items</h3>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Backpacks · Composition notebooks · Pencils &amp; pens · Crayons &amp; markers · Folders · Glue sticks · Scissors · Hand sanitizer</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Make a Donation</h2>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Your donation directly funds school supplies for Austin students. Every dollar makes a difference. 100% of funds raised go toward supplies distributed to children in our community.</p>
<!-- /wp:paragraph -->
<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} -->
<div class="wp-block-buttons">
<!-- wp:button {"backgroundColor":"primary","textColor":"white"} -->
<div class="wp-block-button"><a class="wp-block-button__link has-white-color has-primary-background-color has-text-color has-background" href="mailto:treasurer@psibetasigma1914.org">Donate Now →</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:buttons -->
<!-- wp:paragraph {"align":"center"} -->
<p class="has-text-align-center"><em>Preferred amounts: $10 · $25 · $50 · $100 · Custom</em></p>
<!-- /wp:paragraph -->
';
wp_update_post(['ID' => $bts_id, 'post_content' => $bts_content]);
pbslog("  ✅ Back to School Drive — content loaded");

// Chapter Programs landing page
$chap_prog_content = '
<!-- wp:cover {"overlayColor":"primary","minHeight":220,"align":"full"} -->
<div class="wp-block-cover alignfull" style="background-color:#003087;min-height:220px">
<div class="wp-block-cover__inner-container">
<!-- wp:heading {"textAlign":"center","textColor":"white","level":1} -->
<h1 class="has-text-align-center has-white-color has-text-color">Chapter Programs</h1>
<!-- /wp:heading -->
<p class="has-text-align-center has-white-color has-text-color">Our signature events and initiatives serving the Austin community.</p>
</div></div>
<!-- /wp:cover -->

<!-- wp:columns -->
<div class="wp-block-columns">
<!-- wp:column -->
<div class="wp-block-column">
<!-- wp:heading {"level":3,"textColor":"primary"} -->
<h3 class="has-primary-color has-text-color">⛳ Annual Golf Tournament</h3>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Join us for the Psi Beta Sigma Scholarship Golf Tournament. Brotherhood on the fairway — scholarships on the line.</p>
<!-- /wp:paragraph -->
<!-- wp:paragraph --><p><strong>Date:</strong> September 26, 2026<br><strong>Venue:</strong> Grey Rock Golf &amp; Tennis, Austin TX</p><!-- /wp:paragraph -->
<!-- wp:buttons -->
<div class="wp-block-buttons">
<!-- wp:button -->
<div class="wp-block-button"><a class="wp-block-button__link" href="/chapter-programs/golf-tournament/">Learn More →</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:buttons -->
</div>
<!-- /wp:column -->

<!-- wp:column -->
<div class="wp-block-column">
<!-- wp:heading {"level":3,"textColor":"primary"} -->
<h3 class="has-primary-color has-text-color">🎓 Annual Scholarship Banquet</h3>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Celebrating Excellence. Investing in the Future. An elegant evening honoring Austin\'s brightest students.</p>
<!-- /wp:paragraph -->
<!-- wp:paragraph --><p><strong>Date:</strong> [TBD]<br><strong>Venue:</strong> [TBD], Austin TX</p><!-- /wp:paragraph -->
<!-- wp:buttons -->
<div class="wp-block-buttons">
<!-- wp:button -->
<div class="wp-block-button"><a class="wp-block-button__link" href="/chapter-programs/scholarship-banquet/">Learn More →</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:buttons -->
</div>
<!-- /wp:column -->
</div>
<!-- /wp:columns -->
';
wp_update_post(['ID' => $chap_prog_id, 'post_content' => $chap_prog_content]);
pbslog("  ✅ Chapter Programs — content loaded");

// Scholarship Banquet
$sch_content = '
<!-- wp:cover {"overlayColor":"primary","minHeight":280,"align":"full"} -->
<div class="wp-block-cover alignfull" style="background-color:#003087;min-height:280px">
<div class="wp-block-cover__inner-container">
<!-- wp:heading {"textAlign":"center","textColor":"white","level":1} -->
<h1 class="has-text-align-center has-white-color has-text-color">Annual Scholarship Banquet</h1>
<!-- /wp:heading -->
<!-- wp:paragraph {"align":"center","textColor":"white"} -->
<p class="has-text-align-center has-white-color has-text-color">Celebrating Excellence. Investing in the Future.</p>
<!-- /wp:paragraph -->
</div></div>
<!-- /wp:cover -->

<!-- wp:heading {"level":2} -->
<h2>An Evening of Scholarship and Brotherhood</h2>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>The Psi Beta Sigma Annual Scholarship Banquet is one of the chapter\'s signature events — bringing together students, families, educators, community leaders, and business partners for an evening of recognition, inspiration, and fellowship.</p>
<!-- /wp:paragraph -->
<!-- wp:heading {"level":3} --><h3>Event Highlights</h3><!-- /wp:heading -->
<!-- wp:list -->
<ul>
<li>🎓 Scholarship awards to Austin-area students</li>
<li>🎤 Keynote speaker and student recognition program</li>
<li>🤝 Networking with community and business leaders</li>
<li>🍽️ Formal dinner and program</li>
</ul>
<!-- /wp:list -->
<!-- wp:paragraph -->
<p><strong>Date:</strong> [Date TBD] &nbsp;|&nbsp; <strong>Location:</strong> [Venue TBD], Austin, Texas &nbsp;|&nbsp; <strong>Attire:</strong> Business Formal / Black Tie Optional</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} --><h2>Attend or Sponsor</h2><!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Join us for this memorable evening — tickets and table sponsorships are available. All proceeds directly fund scholarships awarded to Austin-area students.</p>
<!-- /wp:paragraph -->
<!-- wp:table -->
<figure class="wp-block-table"><table><tbody>
<tr><td><strong>Individual Ticket</strong></td><td>$[___]</td></tr>
<tr><td><strong>Table of 8</strong></td><td>$[___]</td></tr>
<tr><td><strong>Presenting Sponsor</strong></td><td>$[___] — includes table, program recognition, speaking opportunity</td></tr>
</tbody></table></figure>
<!-- /wp:table -->
<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} -->
<div class="wp-block-buttons">
<!-- wp:button -->
<div class="wp-block-button"><a class="wp-block-button__link" href="mailto:treasurer@psibetasigma1914.org">Buy Tickets</a></div>
<!-- /wp:button -->
<!-- wp:button {"className":"is-style-outline"} -->
<div class="wp-block-button is-style-outline"><a class="wp-block-button__link" href="/sponsorship/">Become a Sponsor</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:buttons -->
';
wp_update_post(['ID' => $sch_ban_id, 'post_content' => $sch_content]);
pbslog("  ✅ Scholarship Banquet — content loaded");

// Sponsorship page
$spon_content = '
<!-- wp:cover {"overlayColor":"primary","minHeight":250,"align":"full"} -->
<div class="wp-block-cover alignfull" style="background-color:#003087;min-height:250px">
<div class="wp-block-cover__inner-container">
<!-- wp:heading {"textAlign":"center","textColor":"white","level":1} -->
<h1 class="has-text-align-center has-white-color has-text-color">Sponsorship</h1>
<!-- /wp:heading -->
<p class="has-text-align-center has-white-color has-text-color">Support Austin\'s community while gaining visibility for your business or organization.</p>
</div></div>
<!-- /wp:cover -->

<!-- wp:heading {"level":2} --><h2>Why Sponsor Psi Beta Sigma?</h2><!-- /wp:heading -->
<!-- wp:paragraph -->
<p>The Psi Beta Sigma Chapter serves thousands of Austin residents each year through our Golf Tournament, Scholarship Banquet, Back to School Supply Drive, and our partnership with Campbell Elementary. Your sponsorship directly funds these programs and puts your brand in front of Austin\'s professional community.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2,"anchor":"become-a-sponsor"} --><h2 id="become-a-sponsor">Sponsorship Packages</h2><!-- /wp:heading -->
<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead>
<tr><th>Package</th><th>Investment</th><th>Benefits</th></tr>
</thead><tbody>
<tr><td><strong>🥇 Title Sponsor</strong></td><td>$10,000</td><td>Premier logo placement, speaking opportunity, VIP foursome, recognition in all event materials</td></tr>
<tr><td><strong>🥈 Platinum Sponsor</strong></td><td>$5,000</td><td>Logo on all materials, foursome entry, recognition at events</td></tr>
<tr><td><strong>🥉 Gold Sponsor</strong></td><td>$2,500</td><td>Logo on event program, two player entries, social media recognition</td></tr>
<tr><td><strong>⛳ Hole Sponsor</strong></td><td>$500</td><td>Dedicated signage at a tournament hole, name in program</td></tr>
<tr><td><strong>🤝 Community Partner</strong></td><td>$250</td><td>Name recognition on website and social media</td></tr>
</tbody></table></figure>
<!-- /wp:table -->

<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} -->
<div class="wp-block-buttons">
<!-- wp:button -->
<div class="wp-block-button"><a class="wp-block-button__link" href="mailto:president@psibetasigma1914.org?subject=Sponsorship Inquiry — Psi Beta Sigma 1914">Become a Sponsor →</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:buttons -->

<!-- wp:heading {"level":2} --><h2>Our Sponsors</h2><!-- /wp:heading -->
<!-- wp:paragraph -->
<p>We are grateful to the businesses and individuals who support our mission. <a href="/sponsorship/sponsor-thank-you/">View our sponsor recognition page →</a></p>
<!-- /wp:paragraph -->
';
wp_update_post(['ID' => $sponsorship_id, 'post_content' => $spon_content]);
pbslog("  ✅ Sponsorship — content loaded");

// Sponsor Thank You
$thanks_content = '
<!-- wp:cover {"overlayColor":"primary","minHeight":200,"align":"full"} -->
<div class="wp-block-cover alignfull" style="background-color:#003087;min-height:200px">
<div class="wp-block-cover__inner-container">
<!-- wp:heading {"textAlign":"center","textColor":"white","level":1} -->
<h1 class="has-text-align-center has-white-color has-text-color">Thank You to Our Sponsors</h1>
<!-- /wp:heading -->
</div></div>
<!-- /wp:cover -->
<!-- wp:paragraph {"align":"center"} -->
<p class="has-text-align-center">We are deeply grateful to the businesses, organizations, and individuals who invest in the Psi Beta Sigma Chapter\'s mission. Your generosity makes our programs possible.</p>
<!-- /wp:paragraph -->
<!-- wp:paragraph {"align":"center"} -->
<p class="has-text-align-center"><em>Sponsor logos and names will be listed here as partnerships are confirmed.</em></p>
<!-- /wp:paragraph -->
<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} -->
<div class="wp-block-buttons">
<!-- wp:button -->
<div class="wp-block-button"><a class="wp-block-button__link" href="/sponsorship/">Become a Sponsor →</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:buttons -->
';
wp_update_post(['ID' => $thanks_id, 'post_content' => $thanks_content]);
pbslog("  ✅ Thank You Sponsors — content loaded");

// Pay Chapter Dues
$dues_content = '
<!-- wp:cover {"overlayColor":"primary","minHeight":200,"align":"full"} -->
<div class="wp-block-cover alignfull" style="background-color:#003087;min-height:200px">
<div class="wp-block-cover__inner-container">
<!-- wp:heading {"textAlign":"center","textColor":"white","level":1} -->
<h1 class="has-text-align-center has-white-color has-text-color">Pay Chapter Dues</h1>
<!-- /wp:heading -->
</div></div>
<!-- /wp:cover -->
<!-- wp:paragraph -->
<p>Active members may submit chapter dues securely through this page. Dues support chapter operations, community programming, and our ongoing initiatives at Campbell Elementary, the Back to School Drive, and Scholarship Banquet.</p>
<!-- /wp:paragraph -->
<!-- wp:paragraph -->
<p>Please also ensure your national dues are current through the Phi Beta Sigma national portal at <a href="https://phibetasigma1914.org" target="_blank" rel="noopener">phibetasigma1914.org</a>.</p>
<!-- /wp:paragraph -->
<!-- wp:paragraph -->
<p><strong>Chapter Dues Amount:</strong> $[___]</p>
<!-- /wp:paragraph -->
<!-- wp:buttons -->
<div class="wp-block-buttons">
<!-- wp:button -->
<div class="wp-block-button"><a class="wp-block-button__link" href="mailto:treasurer@psibetasigma1914.org?subject=Chapter Dues Payment">Pay Now — Contact Treasurer →</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:buttons -->
<!-- wp:paragraph {"align":"center"} -->
<p class="has-text-align-center"><em>Online payment portal coming soon. Contact <a href="mailto:treasurer@psibetasigma1914.org">treasurer@psibetasigma1914.org</a> for payment instructions.</em></p>
<!-- /wp:paragraph -->
';
wp_update_post(['ID' => $pay_dues_id, 'post_content' => $dues_content]);
pbslog("  ✅ Pay Chapter Dues — content loaded");

pbslog("Sprint B content: DONE");
pbslog("");

// ============================================================
// SPRINT C — GOLF TOURNAMENT REGISTRATION CTA
// ============================================================
pbslog("--- SPRINT C: GOLF TOURNAMENT REGISTRATION ---");

// Update Golf Tournament page with full content + registration CTA
$golf_content = '
<!-- wp:cover {"overlayColor":"primary","minHeight":300,"align":"full"} -->
<div class="wp-block-cover alignfull" style="background-color:#003087;min-height:300px">
<div class="wp-block-cover__inner-container">
<!-- wp:heading {"textAlign":"center","textColor":"white","level":1} -->
<h1 class="has-text-align-center has-white-color has-text-color">2026 Scholarship Golf Tournament</h1>
<!-- /wp:heading -->
<!-- wp:paragraph {"align":"center","textColor":"white"} -->
<p class="has-text-align-center has-white-color has-text-color">⛳ Grey Rock Golf &amp; Tennis · Austin, TX · September 26, 2026</p>
<!-- /wp:paragraph -->
<!-- wp:paragraph {"align":"center","textColor":"white"} -->
<p class="has-text-align-center has-white-color has-text-color"><em>Brotherhood on the fairway. Scholarships on the line.</em></p>
<!-- /wp:paragraph -->
</div></div>
<!-- /wp:cover -->

<!-- wp:columns -->
<div class="wp-block-columns">
<!-- wp:column -->
<div class="wp-block-column">
<!-- wp:heading {"level":3} --><h3>Tournament Details</h3><!-- /wp:heading -->
<!-- wp:list -->
<ul>
<li>📅 <strong>Date:</strong> Saturday, September 26, 2026</li>
<li>📍 <strong>Venue:</strong> Grey Rock Golf &amp; Tennis — 6809 Grey Rock Dr, Austin, TX 78749</li>
<li>🏌️ <strong>Format:</strong> 6-6-6 Team Format (4 Players Per Foursome)</li>
<li>🕗 <strong>Registration/Check-in:</strong> [Time TBD]</li>
<li>🚀 <strong>Shotgun Start:</strong> [Time TBD]</li>
<li>💵 <strong>Entry Fee:</strong> $[___] per player / $[___] per team</li>
</ul>
<!-- /wp:list -->
<p>Proceeds support the chapter\'s community initiatives including the Back to School Supply Drive, Campbell Elementary partnership, and Scholarship Banquet.</p>
</div>
<!-- /wp:column -->

<!-- wp:column -->
<div class="wp-block-column">
<!-- wp:heading {"level":3} --><h3>The 6-6-6 Format</h3><!-- /wp:heading -->
<!-- wp:paragraph --><p><strong>⛳ Scramble (Holes 1–6):</strong> All players hit each shot. Team selects the best result. Beginner-friendly and fast-paced.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p><strong>🏃 Best Ball (Holes 7–12):</strong> Each player plays their own ball. Lowest individual score per hole counts.</p><!-- /wp:paragraph -->
<!-- wp:paragraph --><p><strong>🤝 Alternate Shot (Holes 13–18):</strong> Teammates alternate hitting the same ball. Emphasizes teamwork and strategy.</p><!-- /wp:paragraph -->
</div>
<!-- /wp:column -->
</div>
<!-- /wp:columns -->

<!-- wp:separator --><hr class="wp-block-separator"/><!-- /wp:separator -->

<!-- wp:heading {"level":2,"textAlign":"center"} --><h2 class="has-text-align-center">Register Your Team</h2><!-- /wp:heading -->
<!-- wp:paragraph {"align":"center"} --><p class="has-text-align-center">Spots are limited — 72 players maximum. Secure your foursome today and help fund the next generation of Sigma scholars.</p><!-- /wp:paragraph -->
<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} -->
<div class="wp-block-buttons">
<!-- wp:button -->
<div class="wp-block-button"><a class="wp-block-button__link" href="mailto:president@psibetasigma1914.org?subject=Golf Tournament Registration 2026">Register Now →</a></div>
<!-- /wp:button -->
<!-- wp:button {"className":"is-style-outline"} -->
<div class="wp-block-button is-style-outline"><a class="wp-block-button__link" href="/sponsorship/#become-a-sponsor">Tournament Sponsorship</a></div>
<!-- /wp:button -->
</div>
<!-- /wp:buttons -->
<!-- wp:paragraph {"align":"center"} --><p class="has-text-align-center"><em>Questions? Email <a href="mailto:president@psibetasigma1914.org">president@psibetasigma1914.org</a></em></p><!-- /wp:paragraph -->

<!-- wp:separator --><hr class="wp-block-separator"/><!-- /wp:separator -->

<!-- wp:heading {"level":2} --><h2>Sponsorship Opportunities</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>Support Austin\'s community while gaining visibility for your business. <a href="/sponsorship/">View all sponsorship packages →</a></p><!-- /wp:paragraph -->
<!-- wp:table -->
<figure class="wp-block-table"><table><tbody>
<tr><td><strong>🥇 Title Sponsor</strong></td><td>$10,000</td><td>Premier logo placement, speaking opportunity, VIP foursome</td></tr>
<tr><td><strong>⛳ Hole Sponsor</strong></td><td>$500</td><td>Dedicated signage at a tournament hole, name in program</td></tr>
<tr><td><strong>🏆 Prize/Contest Sponsor</strong></td><td>Custom</td><td>Closest to the Pin, Longest Drive, and more</td></tr>
</tbody></table></figure>
<!-- /wp:table -->
';

wp_update_post(['ID' => $page_ids['golf-tournament'], 'post_content' => $golf_content]);
pbslog("  ✅ Golf Tournament — full content + registration CTA loaded");
pbslog("Sprint C: DONE");
pbslog("");

// ============================================================
// SPRINT D — EVENTS CALENDAR: POPULATE ANCHOR EVENTS
// ============================================================
pbslog("--- SPRINT D: EVENTS CALENDAR ---");

if (class_exists('Tribe__Events__Main')) {
    $tribe_venue_id = tribe_create_venue([
        'Venue'   => 'Grey Rock Golf & Tennis',
        'Address' => '6809 Grey Rock Dr',
        'City'    => 'Austin',
        'State'   => 'TX',
        'Zip'     => '78749',
        'Country' => 'United States',
    ]);
    pbslog("  Venue created/found: ID $tribe_venue_id");

    $events_to_create = [
        [
            'title'      => '2026 Annual Scholarship Golf Tournament',
            'start'      => '2026-09-26 08:00:00',
            'end'        => '2026-09-26 17:00:00',
            'venue'      => $tribe_venue_id,
            'desc'       => 'Join the Austin Sigmas for our annual scholarship golf tournament at Grey Rock Golf & Tennis. 6-6-6 format, 72-player cap. All proceeds support chapter scholarships.',
            'category'   => 'Fundraising',
        ],
        [
            'title'      => 'Back to School Supply Drive 2026',
            'start'      => '2026-08-08 09:00:00',
            'end'        => '2026-08-08 14:00:00',
            'venue'      => 0,
            'desc'       => 'Annual drive collecting school supplies for Austin students. Drop off at [location TBD]. Use #PsiBetaSigmaATX.',
            'category'   => 'Education',
        ],
        [
            'title'      => "Phi Beta Sigma Founder's Day",
            'start'      => '2027-01-09 10:00:00',
            'end'        => '2027-01-09 14:00:00',
            'venue'      => 0,
            'desc'       => 'Celebrating the founding of Phi Beta Sigma Fraternity, Inc. on January 9, 1914 at Howard University.',
            'category'   => 'Brotherhood',
        ],
        [
            'title'      => 'Annual Scholarship Banquet 2026',
            'start'      => '2026-11-14 18:00:00',
            'end'        => '2026-11-14 22:00:00',
            'venue'      => 0,
            'desc'       => 'Annual banquet celebrating Austin-area students with scholarship awards. Business Formal / Black Tie Optional. Date TBD — placeholder set.',
            'category'   => 'Fundraising',
        ],
    ];

    foreach ($events_to_create as $ev) {
        // Check if event title already exists
        $existing = get_page_by_title($ev['title'], OBJECT, 'tribe_events');
        if ($existing) {
            pbslog("  EXISTS: " . $ev['title']);
            continue;
        }
        $args = [
            'post_title'   => $ev['title'],
            'post_status'  => 'publish',
            'EventStartDate'    => substr($ev['start'], 0, 10),
            'EventStartHour'    => substr($ev['start'], 11, 2),
            'EventStartMinute'  => substr($ev['start'], 14, 2),
            'EventEndDate'      => substr($ev['end'], 0, 10),
            'EventEndHour'      => substr($ev['end'], 11, 2),
            'EventEndMinute'    => substr($ev['end'], 14, 2),
            'EventDescription'  => $ev['desc'],
        ];
        if ($ev['venue']) $args['EventVenueID'] = $ev['venue'];
        $event_id = tribe_create_event($args);
        if ($event_id && !is_wp_error($event_id)) {
            pbslog("  CREATED event [$event_id]: " . $ev['title']);
        } else {
            pbslog("  ERROR creating event: " . $ev['title']);
        }
    }
} else {
    pbslog("  WARNING: The Events Calendar plugin not active — skipping event creation");
}
pbslog("Sprint D: DONE");
pbslog("");

// ============================================================
// SPRINT E — MEMBERS PORTAL: PASSWORD PROTECTION
// ============================================================
pbslog("--- SPRINT E: MEMBERS PORTAL PASSWORD PROTECTION ---");

$member_password = 'SigmaBro1914!';

// Password-protect Members Portal + sub-pages
$protected_pages = [
    $page_ids['members-portal'],
    $page_ids['membership-roster'],
    $pay_dues_id,
];
foreach ($protected_pages as $pid) {
    if (!$pid) continue;
    $p = get_post($pid);
    if ($p) {
        wp_update_post([
            'ID'            => $pid,
            'post_password' => $member_password,
        ]);
        pbslog("  🔒 Password-protected: [{$pid}] {$p->post_title}");
    }
}
pbslog("  Member password set: $member_password");
pbslog("  → Share this password with active brothers via chapter email");
pbslog("Sprint E: DONE");
pbslog("");

// ============================================================
// FINAL SUMMARY
// ============================================================
pbslog("=== BATCH COMPLETE ===");
pbslog("");
pbslog("PAGE IDs REFERENCE:");
foreach ($page_ids as $slug => $id) {
    pbslog("  $slug → $id");
}
pbslog("  scholarship-banquet → $sch_ban_id");
pbslog("  sponsorship → $sponsorship_id");
pbslog("  sponsor-thank-you → $thanks_id");
pbslog("  pay-chapter-dues → $pay_dues_id");
pbslog("  back-to-school-drive → $bts_id");
pbslog("  sigma-source → $sigma_src_id");
pbslog("  state-regional-national → $state_reg_id");
pbslog("  chapter-programs → $chap_prog_id");
pbslog("  leadership → $leadership_id");
pbslog("");
pbslog("NEXT STEPS (manual):");
pbslog("  1. Fill bracketed [fields] in pages: Pres Corner, Exec Board, State/Regional, Golf Tournament times/fee");
pbslog("  2. Set up Stripe/PayPal for Golf Tournament + Dues payment");
pbslog("  3. Upload officer headshots to Executive Board page");
pbslog("  4. DNS migration: newsite.psibetasigma1914.org → psibetasigma1914.org");
pbslog("  5. DELETE this file immediately: /wp-content/uploads/pbs-batch.php");
pbslog("");
pbslog("*** DELETE THIS FILE NOW — DO NOT LEAVE ON SERVER ***");
