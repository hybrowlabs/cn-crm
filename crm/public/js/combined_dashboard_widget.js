/**
 * combined_dashboard_widget.js
 *
 * Renders the "Follow-ups by Value" widget and the "Order Frequency Distribution"
 * widget side-by-side in a single container.
 *
 * Both crm.followup_widget and crm.frequency_bucket_widget are also kept intact
 * for backward compatibility (they still function as standalone widgets).
 *
 * Usage in a Frappe Number Card / Custom HTML widget:
 *   crm.combined_dashboard_widget.render(wrapper);
 */

/* ========================================================================================
   SHARED PIE-CHART HELPER – avoids duplicating click-binding logic
   ======================================================================================== */

frappe.provide('crm._widget_utils');

crm._widget_utils = {
    /**
     * Render a frappe.Chart pie chart inside `chartWrapper` and wire up click handlers.
     *
     * @param {jQuery}   chartWrapper - The element to render into.
     * @param {Array}    buckets      - Array of { label, count, customers[] ... }.
     * @param {Array}    colors       - Array of { bg, bar } colour pairs.
     * @param {string}   title        - Chart title string.
     * @param {Function} onSliceClick - Called with the clicked bucket object.
     */
    render_pie_chart(chartWrapper, buckets, colors, title, onSliceClick) {
        setTimeout(() => {
            if (typeof frappe === 'undefined' || typeof frappe.Chart === 'undefined') {
                chartWrapper.hide();
                return;
            }
            try {
                const hasData = buckets.some(b => b.count > 0);
                if (!hasData) {
                    chartWrapper.html('<div style="text-align:center;color:#94a3b8;padding:20px;">No Data</div>');
                    return;
                }

                new frappe.Chart(chartWrapper[0], {
                    data: {
                        labels: buckets.map(b => b.label),
                        datasets: [{ values: buckets.map(b => b.count) }]
                    },
                    title,
                    type: 'pie',
                    height: 300,
                    colors: colors.map(c => c.bg),
                    isNavigable: 1,
                });

                // data-select event (Frappe Charts v1+)
                chartWrapper[0].addEventListener('data-select', (e) => {
                    console.log('Pie chart data-select event:', e);
                    let bucket = null;
                    if (e && e.detail) {
                        if (e.detail.label) {
                            bucket = buckets.find(b => b.label === e.detail.label);
                        } else if (e.detail.index !== undefined) {
                            bucket = buckets[e.detail.index];
                        }
                    } else if (e && typeof e.detail === 'number') {
                        bucket = buckets[e.detail];
                    }

                    if (bucket) {
                        console.log('Selected bucket:', bucket);
                        onSliceClick(bucket);
                    } else {
                        console.warn('Could not identify bucket from event detail:', e.detail);
                    }
                });

                // Fallback: direct DOM click on SVG paths (broader selector for robustness)
                setTimeout(() => {
                    // Try .pie-path, .frappe-chart-path, and generic path inside chart areas
                    const paths = chartWrapper[0].querySelectorAll('.pie-path, path[data-bucket-index], .graph-svg-tip-content + svg path');
                    console.log(`Found ${paths.length} potential pie paths for fallback`);

                    paths.forEach((path, idx) => {
                        path.style.cursor = 'pointer';
                        path.addEventListener('click', (e) => {
                            console.log(`Fallback click on slice index ${idx}`);
                            e.stopPropagation();
                            if (idx < buckets.length) {
                                onSliceClick(buckets[idx]);
                            }
                        });
                    });

                    // Even broader fallback: any path inside the SVG
                    if (paths.length === 0) {
                        chartWrapper.find('svg path').css('cursor', 'pointer').on('click', function (e) {
                            const index = $(this).index(); // rough estimate
                            console.log(`Broad fallback click index ${index}`);
                            if (index >= 0 && index < buckets.length) {
                                onSliceClick(buckets[index]);
                            }
                        });
                    }
                }, 500);

            } catch (err) {
                console.error('Error drawing pie chart:', err);
            }
        }, 100);
    },

    /**
     * Show a lightweight modal overlay (no frappe.ui.Dialog dependency).
     * @param {string} title - Modal title text.
     * @param {string} bodyHtml - Inner HTML for the scrollable modal body.
     * @param {Function} [onReady] - Optional callback once modal is appended (to wire sub-events).
     */
    _show_modal(title, bodyHtml, onReady) {
        console.log('_show_modal called with title:', title);
        // Remove any existing crm-overlay
        document.querySelectorAll('.crm-widget-overlay').forEach(el => {
            console.log('Removing existing overlay');
            el.remove();
        });

        const overlay = document.createElement('div');
        overlay.className = 'crm-widget-overlay';
        overlay.style.cssText = [
            'position:fixed', 'top:0', 'left:0', 'right:0', 'bottom:0', 'z-index:99999',
            'background:rgba(0,0,0,0.5)',
            'display:flex', 'align-items:center', 'justify-content:center',
            'padding:16px', 'opacity:1', 'visibility:visible'
        ].join(';');

        overlay.innerHTML = `
            <div class="crm-widget-modal" style="
                background:#fff;
                border-radius:10px;
                box-shadow:0 8px 32px rgba(0,0,0,0.22);
                width:100%;
                max-width:880px;
                max-height:88vh;
                display:flex;
                flex-direction:column;
                overflow:hidden;
            ">
                <div style="
                    display:flex;justify-content:space-between;align-items:center;
                    padding:14px 20px;
                    background:linear-gradient(135deg,#1e293b 0%,#334155 100%);
                    color:#fff;
                    border-radius:10px 10px 0 0;
                ">
                    <span style="font-size:15px;font-weight:700;">${title}</span>
                    <button class="crm-modal-close" style="
                        background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);
                        color:#fff;border-radius:6px;cursor:pointer;font-size:16px;
                        padding:2px 10px;line-height:1.6;
                    ">&times;</button>
                </div>
                <div style="overflow-y:auto;padding:20px;background:#f8fafc;flex:1;">
                    ${bodyHtml}
                </div>
            </div>
        `;

        // Close on ✕ button
        overlay.querySelector('.crm-modal-close').addEventListener('click', () => overlay.remove());

        // Close on click outside the modal box
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.remove();
        });

        // Close on ESC
        const onKeyDown = (e) => {
            if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', onKeyDown); }
        };
        document.addEventListener('keydown', onKeyDown);

        document.body.appendChild(overlay);
        console.log('Overlay appended to document.body');

        if (typeof onReady === 'function') onReady(overlay);
    }
};

/* ========================================================================================
   FOLLOW-UP WIDGET  (standalone – unchanged API)
   ======================================================================================== */

frappe.provide('crm.followup_widget');

crm.followup_widget = {

    render(wrapper) {
        try {
            const container = $(wrapper);
            container.empty();

            container.html(`
			<style>
				.followup-widget {
					font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
				}
				.followup-header {
					display: flex;
					justify-content: space-between;
					align-items: center;
					padding: 12px 16px;
					background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
					border-radius: 10px 10px 0 0;
					color: #fff;
				}
				.followup-title {
					font-size: 15px;
					font-weight: 600;
					letter-spacing: 0.3px;
				}
				.followup-refresh-btn {
					background: rgba(255,255,255,0.15) !important;
					border: 1px solid rgba(255,255,255,0.2) !important;
					color: #fff !important;
					font-size: 12px;
					padding: 4px 12px;
					border-radius: 6px;
					transition: all 0.2s ease;
				}
				.followup-refresh-btn:hover { background: rgba(255,255,255,0.25) !important; }
				.followup-loading  { text-align: center; padding: 24px; color: #94a3b8; font-size: 13px; }
				.followup-content  {
					background: #f8fafc;
					border-radius: 0 0 10px 10px;
					border: 1px solid #e2e8f0;
					border-top: none;
					max-height: 450px;
					overflow-y: auto;
				}
				.followup-content::-webkit-scrollbar       { width: 6px; }
				.followup-content::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 10px; }
				.followup-empty    { text-align: center; padding: 32px 16px; color: #94a3b8; font-size: 14px; }
				.followup-summary-item {
					display: flex; justify-content: space-between; align-items: center;
					padding: 11px 16px; cursor: pointer; transition: background 0.15s ease;
					border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 8px;
				}
				.followup-summary-item:hover { opacity: 0.8; }
				.followup-summary-label {
					font-size: 14px; font-weight: 600; color: #1e293b;
					display: flex; align-items: center; gap: 10px;
				}
				.followup-summary-count {
					font-size: 11px; font-weight: 700; padding: 2px 8px;
					border-radius: 10px; color: #fff; min-width: 24px; text-align: center;
				}
			</style>
			<div class="followup-widget">
				<div class="followup-header">
					<div class="followup-title">Follow-ups by Value</div>
					<button class="btn btn-sm followup-refresh-btn">Refresh</button>
				</div>
				<div class="followup-loading">Loading...</div>
				<div class="followup-content" style="display:none;">
					<div class="followup-bucket-list"></div>
					<div class="followup-empty" style="display:none;">No follow-ups 🎉</div>
				</div>
			</div>
		`);

            container.off('click', '.followup-refresh-btn');
            container.on('click', '.followup-refresh-btn', () => this.load_data(container));

            this.load_data(container);
        } catch (err) {
            console.error("Error in followup_widget.render:", err);
            $(wrapper).html('<div style="padding:15px;color:red;">Failed to render Follow-ups widget.</div>');
        }
    },

    load_data(container) {
        const loading = container.find('.followup-loading');
        const content = container.find('.followup-content');
        const list = container.find('.followup-bucket-list');
        const empty = container.find('.followup-empty');

        loading.show();
        content.hide();

        frappe.call({
            method: 'crm.fcrm.doctype.frequency_log_list.frequency_log_list.get_followup_logs_for_user',
            callback: (r) => {
                loading.hide();
                content.show();
                if (r.message && r.message.customers && r.message.customers.length) {
                    const buckets = this.build_buckets(r.message.customers);
                    this.render_buckets(list, buckets);
                    empty.hide();
                    list.show();
                } else {
                    list.hide();
                    empty.show();
                }
            }
        });
    },

    build_buckets(customers) {
        const defs = [
            { label: '0-1Lakh', min: 0, max: 100000 },
            { label: '1Lakh-5Lakh', min: 100000, max: 500000 },
            { label: '5Lakh-20Lakh', min: 500000, max: 2000000 },
            { label: '20Lakh-50Lakh', min: 2000000, max: 5000000 },
            { label: '50Lakh+', min: 5000000, max: Infinity },
        ];
        let buckets = defs.map(b => ({ ...b, count: 0, customers: [] }));

        customers.forEach(customer => {
            const val = customer.total_value || 0;
            let target = buckets[buckets.length - 1];
            for (let b of buckets) {
                if (val >= b.min && val < b.max) { target = b; break; }
            }
            target.customers.push(customer);
            target.count += 1;
        });
        return buckets;
    },

    _bucket_colors: [
        { bg: '#3b82f6', bar: '#eff6ff' },
        { bg: '#10b981', bar: '#ecfdf5' },
        { bg: '#f59e0b', bar: '#fffbeb' },
        { bg: '#8b5cf6', bar: '#f3e8ff' },
        { bg: '#ec4899', bar: '#fdf2f8' },
        { bg: '#6b7280', bar: '#f9fafb' },
    ],

    render_buckets(container, buckets) {
        container.empty();

        const chartWrapper = $('<div class="followup-pie-chart" style="margin: 20px auto; max-width: 100%; padding: 10px;"></div>');
        container.append(chartWrapper);

        const listWrapper = $('<div class="followup-summary-list" style="padding: 0 16px 16px 16px;"></div>');
        buckets.forEach((bucket, bIdx) => {
            const palette = this._bucket_colors[bIdx % this._bucket_colors.length];
            const item = $(`
				<div class="followup-summary-item" style="background:${palette.bar};">
					<span class="followup-summary-label">
						<div style="width:12px;height:12px;border-radius:50%;background:${palette.bg}"></div>
						${bucket.label}
					</span>
					<span class="followup-summary-count" style="background:${palette.bg};">${bucket.count}</span>
				</div>
			`);
            item.on('click', () => this.open_bucket_drawer(bucket));
            listWrapper.append(item);
        });
        container.append(listWrapper);

        crm._widget_utils.render_pie_chart(
            chartWrapper, buckets, this._bucket_colors,
            'Follow-ups by Value',
            (bucket) => this.open_bucket_drawer(bucket)
        );
    },

    open_bucket_drawer(bucket) {
        console.log('Opening drawer for bucket:', bucket);
        if (!bucket || !bucket.customers || bucket.customers.length === 0) {
            console.warn('No customers found in bucket');
            /*
            frappe.show_alert
                ? frappe.show_alert({ message: 'No data in ' + bucket.label, indicator: 'orange' })
                : alert('No data in ' + bucket.label);
            */
            return;
        }

        const today = (function () { try { return (frappe.datetime && frappe.datetime.get_today) ? frappe.datetime.get_today() : new Date().toISOString().slice(0, 10); } catch (e) { return new Date().toISOString().slice(0, 10); } })();

        const fmtDate = (d) => frappe.datetime && frappe.datetime.str_to_user ? frappe.datetime.str_to_user(d) : d;
        const fmtCur = (val, cur) => typeof format_currency === 'function'
            ? format_currency(val, cur, 0).replace(/\.00$/, '')
            : '₹' + parseFloat(val || 0).toLocaleString('en-IN');

        let html = `<div class="followup-drawer-content">`;

        bucket.customers.forEach((customer, idx) => {
            html += `
                <div style="margin-bottom:16px;border:1px solid #e2e8f0;border-radius:6px;overflow:hidden;background:#fff;">
                    <div style="background:#f8fafc;padding:12px 16px;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                        <span style="font-weight:600;font-size:14px;color:#1e293b;">
                            <a href="/app/customer/${encodeURIComponent(customer.customer_code)}" style="color:inherit;text-decoration:none;" target="_blank">
                                ${customer.customer_name}
                            </a>
                        </span>
                        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                            <span style="font-size:13px;font-weight:600;color:#1e293b;">Total: ${fmtCur(customer.total_value || 0, customer.default_currency)}</span>
                            <span style="font-size:12px;font-weight:600;color:#64748b;background:#e2e8f0;padding:2px 8px;border-radius:10px;">${customer.items.length} item${customer.items.length !== 1 ? 's' : ''}</span>
                            <button class="crm-create-quotation-btn" data-idx="${idx}" style="font-size:12px;font-weight:600;padding:4px 12px;border-radius:6px;border:1.5px solid #3b82f6;background:#eff6ff;color:#1d4ed8;cursor:pointer;">Create Quotation</button>
                        </div>
                    </div>
                    <div style="overflow-x:auto;">
                        <table style="width:100%;font-size:13px;border-collapse:collapse;min-width:460px;">
                            <thead>
                                <tr style="text-align:left;color:#64748b;font-size:12px;text-transform:uppercase;">
                                    <th style="padding:10px 16px;border-bottom:1px solid #e2e8f0;font-weight:600;">Item Name</th>
                                    <th style="padding:10px 16px;border-bottom:1px solid #e2e8f0;font-weight:600;width:70px;">Qty</th>
                                    <th style="padding:10px 16px;border-bottom:1px solid #e2e8f0;font-weight:600;width:160px;">Rate</th>
                                    <th style="padding:10px 16px;border-bottom:1px solid #e2e8f0;font-weight:600;width:120px;">Next Order</th>
                                </tr>
                            </thead>
                            <tbody>`;

            customer.items.forEach(item => {
                let dateColor = '#16a34a', dateLabel = 'N/A';
                if (item.next_order_date) {
                    dateLabel = fmtDate(item.next_order_date);
                    dateColor = item.next_order_date < today ? '#dc2626'
                        : item.next_order_date === today ? '#d97706' : '#16a34a';
                } else {
                    dateColor = '#94a3b8';
                }
                html += `
                                <tr style="border-bottom:1px solid #f1f5f9;">
                                    <td style="padding:10px 16px;color:#334155;">${item.item}</td>
                                    <td style="padding:10px 16px;color:#334155;">${item.qty}</td>
                                    <td style="padding:10px 16px;font-weight:600;color:#1d4ed8;">${fmtCur(item.rate, customer.default_currency)}</td>
                                    <td style="padding:10px 16px;color:${dateColor};font-weight:600;">${dateLabel}</td>
                                </tr>`;
            });

            html += `</tbody></table></div></div>`;
        });

        html += `</div>`;

        crm._widget_utils._show_modal(`Follow-ups: ${bucket.label}`, html, (overlay) => {
            overlay.querySelectorAll('.crm-create-quotation-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const idx = parseInt(btn.dataset.idx, 10);
                    const customer = bucket.customers[idx];
                    btn.disabled = true;
                    btn.textContent = '...';
                    if (frappe.route_options !== undefined) {
                        frappe.route_options = {
                            quotation_to: 'Customer',
                            party_name: customer.customer_code,
                            currency: customer.default_currency,
                            custom_branch: customer.custom_branch,
                            custom_sale_by: frappe.session.user,
                            items: customer.items.map(i => ({ item_code: i.item, qty: i.qty }))
                        };
                        frappe.new_doc('Quotation', frappe.route_options);
                    } else {
                        window.open(`/app/quotation/new-quotation-1?quotation_to=Customer&party_name=${encodeURIComponent(customer.customer_code)}`, '_blank');
                    }
                    setTimeout(() => { btn.disabled = false; btn.textContent = 'Create Quotation'; }, 1000);
                });
            });
        });
    }
};

/* ========================================================================================
   FREQUENCY BUCKET WIDGET  (standalone – unchanged API)
   ======================================================================================== */

frappe.provide('crm.frequency_bucket_widget');

crm.frequency_bucket_widget = {

    render(wrapper) {
        try {
            const container = $(wrapper);
            container.empty();

            container.html(`
			<style>
				.freq-bucket-widget { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
				.freq-bucket-header {
					display: flex; justify-content: space-between; align-items: center;
					padding: 12px 16px;
					background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
					border-radius: 10px 10px 0 0; color: #fff;
				}
				.freq-bucket-title { font-size: 15px; font-weight: 600; letter-spacing: 0.3px; }
				.freq-refresh-btn {
					background: rgba(255,255,255,0.15) !important;
					border: 1px solid rgba(255,255,255,0.2) !important;
					color: #fff !important; font-size: 12px; padding: 4px 12px;
					border-radius: 6px; transition: all 0.2s ease;
				}
				.freq-refresh-btn:hover { background: rgba(255,255,255,0.25) !important; }
				.freq-loading  { text-align: center; padding: 24px; color: #94a3b8; font-size: 13px; }
				.freq-content  {
					background: #f8fafc; border-radius: 0 0 10px 10px;
					border: 1px solid #e2e8f0; border-top: none;
					max-height: 450px; overflow-y: auto;
				}
				.freq-content::-webkit-scrollbar       { width: 6px; }
				.freq-content::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 10px; }
				.freq-empty { text-align: center; padding: 32px 16px; color: #94a3b8; font-size: 14px; }
				.freq-summary-item {
					display: flex; justify-content: space-between; align-items: center;
					padding: 11px 16px; cursor: pointer; transition: background 0.15s ease;
					border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 8px;
				}
				.freq-summary-item:hover { opacity: 0.8; }
				.freq-summary-label {
					font-size: 14px; font-weight: 600; color: #1e293b;
					display: flex; align-items: center; gap: 10px;
				}
				.freq-summary-count {
					font-size: 11px; font-weight: 700; padding: 2px 8px;
					border-radius: 10px; color: #fff; min-width: 24px; text-align: center;
				}
			</style>
			<div class="freq-bucket-widget">
				<div class="freq-bucket-header">
					<div class="freq-bucket-title">Order Frequency Distribution</div>
					<button class="btn btn-sm freq-refresh-btn">Refresh</button>
				</div>
				<div class="freq-loading">Loading...</div>
				<div class="freq-content" style="display:none;">
					<div class="freq-bucket-list"></div>
					<div class="freq-empty" style="display:none;">No frequency data available</div>
				</div>
			</div>
		`);

            container.off('click', '.freq-refresh-btn');
            container.on('click', '.freq-refresh-btn', () => this.load_data(container));

            this.load_data(container);
        } catch (err) {
            console.error("Error in frequency_bucket_widget.render:", err);
            $(wrapper).html('<div style="padding:15px;color:red;">Failed to render Frequency widget.</div>');
        }
    },

    load_data(container) {
        const loading = container.find('.freq-loading');
        const content = container.find('.freq-content');
        const list = container.find('.freq-bucket-list');
        const empty = container.find('.freq-empty');

        loading.show();
        content.hide();

        frappe.call({
            method: 'crm.fcrm.doctype.frequency_log_list.frequency_log_list.get_frequency_buckets',
            callback: (r) => {
                loading.hide();
                content.show();
                if (r.message?.buckets?.length) {
                    this.render_buckets(list, r.message.buckets);
                    empty.hide();
                    list.show();
                } else {
                    list.hide();
                    empty.show();
                }
            }
        });
    },

    _bucket_colors: [
        { bg: '#10b981', bar: '#ecfdf5' },
        { bg: '#3b82f6', bar: '#eff6ff' },
        { bg: '#f59e0b', bar: '#fffbeb' },
        { bg: '#6b7280', bar: '#f9fafb' },
    ],

    render_buckets(container, buckets) {
        container.empty();

        const chartWrapper = $('<div class="freq-pie-chart" style="margin: 20px auto; max-width: 100%; padding: 10px;"></div>');
        container.append(chartWrapper);

        const listWrapper = $('<div class="freq-summary-list" style="padding: 0 16px 16px 16px;"></div>');
        buckets.forEach((bucket, bIdx) => {
            const palette = this._bucket_colors[bIdx % this._bucket_colors.length];
            const item = $(`
				<div class="freq-summary-item" style="background:${palette.bar};">
					<span class="freq-summary-label">
						<div style="width:12px;height:12px;border-radius:50%;background:${palette.bg}"></div>
						${bucket.label}
					</span>
					<span class="freq-summary-count" style="background:${palette.bg};">${bucket.count}</span>
				</div>
			`);
            item.on('click', () => this.open_bucket_drawer(bucket));
            listWrapper.append(item);
        });
        container.append(listWrapper);

        crm._widget_utils.render_pie_chart(
            chartWrapper, buckets, this._bucket_colors,
            'Breakdown by Days',
            (bucket) => this.open_bucket_drawer(bucket)
        );
    },

    open_bucket_drawer(bucket) {
        console.log('Opening drawer for frequency bucket:', bucket);
        if (!bucket || !bucket.customers || bucket.customers.length === 0) {
            console.warn('No customers found in frequency bucket');
            /*
            frappe.show_alert
                ? frappe.show_alert({ message: 'No data in ' + bucket.label, indicator: 'orange' })
                : alert('No data in ' + bucket.label);
            */
            return;
        }

        const today = (function () { try { return (frappe.datetime && frappe.datetime.get_today) ? frappe.datetime.get_today() : new Date().toISOString().slice(0, 10); } catch (e) { return new Date().toISOString().slice(0, 10); } })();

        const fmtDate = (d) => frappe.datetime && frappe.datetime.str_to_user ? frappe.datetime.str_to_user(d) : d;
        const fmtCur = (val, cur) => typeof format_currency === 'function'
            ? format_currency(val, cur, 0).replace(/\.00$/, '')
            : '₹' + parseFloat(val || 0).toLocaleString('en-IN');

        let html = `<div>`;

        bucket.customers.forEach(customer => {
            html += `
                <div style="margin-bottom:16px;border:1px solid #e2e8f0;border-radius:6px;overflow:hidden;background:#fff;">
                    <div style="background:#f8fafc;padding:12px 16px;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                        <span style="font-weight:600;font-size:14px;color:#1e293b;">
                            <a href="/app/customer/${encodeURIComponent(customer.customer_code)}" style="color:inherit;text-decoration:none;" target="_blank">
                                ${customer.customer_name}
                            </a>
                        </span>
                        <span style="font-size:12px;font-weight:600;color:#64748b;background:#e2e8f0;padding:2px 8px;border-radius:10px;">${customer.items.length} item${customer.items.length !== 1 ? 's' : ''}</span>
                    </div>
                    <div style="overflow-x:auto;">
                        <table style="width:100%;font-size:13px;border-collapse:collapse;min-width:460px;">
                            <thead>
                                <tr style="text-align:left;color:#64748b;font-size:12px;text-transform:uppercase;">
                                    <th style="padding:10px 16px;border-bottom:1px solid #e2e8f0;font-weight:600;">Item Name</th>
                                    <th style="padding:10px 16px;border-bottom:1px solid #e2e8f0;font-weight:600;width:70px;">Qty</th>
                                    <th style="padding:10px 16px;border-bottom:1px solid #e2e8f0;font-weight:600;width:160px;">Rate</th>
                                    <th style="padding:10px 16px;border-bottom:1px solid #e2e8f0;font-weight:600;width:90px;">Freq Day</th>
                                    <th style="padding:10px 16px;border-bottom:1px solid #e2e8f0;font-weight:600;width:120px;">Next Order</th>
                                </tr>
                            </thead>
                            <tbody>`;

            customer.items.forEach(item => {
                let dateColor = '#16a34a', dateLabel = 'N/A';
                if (item.next_order_date) {
                    dateLabel = fmtDate(item.next_order_date);
                    dateColor = item.next_order_date < today ? '#dc2626'
                        : item.next_order_date === today ? '#d97706' : '#16a34a';
                } else {
                    dateColor = '#94a3b8';
                }
                html += `
                                <tr style="border-bottom:1px solid #f1f5f9;">
                                    <td style="padding:10px 16px;color:#334155;">${item.item}</td>
                                    <td style="padding:10px 16px;color:#334155;">${item.quantity || 0}</td>
                                    <td style="padding:10px 16px;font-weight:600;color:#1d4ed8;">${fmtCur(item.rate || 0, customer.default_currency)}</td>
                                    <td style="padding:10px 16px;font-weight:600;color:#1d4ed8;">${item.frequency_day}</td>
                                    <td style="padding:10px 16px;color:${dateColor};font-weight:600;">${dateLabel}</td>
                                </tr>`;
            });

            html += `</tbody></table></div></div>`;
        });

        html += `</div>`;

        crm._widget_utils._show_modal(`Frequency Data: ${bucket.label}`, html);
    }
};

/* ========================================================================================
   COMBINED DASHBOARD WIDGET  – renders both widgets side by side
   ======================================================================================== */

frappe.provide('crm.combined_dashboard_widget');

crm.combined_dashboard_widget = {

    render(wrapper) {
        try {
            const container = $(wrapper);
            container.empty();

            // Outer flex row – two equal columns
            container.html(`
			<style>
				.combined-widget-row {
					display: flex;
					gap: 20px;
					align-items: flex-start;
					flex-wrap: wrap;
				}
				.combined-widget-col {
					flex: 1 1 0;
					min-width: 320px;
				}
				@media (max-width: 860px) {
					.combined-widget-col { flex: 1 1 100%; }
				}

				/* -- shared refresh button -- */
				.combined-refresh-btn {
					margin: 10px 0 0 0;
					display: flex;
					justify-content: flex-end;
				}
			</style>
			<div class="combined-widget-row">
				<div class="combined-widget-col" id="combined-followup-col"></div>
				<div class="combined-widget-col" id="combined-frequency-col"></div>
			</div>
		`);

            // Render each widget into its respective column
            if (window.crm && crm.followup_widget) {
                crm.followup_widget.render(container.find('#combined-followup-col')[0]);
            }
            if (window.crm && crm.frequency_bucket_widget) {
                crm.frequency_bucket_widget.render(container.find('#combined-frequency-col')[0]);
            }
        } catch (err) {
            console.error("Error in combined_dashboard_widget.render:", err);
            $(wrapper).html('<div style="padding:15px;color:red;">Failed to render Combined Dashboard widget.</div>');
        }
    }
};
