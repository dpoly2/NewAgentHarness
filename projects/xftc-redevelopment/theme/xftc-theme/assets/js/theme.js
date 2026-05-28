/**
 * XFTC Track & Field Theme — Main JS
 * @package TRACKSUITE_Theme
 */
(function ($) {
    'use strict';

    // ── Mobile Nav Toggle ────────────────────────────────────────────────────
    const navToggle = document.querySelector('.nav-toggle');
    const navPrimary = document.querySelector('.nav-primary');

    if (navToggle && navPrimary) {
        navToggle.addEventListener('click', function () {
            const isOpen = navPrimary.classList.toggle('is-open');
            navToggle.setAttribute('aria-expanded', isOpen);
            document.body.classList.toggle('nav-open', isOpen);
        });

        // Close on outside click
        document.addEventListener('click', function (e) {
            if (!navToggle.contains(e.target) && !navPrimary.contains(e.target)) {
                navPrimary.classList.remove('is-open');
                navToggle.setAttribute('aria-expanded', 'false');
                document.body.classList.remove('nav-open');
            }
        });

        // Close on Escape
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                navPrimary.classList.remove('is-open');
                navToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // ── Portal Tabs ──────────────────────────────────────────────────────────
    function initTabs() {
        const tabs = document.querySelectorAll('.portal-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', function () {
                const panel = this.dataset.tab;

                // Deactivate all tabs
                tabs.forEach(t => t.classList.remove('is-active'));
                document.querySelectorAll('.tab-panel, [id^="tab-"]').forEach(p => {
                    p.style.display = 'none';
                });

                // Activate clicked
                this.classList.add('is-active');
                const target = document.getElementById('tab-' + panel);
                if (target) target.style.display = 'block';
            });
        });
    }
    initTabs();

    // ── Schedule Filters ─────────────────────────────────────────────────────
    function initScheduleFilters() {
        const filterBtns = document.querySelectorAll('.schedule-filter-btn');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', function () {
                filterBtns.forEach(b => b.classList.remove('is-active'));
                this.classList.add('is-active');

                const filter = this.dataset.filter;
                const items = document.querySelectorAll('.meet-card, .schedule-item');

                items.forEach(item => {
                    if (filter === 'all') {
                        item.style.display = '';
                    } else {
                        const matchType = item.dataset.type === filter;
                        const matchStatus = item.dataset.status === filter;
                        item.style.display = (matchType || matchStatus) ? '' : 'none';
                    }
                });
            });
        });
    }
    initScheduleFilters();

    // ── Roster Filters ───────────────────────────────────────────────────────
    function initRosterFilters() {
        const filterBtns = document.querySelectorAll('[data-filter]');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', function () {
                const group = this.closest('.schedule-filters');
                if (!group) return;

                group.querySelectorAll('[data-filter]').forEach(b => b.classList.remove('is-active'));
                this.classList.add('is-active');

                const filter = this.dataset.filter;
                const cards = document.querySelectorAll('.athlete-card');

                cards.forEach(card => {
                    if (filter === 'all') {
                        card.style.display = '';
                    } else {
                        card.style.display = card.dataset.division === filter ? '' : 'none';
                    }
                });
            });
        });
    }
    initRosterFilters();

    // ── Sticky Header shadow on scroll ──────────────────────────────────────
    const header = document.querySelector('.site-header');
    if (header) {
        window.addEventListener('scroll', function () {
            header.classList.toggle('is-scrolled', window.scrollY > 10);
        }, { passive: true });
    }

    // ── Smooth scroll for anchor links ──────────────────────────────────────
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // ── Results chart init (Chart.js — if present) ──────────────────────────
    function initResultsChart() {
        const canvas = document.getElementById('ts-results-chart');
        if (!canvas || typeof Chart === 'undefined') return;

        const rawData = canvas.dataset.chartData;
        if (!rawData) return;

        try {
            const data = JSON.parse(rawData);
            new Chart(canvas, {
                type: 'line',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'Performance',
                        data: data.values || [],
                        borderColor: '#F5A623',
                        backgroundColor: 'rgba(245, 166, 35, 0.12)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#F5A623',
                        pointRadius: 5,
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: ctx => ctx.parsed.y
                            }
                        }
                    },
                    scales: {
                        y: {
                            reverse: data.reverse || false, // lower is better for times
                            grid: { color: 'rgba(0,0,0,.06)' },
                            ticks: { font: { family: 'Inter' } }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { font: { family: 'Inter' } }
                        }
                    }
                }
            });
        } catch (err) {
            console.warn('XFTC Chart init failed:', err);
        }
    }
    initResultsChart();

    // ── Print button (results/roster pages) ─────────────────────────────────
    document.querySelectorAll('[data-print]').forEach(btn => {
        btn.addEventListener('click', () => window.print());
    });

    // ── Flash message auto-dismiss ───────────────────────────────────────────
    document.querySelectorAll('.ts-notice[data-auto-dismiss]').forEach(notice => {
        const delay = parseInt(notice.dataset.autoDismiss, 10) || 4000;
        setTimeout(() => {
            notice.style.opacity = '0';
            notice.style.transition = 'opacity .4s';
            setTimeout(() => notice.remove(), 400);
        }, delay);
    });

}(jQuery));

