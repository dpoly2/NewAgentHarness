/**
 * XFTC Membership — Public JS (v2.0.0)
 * Handles: portal tab switching, registration AJAX, meet registration
 */
(function($) {
    'use strict';

    /* ══════════════════════════════════════════════════════════════════════
       PORTAL TABS — athlete card tab switching
       ════════════════════════════════════════════════════════════════════ */
    $(document).on('click', '.xftc-tab-btn', function() {
        var $btn   = $(this);
        var tabId  = $btn.data('tab');
        var $tabs  = $btn.closest('.xftc-tabs');

        // Update button states
        $tabs.find('.xftc-tab-btn').removeClass('xftc-tab-btn--active');
        $btn.addClass('xftc-tab-btn--active');

        // Update panel states
        $tabs.find('.xftc-tab-panel').removeClass('xftc-tab-panel--active');
        $('#' + tabId).addClass('xftc-tab-panel--active');
    });

    /* ══════════════════════════════════════════════════════════════════════
       REGISTRATION FORM — multi-step AJAX submit
       ════════════════════════════════════════════════════════════════════ */
    var $regForm  = $('#xftc-registration-form');
    var $steps    = $regForm.find('.xftc-step');
    var $progress = $regForm.find('.xftc-progress-bar__fill');
    var currentStep = 0;

    function showStep(n) {
        $steps.hide().eq(n).fadeIn(200);
        var pct = ((n + 1) / $steps.length) * 100;
        $progress.css('width', pct + '%');
        $regForm.find('.xftc-step-indicator').text('Step ' + (n + 1) + ' of ' + $steps.length);
    }

    $(document).on('click', '.xftc-next-step', function() {
        var $current = $steps.eq(currentStep);
        // Basic validation
        var valid = true;
        $current.find('[required]').each(function() {
            if (!$(this).val().trim()) {
                $(this).addClass('xftc-input--error');
                valid = false;
            } else {
                $(this).removeClass('xftc-input--error');
            }
        });
        if (!valid) {
            showError($current, 'Please fill in all required fields.');
            return;
        }
        currentStep++;
        showStep(currentStep);
    });

    $(document).on('click', '.xftc-prev-step', function() {
        if (currentStep > 0) { currentStep--; showStep(currentStep); }
    });

    $regForm.on('submit', function(e) {
        e.preventDefault();
        var $btn = $regForm.find('[type=submit]');
        $btn.prop('disabled', true).text('Submitting...');

        $.ajax({
            url:      xftc_vars.ajax_url,
            method:   'POST',
            data:     $regForm.serialize() + '&action=xftc_register&nonce=' + xftc_vars.nonce,
            dataType: 'json',
            success: function(res) {
                if (res.success) {
                    $regForm.html(
                        '<div class="xftc-success">' +
                        '<h3>✅ Registration Complete!</h3>' +
                        '<p>' + (res.data.message || 'Welcome to Xtreme Force Track Club!') + '</p>' +
                        (res.data.redirect ? '<p>Redirecting...</p>' : '') +
                        '</div>'
                    );
                    if (res.data.redirect) {
                        setTimeout(function() { window.location.href = res.data.redirect; }, 1500);
                    }
                } else {
                    showError($regForm, res.data.message || 'An error occurred. Please try again.');
                    $btn.prop('disabled', false).text('Submit Registration');
                }
            },
            error: function() {
                showError($regForm, 'Network error. Please check your connection and try again.');
                $btn.prop('disabled', false).text('Submit Registration');
            }
        });
    });

    /* ══════════════════════════════════════════════════════════════════════
       MEET REGISTRATION — inline AJAX
       ════════════════════════════════════════════════════════════════════ */
    $(document).on('click', '.xftc-register-meet-btn', function() {
        var $btn     = $(this);
        var meetId   = $btn.data('meet-id');
        var athleteId = $btn.data('athlete-id');

        $btn.prop('disabled', true).text('Registering...');

        $.ajax({
            url:      xftc_vars.ajax_url,
            method:   'POST',
            data: {
                action:     'xftc_register_meet',
                nonce:      xftc_vars.nonce,
                meet_id:    meetId,
                athlete_id: athleteId
            },
            dataType: 'json',
            success: function(res) {
                if (res.success) {
                    $btn.replaceWith('<span class="xftc-badge xftc-badge--green">✅ Registered</span>');
                } else {
                    $btn.prop('disabled', false).text('Register');
                    alert(res.data.message || 'Registration failed. Please try again.');
                }
            },
            error: function() {
                $btn.prop('disabled', false).text('Register');
                alert('Network error. Please try again.');
            }
        });
    });

    /* ══════════════════════════════════════════════════════════════════════
       UTILITIES
       ════════════════════════════════════════════════════════════════════ */
    function showError($el, msg) {
        $el.find('.xftc-form-error').remove();
        $el.prepend('<div class="xftc-form-error">' + msg + '</div>');
        $el[0].scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Init: show first step if multi-step form exists
    if ($steps.length) { showStep(0); }

})(jQuery);
