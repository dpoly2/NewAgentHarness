/**
 * XFTC Membership Plugin — Public JS
 * Handles: registration form, login, meet registration AJAX, chart loading
 */
(function ($) {
    'use strict';

    const ajax = xftcPublic.ajaxUrl;
    const nonce = xftcPublic.nonce;

    // ── Utility ─────────────────────────────────────────────────────────────
    function showFeedback($el, msg, type) {
        $el.html('<div class="ts-notice ts-notice--' + type + '">' + msg + '</div>');
    }

    function serializeFormObj($form) {
        const data = {};
        $form.serializeArray().forEach(function (f) { data[f.name] = f.value; });
        return data;
    }

    // ── Multi-step Registration Form ─────────────────────────────────────────
    const $regForm = $('#ts-register-form');
    if ($regForm.length) {
        let currentStep = 1;
        const totalSteps = $regForm.find('.ts-form__step').length;

        function showStep(step) {
            $regForm.find('.ts-form__step').hide();
            $regForm.find('[data-step="' + step + '"]').show();
            currentStep = step;
        }

        // Next step
        $regForm.on('click', '.ts-next-step', function () {
            const $step = $regForm.find('[data-step="' + currentStep + '"]');

            // Basic validation
            let valid = true;
            $step.find('[required]').each(function () {
                if (!$(this).val().trim()) {
                    $(this).addClass('is-invalid');
                    valid = false;
                } else {
                    $(this).removeClass('is-invalid');
                }
            });

            // Password match check on step 1
            if (currentStep === 1) {
                const pw1 = $('#reg_password').val();
                const pw2 = $('#reg_password2').val();
                if (pw1 !== pw2) {
                    showFeedback($regForm.find('.ts-form__feedback'), 'Passwords do not match.', 'error');
                    valid = false;
                }
            }

            if (!valid) return;

            // Populate review summary on last step
            if (currentStep === totalSteps - 1) {
                buildReviewSummary();
            }

            showStep(currentStep + 1);
            window.scrollTo({ top: $regForm.offset().top - 100, behavior: 'smooth' });
        });

        // Prev step
        $regForm.on('click', '.ts-prev-step', function () {
            showStep(currentStep - 1);
        });

        // Build review summary
        function buildReviewSummary() {
            const d = serializeFormObj($regForm);
            const tier = $regForm.find('[name="tier"]:checked').val() || 'standard';
            const html = [
                ['Parent Name', (d.parent_first || '') + ' ' + (d.parent_last || '')],
                ['Email', d.parent_email || ''],
                ['Athlete', (d.athlete_first || '') + ' ' + (d.athlete_last || '')],
                ['Team Level', d.team_level || 'Not selected'],
                ['Membership Tier', tier.charAt(0).toUpperCase() + tier.slice(1)],
            ].map(function (r) {
                return '<div class="ts-review-summary__row"><span>' + r[0] + '</span><strong>' + r[1] + '</strong></div>';
            }).join('');
            $('#ts-review-summary').html(html);
        }

        // Submit
        $regForm.on('submit', function (e) {
            e.preventDefault();
            const $btn = $('#ts-submit-btn');
            const $fb  = $regForm.find('.ts-form__feedback');

            $btn.prop('disabled', true).text('Registering…');

            $.post(ajax, $regForm.serialize() + '&TRACKSUITE_nonce=' + nonce, function (res) {
                if (res.success) {
                    showFeedback($fb, res.data.message, 'success');
                    setTimeout(function () {
                        window.location.href = res.data.redirect || xftcPublic.portalUrl;
                    }, 1200);
                } else {
                    showFeedback($fb, res.data.message || 'An error occurred.', 'error');
                    $btn.prop('disabled', false).text('Complete Registration');
                }
            }).fail(function () {
                showFeedback($fb, 'Server error. Please try again.', 'error');
                $btn.prop('disabled', false).text('Complete Registration');
            });
        });
    }

    // ── Login Form ──────────────────────────────────────────────────────────
    $('#ts-login-form').on('submit', function (e) {
        e.preventDefault();
        const $form = $(this);
        const $fb   = $form.find('.ts-form__feedback');
        const $btn  = $form.find('[type="submit"]');

        $btn.prop('disabled', true).text('Logging in…');

        $.post(ajax, $form.serialize() + '&TRACKSUITE_nonce=' + nonce, function (res) {
            if (res.success) {
                showFeedback($fb, 'Logged in! Redirecting…', 'success');
                setTimeout(function () {
                    window.location.href = res.data.redirect || xftcPublic.portalUrl;
                }, 800);
            } else {
                showFeedback($fb, res.data.message || 'Login failed.', 'error');
                $btn.prop('disabled', false).text('Log In');
            }
        }).fail(function () {
            showFeedback($fb, 'Server error.', 'error');
            $btn.prop('disabled', false).text('Log In');
        });
    });

    // ── Meet Registration Button ─────────────────────────────────────────────
    $(document).on('click', '.ts-register-meet-btn', function () {
        if (!xftcPublic.isLoggedIn) {
            window.location.href = xftcPublic.portalUrl;
            return;
        }

        const $btn      = $(this);
        const meetId    = $btn.data('meet-id');
        const meetName  = $btn.data('meet-name');
        const athleteId = $btn.data('athlete-id') || 0;

        // If no athlete ID — prompt selection or just confirm
        const confirmMsg = athleteId
            ? 'Register your athlete for "' + meetName + '"?'
            : 'Register for "' + meetName + '"?';

        if (!confirm(confirmMsg)) return;

        $btn.prop('disabled', true).text('Registering…');

        $.post(ajax, {
            action:     'TRACKSUITE_register_for_meet',
            TRACKSUITE_nonce: nonce,
            meet_id:    meetId,
            athlete_id: athleteId,
        }, function (res) {
            if (res.success) {
                $btn.text('✅ Registered').css('background', '#28a745');
                // Show inline confirmation
                const $notice = $('<div class="ts-notice ts-notice--success" style="margin-top:.5rem">' + res.data.message + '</div>');
                $btn.closest('.ts-meet-card').append($notice);
            } else {
                alert(res.data.message || 'Registration failed.');
                $btn.prop('disabled', false).text('Register');
            }
        }).fail(function () {
            alert('Server error. Please try again.');
            $btn.prop('disabled', false).text('Register');
        });
    });

    // ── Results Chart (Chart.js) ─────────────────────────────────────────────
    function initResultsChart() {
        const canvas = document.getElementById('ts-results-chart');
        if (!canvas || typeof Chart === 'undefined') return;

        const raw = canvas.dataset.chartData;
        if (!raw) return;

        let data;
        try { data = JSON.parse(raw); } catch (e) { return; }
        if (!data.labels || !data.labels.length) return;

        // Determine if time event (lower = better, reverse Y axis)
        const isTime = (data.values || []).some(v => String(v).includes(':'));

        new Chart(canvas, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: data.event || 'Performance',
                    data: data.values,
                    borderColor: '#F5A623',
                    backgroundColor: 'rgba(245,166,35,.1)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: data.is_pb
                        ? data.is_pb.map(pb => pb ? '#28a745' : '#F5A623')
                        : '#F5A623',
                    pointRadius: 6,
                    pointHoverRadius: 8,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            afterLabel: function (ctx) {
                                return data.is_pb && data.is_pb[ctx.dataIndex] ? '⚡ Personal Best' : '';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        reverse: isTime,
                        grid: { color: 'rgba(0,0,0,.06)' },
                        ticks: { font: { family: 'Inter, sans-serif', size: 11 } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: 'Inter, sans-serif', size: 11 } }
                    }
                }
            }
        });
    }

    // Load Chart.js on demand for results pages
    if (document.getElementById('ts-results-chart')) {
        if (typeof Chart !== 'undefined') {
            initResultsChart();
        } else {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
            script.onload = initResultsChart;
            document.head.appendChild(script);
        }
    }

    // ── Event selector for chart (portal results view) ───────────────────────
    $(document).on('change', '#ts-event-selector', function () {
        const athleteId = $(this).data('athlete-id');
        const event     = $(this).val();
        if (!athleteId || !event) return;

        $.post(ajax, {
            action:     'TRACKSUITE_get_chart_data',
            TRACKSUITE_nonce: nonce,
            athlete_id: athleteId,
            event:      event,
        }, function (res) {
            if (res.success) {
                // Update the canvas data and re-init
                const canvas = document.getElementById('ts-results-chart');
                if (canvas) {
                    canvas.dataset.chartData = JSON.stringify(res.data);
                    // Destroy existing chart instance
                    const existing = Chart.getChart(canvas);
                    if (existing) existing.destroy();
                    initResultsChart();
                }
            }
        });
    });

}(jQuery));

