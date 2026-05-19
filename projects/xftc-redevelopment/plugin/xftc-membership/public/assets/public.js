/* XFTC Membership — Public JavaScript */
(function ($) {
    'use strict';

    // ── Registration Form ─────────────────────────────────────────────────────
    $('#xftc-register-form').on('submit', function (e) {
        e.preventDefault();

        var $btn = $('#xftc-register-btn');
        var $msg = $('#xftc-register-message');
        var pass  = $('#xftc_password').val();
        var conf  = $('#xftc_password_confirm').val();

        if (pass !== conf) {
            xftcShowMessage($msg, 'error', 'Passwords do not match.');
            return;
        }

        $btn.prop('disabled', true).text('Creating account…');

        $.post(xftcPublic.ajaxUrl, {
            action:     'xftc_register_parent',
            nonce:      xftcPublic.registerNonce,
            first_name: $('#xftc_first_name').val(),
            last_name:  $('#xftc_last_name').val(),
            email:      $('#xftc_email').val(),
            phone:      $('#xftc_phone').val(),
            password:   pass,
        })
        .done(function (res) {
            if (res.success) {
                xftcShowMessage($msg, 'success', res.data.message);
                $('#xftc-register-form')[0].reset();
                setTimeout(function () { window.location.href = '/member-portal/'; }, 2000);
            } else {
                xftcShowMessage($msg, 'error', res.data.message);
            }
        })
        .fail(function () {
            xftcShowMessage($msg, 'error', 'Something went wrong. Please try again.');
        })
        .always(function () {
            $btn.prop('disabled', false).text('Create Account');
        });
    });

    // ── Add Athlete Modal ─────────────────────────────────────────────────────
    $(document).on('click', '#xftc-add-athlete-btn, #xftc-add-athlete-btn-2', function () {
        $('#xftc-add-athlete-modal').fadeIn(200);
    });

    $(document).on('click', '.xftc-modal-close', function () {
        $(this).closest('.xftc-modal').fadeOut(200);
    });

    // Close modal on outside click
    $(document).on('click', '.xftc-modal', function (e) {
        if ($(e.target).hasClass('xftc-modal')) {
            $(this).fadeOut(200);
        }
    });

    // ── Add Athlete Form ──────────────────────────────────────────────────────
    $('#xftc-add-athlete-form').on('submit', function (e) {
        e.preventDefault();

        var $msg  = $('#xftc-add-athlete-message');
        var $btn  = $(this).find('button[type=submit]');
        var data  = $(this).serializeArray().reduce(function (obj, item) {
            obj[item.name] = item.value;
            return obj;
        }, {});

        $btn.prop('disabled', true).text('Saving…');

        $.post(xftcPublic.ajaxUrl, $.extend(data, {
            action: 'xftc_add_athlete',
            nonce:  xftcPublic.athleteNonce,
        }))
        .done(function (res) {
            if (res.success) {
                xftcShowMessage($msg, 'success', res.data.message);
                setTimeout(function () { location.reload(); }, 1500);
            } else {
                xftcShowMessage($msg, 'error', res.data.message);
            }
        })
        .fail(function () {
            xftcShowMessage($msg, 'error', 'Something went wrong. Please try again.');
        })
        .always(function () {
            $btn.prop('disabled', false).text('Save Athlete');
        });
    });

    // ── Season Registration ───────────────────────────────────────────────────
    $(document).on('click', '.xftc-register-for-season', function () {
        var athleteId = $(this).data('athlete-id');
        var seasonId  = $(this).data('season-id');
        var $btn      = $(this);

        if (!confirm('Register this athlete for the current season?')) return;

        $btn.prop('disabled', true).text('Registering…');

        $.post(xftcPublic.ajaxUrl, {
            action:     'xftc_register_membership',
            nonce:      xftcPublic.membershipNonce,
            athlete_id: athleteId,
            season_id:  seasonId,
            tier:       'standard',
        })
        .done(function (res) {
            if (res.success) {
                alert(res.data.message + ' Amount due: $' + parseFloat(res.data.amount_due).toFixed(2));
                location.reload();
            } else {
                alert(res.data.message);
            }
        })
        .fail(function () {
            alert('Something went wrong. Please try again.');
        })
        .always(function () {
            $btn.prop('disabled', false).text('Register for Season');
        });
    });

    // ── Utility ───────────────────────────────────────────────────────────────
    function xftcShowMessage($el, type, msg) {
        $el.removeClass('xftc-success xftc-error')
           .addClass('xftc-' + type)
           .html(msg)
           .fadeIn(200);
    }

}(jQuery));
