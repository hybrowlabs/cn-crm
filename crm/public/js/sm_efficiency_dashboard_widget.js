frappe.provide('crm.sm_efficiency_dashboard_widget');

crm.sm_efficiency_dashboard_widget = {

    render(wrapper) {
        let $wrapper = $(wrapper);
        $wrapper.empty();

        const widget_html = `
            <div class="sm-eff-widget" style="padding: 20px; background: var(--card-bg, #fff); border-radius: 8px; box-shadow: var(--shadow-sm, 0 1px 3px rgba(0,0,0,.1));">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <div style="font-size: 16px; font-weight: 700; color: var(--text-color, #1f272e);">
                        Sales Manager – Team Reorder Efficiency
                    </div>
                    <button class="btn btn-sm btn-default sm-eff-refresh-btn">Refresh</button>
                </div>

                <div class="sm-eff-loading" style="text-align: center; padding: 30px; color: var(--text-muted);">Loading…</div>
                <div class="sm-eff-error" style="display:none; text-align:center; padding:20px; color:var(--text-muted);"></div>
                <div class="sm-eff-content" style="display:none; overflow-x: auto;"></div>

                <!-- Drill-down overlay -->
                <div class="sm-eff-drilldown-overlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,.45); z-index:1050;"></div>
                <div class="sm-eff-drilldown-modal" style="display:none; position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); width:720px; max-width:92vw; max-height:80vh; background:var(--card-bg,#fff); border-radius:10px; box-shadow:0 8px 30px rgba(0,0,0,.25); z-index:1060; overflow:hidden;">
                    <div class="sm-eff-drilldown-header" style="display:flex; justify-content:space-between; align-items:center; padding:16px 20px; border-bottom:1px solid var(--border-color,#d1d8dd);">
                        <div class="sm-eff-drilldown-title" style="font-size:15px; font-weight:600; color:var(--text-color);"></div>
                        <button class="btn btn-sm btn-default sm-eff-drilldown-close" style="font-size:18px; line-height:1; padding:2px 8px;">✕</button>
                    </div>
                    <div class="sm-eff-drilldown-body" style="padding:16px 20px; max-height:calc(80vh - 60px); overflow-y:auto;"></div>
                </div>
            </div>
        `;

        $wrapper.append(widget_html);

        $wrapper.on('click', '.sm-eff-refresh-btn', () => this.load_data($wrapper));
        $wrapper.on('click', '.sm-eff-drilldown-close, .sm-eff-drilldown-overlay', () => this.close_drilldown($wrapper));

        // Collapsible group toggle
        $wrapper.on('click', '.sm-eff-group-toggle', function () {
            const $body = $(this).next('.sm-eff-group-body');
            const $arrow = $(this).find('.sm-eff-arrow');
            $body.slideToggle(200);
            $arrow.toggleClass('sm-eff-arrow-open');
        });

        this.load_data($wrapper);
    },

    // ── Load data from backend ──
    load_data($wrapper) {
        $wrapper.find('.sm-eff-loading').show();
        $wrapper.find('.sm-eff-content').hide();
        $wrapper.find('.sm-eff-error').hide();

        frappe.call({
            method: 'crm.api.sm_efficiency_dashboard.get_sm_efficiency_data',
            callback: (r) => {
                $wrapper.find('.sm-eff-loading').hide();

                if (!r || !r.message) {
                    $wrapper.find('.sm-eff-error').text('Failed to load data.').show();
                    return;
                }

                const data = r.message;

                if (!data.is_sales_manager) {
                    $wrapper.find('.sm-eff-widget').hide();
                    return;
                }

                if (data.error) {
                    $wrapper.find('.sm-eff-error').text(data.error).show();
                    return;
                }

                // Inject arrow CSS once
                if (!document.getElementById('sm-eff-group-style')) {
                    const style = document.createElement('style');
                    style.id = 'sm-eff-group-style';
                    style.textContent = `
                        .sm-eff-arrow { display:inline-block; transition:transform .2s ease; transform:rotate(0deg); }
                        .sm-eff-arrow-open { transform:rotate(90deg) !important; }
                        .sm-eff-group-toggle:hover { background: var(--subtle-bg, #f0f2f5) !important; }
                    `;
                    document.head.appendChild(style);
                }

                if (data.view_mode === 'admin') {
                    this.render_admin_view($wrapper, data);
                } else {
                    this.render_manager_view($wrapper, data);
                }
            }
        });
    },

    // ── Sales Manager view: flat table ──
    render_manager_view($wrapper, data) {
        const $content = $wrapper.find('.sm-eff-content');
        $content.empty().show();

        if (!data.sales_users || data.sales_users.length === 0) {
            $content.html('<div style="text-align:center; padding:20px; color:var(--text-muted);">No team members found.</div>');
            return;
        }

        const table = this.build_table(data.sales_users);
        $content.html(`<div style="overflow-x: auto; width: 100%;">${table}</div>`);
        this.attach_badge_clicks($content, $wrapper);
    },

    // ── Administrator view: collapsible groups ──
    render_admin_view($wrapper, data) {
        const $content = $wrapper.find('.sm-eff-content');
        $content.empty().show();

        const groups = data.groups || [];

        if (groups.length === 0) {
            $content.html('<div style="text-align:center; padding:20px; color:var(--text-muted);">No Sales Manager groups found.</div>');
            return;
        }

        let html = '';
        groups.forEach((group) => {
            const table = this.build_table(group.sales_users);

            // Aggregate group efficiency
            let totalExpected = 0, totalActual = 0;
            group.sales_users.forEach(su => {
                totalExpected += su.expected_count || 0;
                totalActual += su.actual_count || 0;
            });
            const groupEff = totalExpected > 0
                ? Math.round((totalActual / totalExpected) * 100)
                : null;
            const groupEffLabel = groupEff !== null ? `${groupEff}% group efficiency` : 'N/A';
            const groupEffColor = this._eff_color(groupEff);

            html += `
                <div style="border:1px solid var(--border-color, #d1d8dd); border-radius:8px; margin-bottom:12px; overflow:hidden;">
                    <div class="sm-eff-group-toggle" style="display:flex; justify-content:space-between; align-items:center; padding:14px 18px; cursor:pointer; background:var(--card-bg, #fff); user-select:none;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span class="sm-eff-arrow sm-eff-arrow-open" style="font-size:12px; color:var(--text-muted);">▶</span>
                            <span style="font-size:14px; font-weight:700; color:var(--text-color);">${group.manager_name}</span>
                            <span style="font-size:12px; color:var(--text-muted); font-weight:400;">${group.sales_users.length} member(s)</span>
                        </div>
                        <span style="font-size:12px; padding:3px 12px; border-radius:12px; background:${groupEffColor}18; color:${groupEffColor}; border:1px solid ${groupEffColor}40; font-weight:700;">
                            ${groupEffLabel}
                        </span>
                    </div>
                    <div class="sm-eff-group-body" style="padding:0 12px 12px 12px; overflow-x:auto;">
                        ${table}
                    </div>
                </div>
            `;
        });

        $content.html(html);
        this.attach_badge_clicks($content, $wrapper);
    },

    // ── Build the efficiency table ──
    build_table(sales_users) {
        const headerCells = `
            <th style="padding:10px 14px; text-align:left; white-space:nowrap; font-weight:600; position:sticky; left:0; background:var(--subtle-bg,#f8f9fa); z-index:2;">Sales Person</th>
            <th style="padding:10px 12px; text-align:center; white-space:nowrap; font-weight:600;">Expected Reorders</th>
            <th style="padding:10px 12px; text-align:center; white-space:nowrap; font-weight:600;">Actual Reorders</th>
            <th style="padding:10px 12px; text-align:center; white-space:nowrap; font-weight:600;">Efficiency %</th>
        `;

        let rows = '';
        sales_users.forEach(su => {
            const pct = su.efficiency_pct;
            const color = this._eff_color(pct);

            let effCell;
            if (pct === null || pct === undefined) {
                effCell = `<span style="color:var(--text-muted); font-size:13px;">N/A</span>`;
            } else {
                const pctDisplay = pct.toFixed(1) + '%';
                effCell = `
                    <span class="sm-eff-badge" data-sp="${su.sales_person}" data-name="${su.full_name}"
                          style="display:inline-flex; align-items:center; gap:6px; min-width:70px; justify-content:center;
                                 padding:5px 14px; border-radius:8px; font-weight:700; font-size:13px; cursor:pointer;
                                 background:${color}18; color:${color}; border:1px solid ${color}40;
                                 transition:all .15s ease;"
                          onmouseover="this.style.background='${color}'; this.style.color='#fff'; this.style.transform='scale(1.06)';"
                          onmouseout="this.style.background='${color}18'; this.style.color='${color}'; this.style.transform='scale(1)';">
                        ${pctDisplay}
                    </span>
                `;
            }

            const expCount = su.expected_count > 0
                ? `<span style="font-weight:600; color:var(--text-color);">${su.expected_count}</span>`
                : `<span style="color:var(--text-light,#c0c4cc);">–</span>`;

            const actCount = su.expected_count > 0
                ? `<span style="font-weight:600; color:var(--text-color);">${su.actual_count}</span>`
                : `<span style="color:var(--text-light,#c0c4cc);">–</span>`;

            rows += `
                <tr style="border-bottom:1px solid var(--border-color,#eee);">
                    <td style="padding:10px 14px; font-weight:600; white-space:nowrap; position:sticky; left:0; background:var(--card-bg,#fff); z-index:1;">${su.full_name}</td>
                    <td style="padding:10px 12px; text-align:center;">${expCount}</td>
                    <td style="padding:10px 12px; text-align:center;">${actCount}</td>
                    <td style="padding:10px 12px; text-align:center;">${effCell}</td>
                </tr>
            `;
        });

        return `
            <table style="width:100%; border-collapse:collapse; font-size:13px;">
                <thead><tr style="background:var(--subtle-bg,#f8f9fa); border-bottom:2px solid var(--border-color,#d1d8dd);">${headerCells}</tr></thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    },

    // ── Efficiency color helper ──
    _eff_color(pct) {
        if (pct === null || pct === undefined) return '#6b7280';
        if (pct >= 80) return '#22c55e';  // green
        if (pct >= 50) return '#f59e0b';  // amber
        return '#ef4444';                  // red
    },

    // ── Attach click handlers for efficiency badges ──
    attach_badge_clicks($content, $wrapper) {
        $content.off('click', '.sm-eff-badge');
        $content.on('click', '.sm-eff-badge', (e) => {
            const $el = $(e.currentTarget);
            this.open_drilldown($wrapper, $el.data('sp'), $el.data('name'));
        });
    },

    // ── Drill-down modal ──
    open_drilldown($wrapper, sp_name, salesPersonName) {
        const $overlay = $wrapper.find('.sm-eff-drilldown-overlay');
        const $modal = $wrapper.find('.sm-eff-drilldown-modal');
        const $title = $wrapper.find('.sm-eff-drilldown-title');
        const $body = $wrapper.find('.sm-eff-drilldown-body');

        $title.html(`${salesPersonName} – Customer Reorder Breakdown`);
        $body.html('<div style="text-align:center; padding:20px; color:var(--text-muted);">Loading…</div>');

        $overlay.show();
        $modal.show();

        frappe.call({
            method: 'crm.api.sm_efficiency_dashboard.get_efficiency_details',
            args: { sp_name },
            callback: (r) => {
                if (!r || !r.message || r.message.length === 0) {
                    $body.html('<div style="text-align:center; padding:20px; color:var(--text-muted);">No customers found.</div>');
                    return;
                }
                this.render_customer_list($body, r.message);
            }
        });
    },

    render_customer_list($body, records) {
        // Summary counts
        const expectedList = records.filter(r => r.is_expected);
        const reorderedExpected = expectedList.filter(r => r.did_reorder).length;
        const totalExpected = expectedList.length;
        const effPct = totalExpected > 0 ? ((reorderedExpected / totalExpected) * 100).toFixed(1) : null;
        const effColor = this._eff_color(effPct !== null ? parseFloat(effPct) : null);

        let summaryHtml = `
            <div style="display:flex; gap:16px; margin-bottom:14px; flex-wrap:wrap;">
                <div style="padding:10px 18px; border-radius:8px; background:var(--subtle-bg,#f8f9fa); text-align:center; min-width:100px;">
                    <div style="font-size:22px; font-weight:800; color:var(--text-color);">${totalExpected}</div>
                    <div style="font-size:11px; color:var(--text-muted);">Expected</div>
                </div>
                <div style="padding:10px 18px; border-radius:8px; background:var(--subtle-bg,#f8f9fa); text-align:center; min-width:100px;">
                    <div style="font-size:22px; font-weight:800; color:var(--text-color);">${reorderedExpected}</div>
                    <div style="font-size:11px; color:var(--text-muted);">Reordered</div>
                </div>
                <div style="padding:10px 18px; border-radius:8px; background:${effColor}18; border:1px solid ${effColor}30; text-align:center; min-width:100px;">
                    <div style="font-size:22px; font-weight:800; color:${effColor};">${effPct !== null ? effPct + '%' : 'N/A'}</div>
                    <div style="font-size:11px; color:var(--text-muted);">Efficiency</div>
                </div>
            </div>
        `;

        let html = `
            <table style="width:100%; border-collapse:collapse; font-size:13px;">
                <thead>
                    <tr style="background:var(--subtle-bg,#f8f9fa); border-bottom:2px solid var(--border-color);">
                        <th style="padding:8px 12px; text-align:left;">#</th>
                        <th style="padding:8px 12px; text-align:left;">Customer</th>
                        <th style="padding:8px 12px; text-align:center;">Expected?</th>
                        <th style="padding:8px 12px; text-align:center;">Reordered?</th>
                        <th style="padding:8px 12px; text-align:center;">Freq (days)</th>
                    </tr>
                </thead>
                <tbody>
        `;

        records.forEach((rec, idx) => {
            const expBadge = rec.is_expected
                ? `<span style="padding:2px 10px; border-radius:12px; background:#3b82f618; color:#3b82f6; border:1px solid #3b82f630; font-weight:600; font-size:12px;">Yes</span>`
                : `<span style="padding:2px 10px; border-radius:12px; background:var(--subtle-bg,#f0f2f5); color:var(--text-muted); font-size:12px;">No</span>`;

            const reordBadge = rec.did_reorder
                ? `<span style="padding:2px 10px; border-radius:12px; background:#22c55e18; color:#22c55e; border:1px solid #22c55e30; font-weight:600; font-size:12px;">✓ Yes</span>`
                : (rec.is_expected
                    ? `<span style="padding:2px 10px; border-radius:12px; background:#ef444418; color:#ef4444; border:1px solid #ef444430; font-weight:600; font-size:12px;">✗ No</span>`
                    : `<span style="color:var(--text-light,#c0c4cc); font-size:12px;">–</span>`);

            const freqDisplay = rec.frequency_day
                ? `<span style="color:var(--text-muted);">${rec.frequency_day}d</span>`
                : `<span style="color:var(--text-light,#c0c4cc);">–</span>`;

            html += `
                <tr style="border-bottom:1px solid var(--border-color,#eee); cursor:pointer;"
                    onclick="window.open('${rec.doc_route}', '_blank')">
                    <td style="padding:8px 12px; color:var(--text-muted);">${idx + 1}</td>
                    <td style="padding:8px 12px;">
                        <a href="${rec.doc_route}" target="_blank" style="font-weight:600; color:var(--primary-color,#2490ef);">
                            ${rec.customer_name}
                        </a>
                        <div style="font-size:11px; color:var(--text-muted);">${rec.customer}</div>
                    </td>
                    <td style="padding:8px 12px; text-align:center;">${expBadge}</td>
                    <td style="padding:8px 12px; text-align:center;">${reordBadge}</td>
                    <td style="padding:8px 12px; text-align:center;">${freqDisplay}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        html += `<div style="padding:8px 12px; font-size:12px; color:var(--text-muted); text-align:right;">${records.length} customer(s) total</div>`;

        $body.html(summaryHtml + html);
    },

    close_drilldown($wrapper) {
        $wrapper.find('.sm-eff-drilldown-overlay').hide();
        $wrapper.find('.sm-eff-drilldown-modal').hide();
    }
};
