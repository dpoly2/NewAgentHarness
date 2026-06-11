/**
 * PBS Event Commerce — Checkout JS
 * Handles: qty selection, gateway switching, Stripe.js, Square Web Payments SDK, PayPal JS SDK
 */
(function($) {
    'use strict';

    const PBS = window.PBS_EC || {};

    /* ── Utility ────────────────────────────────────────────── */
    function formatCurrency(amount) {
        return '$' + parseFloat(amount).toFixed(2);
    }

    /* ── Qty controls + order total ─────────────────────────── */
    function initQtyControls($form) {
        function recalc() {
            let total = 0, ticketNames = [], totalQty = 0;

            $form.find('.pbs-qty-input').each(function() {
                const qty   = parseInt($(this).val()) || 0;
                const $item = $(this).closest('.pbs-ticket-item');
                const price = parseFloat($item.data('price')) || 0;
                const name  = $item.data('name');
                if (qty > 0) { total += price * qty; ticketNames.push(name); totalQty += qty; }
            });

            const $summary = $form.find('.pbs-order-summary, .pbs-donate-summary');
            if (total > 0) {
                $form.find('.pbs-order-total').text(formatCurrency(total));
                $form.find('.pbs-amount-input').val(total.toFixed(2));
                $form.find('.pbs-ticket-type-input').val(ticketNames.join(', '));
                $form.find('.pbs-quantity-input').val(totalQty);
                $summary.show();
            } else {
                $summary.hide();
            }
        }

        $form.on('click', '.pbs-qty-minus', function() {
            const $input = $(this).siblings('.pbs-qty-input');
            const val = Math.max(0, parseInt($input.val()) - 1);
            $input.val(val); recalc();
        });
        $form.on('click', '.pbs-qty-plus', function() {
            const $input = $(this).siblings('.pbs-qty-input');
            const max = parseInt($input.attr('max')) || 20;
            const val = Math.min(max, parseInt($input.val()) + 1);
            $input.val(val); recalc();
        });
        $form.on('change', '.pbs-qty-input', recalc);
    }

    /* ── Donation amount selector ───────────────────────────── */
    function initDonateWidget($form) {
        $form.on('click', '.pbs-amount-btn', function() {
            $form.find('.pbs-amount-btn').removeClass('active');
            $(this).addClass('active');
            const amt = $(this).data('amount');

            if (amt === 'custom') {
                $form.find('.pbs-custom-amount-wrap').show();
            } else {
                $form.find('.pbs-custom-amount-wrap').hide();
                $form.find('.pbs-amount-input').val(parseFloat(amt).toFixed(2));
                $form.find('.pbs-order-total').text(formatCurrency(amt));
                $form.find('.pbs-donate-summary').show();
            }
        });

        $form.on('input', '.pbs-custom-amount-input', function() {
            const amt = parseFloat($(this).val()) || 0;
            if (amt > 0) {
                $form.find('.pbs-amount-input').val(amt.toFixed(2));
                $form.find('.pbs-order-total').text(formatCurrency(amt));
                $form.find('.pbs-donate-summary').show();
            }
        });
    }

    /* ── Gateway tab switching ──────────────────────────────── */
    function initGatewayTabs($form) {
        $form.on('click', '.pbs-gateway-tab', function() {
            const gw = $(this).data('gateway');
            $form.find('.pbs-gateway-tab').removeClass('active');
            $(this).addClass('active');
            $form.find('.pbs-gateway-input').val(gw);
            $form.find('.pbs-payment-panel').hide();
            $form.find('.pbs-payment-panel[data-panel="' + gw + '"]').show();
        });
    }

    /* ── Stripe ─────────────────────────────────────────────── */
    let stripeInstances = {};

    function initStripe($container) {
        if (!PBS.stripe_pub_key || typeof Stripe === 'undefined') return;
        const eventId = $container.data('event');
        const stripe  = Stripe(PBS.stripe_pub_key);
        const elements = stripe.elements();
        const cardEl  = elements.create('card', {
            style: { base: { fontFamily: "'Open Sans', Arial, sans-serif", fontSize: '15px', color: '#1a1a1a' } }
        });

        const isDonate = $container.hasClass('pbs-donate-widget');
        const mountId = isDonate ? 'pbs-stripe-donate-' + eventId : 'pbs-stripe-card-' + eventId;
        const mountEl = document.getElementById(mountId) ||
                        $container.find('.pbs-stripe-card-element')[0];
        if (mountEl) {
            cardEl.mount(mountEl);
            cardEl.on('change', function(e) {
                $container.find('.pbs-card-errors').text(e.error ? e.error.message : '');
            });
        }
        stripeInstances[eventId] = { stripe, cardEl };
    }

    /* ── Square ─────────────────────────────────────────────── */
    let squareInstances = {};

    async function initSquare($container) {
        if (!PBS.square_app_id || typeof Square === 'undefined') return;
        const eventId = $container.data('event');
        try {
            const payments = Square.payments(PBS.square_app_id, PBS.square_location_id);
            const card = await payments.card();
            const isDonate = $container.hasClass('pbs-donate-widget');
            const mountId = isDonate ? 'pbs-square-donate-' + eventId : 'pbs-square-card-' + eventId;
            await card.attach('#' + mountId);
            squareInstances[eventId] = { payments, card };
        } catch(e) { console.warn('Square init failed:', e); }
    }

    /* ── PayPal ─────────────────────────────────────────────── */
    function initPayPal($container) {
        if (!PBS.paypal_client_id || typeof paypal === 'undefined') return;
        const eventId  = $container.data('event');
        const isDonate = $container.hasClass('pbs-donate-widget');
        const btnId    = isDonate ? 'pbs-paypal-donate-' + eventId : 'pbs-paypal-btn-' + eventId;

        paypal.Buttons({
            createOrder: function(data, actions) {
                const amount = $container.find('.pbs-amount-input').val() || '0';
                return actions.order.create({
                    purchase_units: [{ amount: { value: amount, currency_code: 'USD' } }]
                });
            },
            onApprove: function(data, actions) {
                $container.find('.pbs-spinner').show();
                const $form = $container.find('.pbs-checkout-form, .pbs-donate-form');
                submitOrder($form, $container, null, data.orderID);
            },
            onError: function(err) {
                $container.find('.pbs-error-msg').text('PayPal error. Please try again.');
            }
        }).render('#' + btnId);
    }

    /* ── Form submit ────────────────────────────────────────── */
    function initFormSubmit($container) {
        $container.find('.pbs-checkout-form, .pbs-donate-form').on('submit', async function(e) {
            e.preventDefault();
            const $form   = $(this);
            const gateway = $form.find('.pbs-gateway-input').val();
            const eventId = $container.data('event');

            $container.find('.pbs-submit-btn').prop('disabled', true);
            $container.find('.pbs-spinner').show();
            $container.find('.pbs-error-msg').text('');

            let paymentToken = '';

            // Get token from gateway
            try {
                if (gateway === 'stripe' && stripeInstances[eventId]) {
                    const { stripe, cardEl } = stripeInstances[eventId];
                    const result = await stripe.createPaymentMethod({ type: 'card', card: cardEl });
                    if (result.error) throw new Error(result.error.message);
                    paymentToken = result.paymentMethod.id;
                } else if (gateway === 'square' && squareInstances[eventId]) {
                    const { card } = squareInstances[eventId];
                    const result = await card.tokenize();
                    if (result.status !== 'OK') throw new Error(result.errors?.[0]?.message || 'Card error');
                    paymentToken = result.token;
                }
                // PayPal is handled in onApprove callback
                if (gateway !== 'paypal') {
                    submitOrder($form, $container, paymentToken, null);
                }
            } catch(err) {
                showError($container, err.message);
            }
        });
    }

    function submitOrder($form, $container, paymentToken, paypalOrderId) {
        const eventId = $container.data('event');
        const data = $form.serialize()
            + '&action=pbs_process_order'
            + '&nonce=' + PBS.nonce
            + (paymentToken  ? '&payment_token=' + encodeURIComponent(paymentToken)  : '')
            + (paypalOrderId ? '&paypal_order_id=' + encodeURIComponent(paypalOrderId) : '');

        $.post(PBS.ajax_url, data, async function(res) {
            if (res.success) {
                // Bug 5 fix: handle Stripe 3DS requires_action
                if (res.data.requires_action && stripeInstances[eventId]) {
                    const { stripe } = stripeInstances[eventId];
                    const { error, paymentIntent } = await stripe.confirmCardPayment(res.data.client_secret);
                    if (error) {
                        showError($container, error.message || '3D Secure authentication failed.');
                        return;
                    }
                    if (paymentIntent && paymentIntent.status === 'succeeded') {
                        // Notify server to mark order complete
                        $.post(PBS.ajax_url, {
                            action: 'pbs_stripe_3ds_complete',
                            nonce: PBS.nonce,
                            order_id: res.data.order_id,
                            payment_intent_id: paymentIntent.id,
                        }, function(r) {
                            if (r.success) { window.location.href = r.data.redirect; }
                            else { showError($container, r.data.message || '3DS confirmation failed.'); }
                        }).fail(function() { showError($container, 'Network error after 3DS.'); });
                    }
                    return;
                }
                window.location.href = res.data.redirect;
            } else {
                showError($container, res.data.message || 'Payment failed. Please try again.');
            }
        }).fail(function() {
            showError($container, 'Network error. Please try again.');
        });
    }

    function showError($container, msg) {
        $container.find('.pbs-submit-btn').prop('disabled', false);
        $container.find('.pbs-spinner').hide();
        $container.find('.pbs-error-msg').text(msg);
    }

    /* ── Init all widgets on page ───────────────────────────── */
    $(document).ready(function() {
        let sdksNeeded  = 0;
        let sdksLoaded  = 0;

        function onSdkLoaded() {
            sdksLoaded++;
            if (sdksLoaded >= sdksNeeded) { initWidgets(); }
        }

        function loadScript(src, onload) {
            sdksNeeded++;
            const s = document.createElement('script');
            s.src = src;
            s.onload = onload || onSdkLoaded;
            s.onerror = onSdkLoaded; // count failures so we don't hang
            document.head.appendChild(s);
        }

        // Load Stripe.js if key configured
        if (PBS.stripe_pub_key) {
            loadScript('https://js.stripe.com/v3/');
        }
        // Bug 1 fix: interpolate sqEnv into Square SDK URL
        if (PBS.square_app_id) {
            const sqEnv = PBS.square_env === 'production' ? '' : 'sandbox.';
            loadScript(`https://${sqEnv}web.squarecdn.com/v1/square.js`);
        }
        // Load PayPal SDK
        if (PBS.paypal_client_id) {
            loadScript('https://www.paypal.com/sdk/js?client-id=' + PBS.paypal_client_id + '&currency=USD');
        }

        // If no SDKs needed, init immediately
        if (sdksNeeded === 0) { initWidgets(); }

        function initWidgets() {
            $('.pbs-ticket-widget, .pbs-donate-widget').each(function() {
                const $container = $(this);
                initQtyControls($container.find('form'));
                initDonateWidget($container.find('form'));
                initGatewayTabs($container.find('form'));
                initStripe($container);
                initSquare($container);
                initPayPal($container);
                initFormSubmit($container);
            });
        }
    });

})(jQuery);
