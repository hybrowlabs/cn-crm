frappe.provide('crm.sm_pipeline_dashboard_widget');

crm.sm_pipeline_dashboard_widget = {

    render(wrapper) {
        let $wrapper = $(wrapper);
        $wrapper.empty();

        let widget_html = `
            <div class="sm-pipeline-widget" style="padding: 20px; background: var(--card-bg, #fff); border-radius: 8px; box-shadow: var(--shadow-sm, 0 1px 3px rgba(0,0,0,.1));">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <div style="font-size: 16px; font-weight: 700; color: var(--text-color, #1f272e);">
                        Sales Manager – Team Pipeline
                    </div>
                    <button class="btn btn-sm btn-default sm-refresh-btn">Refresh</button>
                </div>

                <div class="sm-loading" style="text-align: center; padding: 30px; color: var(--text-muted);">Loading…</div>
                <div class="sm-error" style="display:none; text-align:center; padding:20px; color:var(--text-muted);"></div>
                <div class="sm-content" style="display:none;"></div>

                <!-- Drill-down overlay -->
                <div class="sm-drilldown-overlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,.45); z-index:1050;"></div>
                <div class="sm-drilldown-modal" style="display:none; position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); width:700px; max-width:90vw; max-height:80vh; background:var(--card-bg,#fff); border-radius:10px; box-shadow:0 8px 30px rgba(0,0,0,.25); z-index:1060; overflow:hidden;">
                    <div class="sm-drilldown-header" style="display:flex; justify-content:space-between; align-items:center; padding:16px 20px; border-bottom:1px solid var(--border-color,#d1d8dd);">
                        <div class="sm-drilldown-title" style="font-size:15px; font-weight:600; color:var(--text-color);"></div>
                        <button class="btn btn-sm btn-default sm-drilldown-close" style="font-size:18px; line-height:1; padding:2px 8px;">✕</button>
                    </div>
                    <div class="sm-drilldown-body" style="padding:16px 20px; max-height:calc(80vh - 60px); overflow-y:auto;"></div>
                </div>
            </div>
        `;

        $wrapper.append(widget_html);

        // Refresh
        $wrapper.on('click', '.sm-refresh-btn', () => this.load_data($wrapper));

        // Close drilldown
        $wrapper.on('click', '.sm-drilldown-close, .sm-drilldown-overlay', () => this.close_drilldown($wrapper));

        // Collapsible toggle
        $wrapper.on('click', '.sm-group-toggle', function () {
            const $header = $(this);
            const $body = $header.next('.sm-group-body');
            const $arrow = $header.find('.sm-arrow');
            $body.slideToggle(200);
            $arrow.toggleClass('sm-arrow-open');
        });

        this.load_data($wrapper);
    },

    stageColors: {
        'New': '#ffa00a',
        'Contacted': '#f59e0b',
        'Nurture': '#3b82f6',
        'Qualified': '#10b981',
        'Unqualified': '#ef4444',
        'Junk': '#8b5cf6',
        'Qualification': '#6b7280',
        'Demo/Making': '#f97316',
        'Proposal/Quotation': '#3b82f6',
        'Negotiation': '#eab308',
        'Won': '#22c55e',
        'Lost': '#ef4444'
    },

    load_data($wrapper) {
        $wrapper.find('.sm-loading').show();
        $wrapper.find('.sm-content').hide();
        $wrapper.find('.sm-error').hide();

        frappe.call({
            method: 'crm.api.sm_pipeline_dashboard.get_sm_pipeline_data',
            callback: (r) => {
                $wrapper.find('.sm-loading').hide();

                if (!r || !r.message) {
                    $wrapper.find('.sm-error').text('Failed to load data.').show();
                    return;
                }

                const data = r.message;

                if (!data.is_sales_manager) {
                    $wrapper.find('.sm-pipeline-widget').hide();
                    return;
                }

                if (data.error) {
                    $wrapper.find('.sm-error').text(data.error).show();
                    return;
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
        const $content = $wrapper.find('.sm-content');
        $content.empty().show();

        if (!data.sales_users || data.sales_users.length === 0) {
            $content.html('<div style="text-align:center; padding:20px; color:var(--text-muted);">No subordinate sales users found.</div>');
            return;
        }

        const table = this.build_table(data.stage_columns, data.sales_users);
        $content.html(table);
        this.attach_badge_clicks($content, $wrapper);
    },

    // ── Administrator view: collapsible groups ──
    render_admin_view($wrapper, data) {
        const $content = $wrapper.find('.sm-content');
        $content.empty().show();

        const groups = data.groups || [];

        if (groups.length === 0) {
            $content.html('<div style="text-align:center; padding:20px; color:var(--text-muted);">No Sales Manager groups found.</div>');
            return;
        }

        // Add CSS for arrow animation
        if (!document.getElementById('sm-group-style')) {
            const style = document.createElement('style');
            style.id = 'sm-group-style';
            style.textContent = `
                .sm-arrow { display:inline-block; transition:transform .2s ease; transform:rotate(0deg); }
                .sm-arrow-open { transform:rotate(90deg) !important; }
                .sm-group-toggle:hover { background: var(--subtle-bg, #f0f2f5) !important; }
            `;
            document.head.appendChild(style);
        }

        let html = '';
        groups.forEach((group, idx) => {
            const totalCount = group.sales_users.reduce((sum, su) => {
                return sum + su.stages.reduce((s, st) => s + (st.count || 0), 0);
            }, 0);

            const table = this.build_table(data.stage_columns, group.sales_users);

            html += `
                <div style="border:1px solid var(--border-color, #d1d8dd); border-radius:8px; margin-bottom:12px; overflow:hidden;">
                    <div class="sm-group-toggle" style="display:flex; justify-content:space-between; align-items:center; padding:14px 18px; cursor:pointer; background:var(--card-bg, #fff); user-select:none;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span class="sm-arrow sm-arrow-open" style="font-size:12px; color:var(--text-muted);">▶</span>
                            <span style="font-size:14px; font-weight:700; color:var(--text-color);">${group.manager_name}</span>
                            <span style="font-size:12px; color:var(--text-muted); font-weight:400;">${group.sales_users.length} member(s)</span>
                        </div>
                        <span style="font-size:12px; padding:3px 10px; border-radius:12px; background:var(--subtle-bg, #f0f2f5); color:var(--text-muted); font-weight:600;">${totalCount} total items</span>
                    </div>
                    <div class="sm-group-body" style="padding:0 12px 12px 12px; overflow-x:auto;">
                        ${table}
                    </div>
                </div>
            `;
        });

        $content.html(html);
        this.attach_badge_clicks($content, $wrapper);
    },

    // ── Shared: build pipeline table HTML ──
    build_table(stage_columns, sales_users) {
        let headerCells = '<th style="padding:10px 14px; text-align:left; white-space:nowrap; font-weight:600; position:sticky; left:0; background:var(--subtle-bg, #f8f9fa); z-index:2;">Sales Person</th>';
        stage_columns.forEach(col => {
            const dt = col.doctype === 'CRM Lead' ? 'Lead' : 'Deal';
            headerCells += `<th style="padding:10px 12px; text-align:center; white-space:nowrap; font-weight:600;">
                <div>${col.stage}</div>
                <div style="font-size:10px; color:var(--text-muted); font-weight:400;">${dt}</div>
            </th>`;
        });

        let rows = '';
        sales_users.forEach(su => {
            let cells = `<td style="padding:10px 14px; font-weight:600; white-space:nowrap; position:sticky; left:0; background:var(--card-bg,#fff); z-index:1;">${su.full_name}</td>`;

            su.stages.forEach(st => {
                const count = st.count || 0;
                const color = this.stageColors[st.stage] || '#6b7280';

                if (count > 0) {
                    cells += `<td style="padding:10px 12px; text-align:center;">
                        <span class="sm-count-badge" data-user="${su.user}" data-doctype="${st.doctype}" data-status="${st.stage}" data-name="${su.full_name}"
                              style="display:inline-block; min-width:32px; padding:4px 10px; border-radius:6px; font-weight:700; font-size:13px; cursor:pointer;
                                     background:${color}18; color:${color}; border:1px solid ${color}40;
                                     transition: all .15s ease;"
                              onmouseover="this.style.background='${color}'; this.style.color='#fff'; this.style.transform='scale(1.08)';"
                              onmouseout="this.style.background='${color}18'; this.style.color='${color}'; this.style.transform='scale(1)';">
                            ${count}
                        </span>
                    </td>`;
                } else {
                    cells += `<td style="padding:10px 12px; text-align:center; color:var(--text-light, #c0c4cc); font-size:13px;">–</td>`;
                }
            });

            rows += `<tr style="border-bottom:1px solid var(--border-color, #eee);">${cells}</tr>`;
        });

        return `
            <table style="width:100%; border-collapse:collapse; font-size:13px;">
                <thead><tr style="background: var(--subtle-bg, #f8f9fa); border-bottom: 2px solid var(--border-color, #d1d8dd);">${headerCells}</tr></thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    },

    // ── Attach click handlers for drill-down badges ──
    attach_badge_clicks($content, $wrapper) {
        $content.off('click', '.sm-count-badge');
        $content.on('click', '.sm-count-badge', (e) => {
            const $el = $(e.currentTarget);
            this.open_drilldown(
                $wrapper,
                $el.data('user'),
                $el.data('doctype'),
                $el.data('status'),
                $el.data('name')
            );
        });
    },

    // ── Drill-down modal ──
    open_drilldown($wrapper, user, doctype, status, salesPersonName) {
        const $overlay = $wrapper.find('.sm-drilldown-overlay');
        const $modal = $wrapper.find('.sm-drilldown-modal');
        const $title = $wrapper.find('.sm-drilldown-title');
        const $body = $wrapper.find('.sm-drilldown-body');

        const dtLabel = doctype === 'CRM Lead' ? 'Leads' : 'Deals';
        $title.html(`${salesPersonName} – ${status} ${dtLabel}`);
        $body.html('<div style="text-align:center; padding:20px; color:var(--text-muted);">Loading…</div>');

        $overlay.show();
        $modal.show();

        frappe.call({
            method: 'crm.api.sm_pipeline_dashboard.get_stage_details',
            args: { user, doctype, status },
            callback: (r) => {
                if (!r || !r.message || r.message.length === 0) {
                    $body.html('<div style="text-align:center; padding:20px; color:var(--text-muted);">No records found.</div>');
                    return;
                }

                if (doctype === 'CRM Lead') {
                    this.render_lead_list($body, r.message);
                } else {
                    this.render_deal_list($body, r.message);
                }
            }
        });
    },

    render_lead_list($body, records) {
        let html = `
            <table style="width:100%; border-collapse:collapse; font-size:13px;">
                <thead>
                    <tr style="background:var(--subtle-bg, #f8f9fa); border-bottom:2px solid var(--border-color);">
                        <th style="padding:8px 12px; text-align:left;">#</th>
                        <th style="padding:8px 12px; text-align:left;">Lead ID</th>
                        <th style="padding:8px 12px; text-align:left;">Organization</th>
                        <th style="padding:8px 12px; text-align:left;">Contact</th>
                        <th style="padding:8px 12px; text-align:left;">Mobile</th>
                    </tr>
                </thead>
                <tbody>
        `;

        records.forEach((rec, idx) => {
            const contact = [rec.first_name, rec.last_name].filter(Boolean).join(' ');
            html += `
                <tr style="border-bottom:1px solid var(--border-color, #eee); cursor:pointer;"
                    onclick="window.open('/app/crm-lead/${rec.id}', '_blank')">
                    <td style="padding:8px 12px; color:var(--text-muted);">${idx + 1}</td>
                    <td style="padding:8px 12px;"><a href="/app/crm-lead/${rec.id}" target="_blank" style="font-weight:600; color:var(--primary-color, #2490ef);">${rec.id}</a></td>
                    <td style="padding:8px 12px;">${rec.organization || '–'}</td>
                    <td style="padding:8px 12px;">${contact || '–'}</td>
                    <td style="padding:8px 12px;">${rec.mobile_no || '–'}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        html += `<div style="padding:8px 12px; font-size:12px; color:var(--text-muted); text-align:right;">${records.length} record(s)</div>`;
        $body.html(html);
    },

    render_deal_list($body, records) {
        let html = `
            <table style="width:100%; border-collapse:collapse; font-size:13px;">
                <thead>
                    <tr style="background:var(--subtle-bg, #f8f9fa); border-bottom:2px solid var(--border-color);">
                        <th style="padding:8px 12px; text-align:left;">#</th>
                        <th style="padding:8px 12px; text-align:left;">Deal ID</th>
                        <th style="padding:8px 12px; text-align:left;">Organization</th>
                        <th style="padding:8px 12px; text-align:left;">Deal Value</th>
                    </tr>
                </thead>
                <tbody>
        `;

        records.forEach((rec, idx) => {
            const org = rec.organization_name || rec.organization || '–';
            const val = rec.deal_value ? ('₹' + parseFloat(rec.deal_value).toLocaleString('en-IN')) : '–';
            html += `
                <tr style="border-bottom:1px solid var(--border-color, #eee); cursor:pointer;"
                    onclick="window.open('/app/crm-deal/${rec.id}', '_blank')">
                    <td style="padding:8px 12px; color:var(--text-muted);">${idx + 1}</td>
                    <td style="padding:8px 12px;"><a href="/app/crm-deal/${rec.id}" target="_blank" style="font-weight:600; color:var(--primary-color, #2490ef);">${rec.id}</a></td>
                    <td style="padding:8px 12px;">${org}</td>
                    <td style="padding:8px 12px;">${val}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        html += `<div style="padding:8px 12px; font-size:12px; color:var(--text-muted); text-align:right;">${records.length} record(s)</div>`;
        $body.html(html);
    },

    close_drilldown($wrapper) {
        $wrapper.find('.sm-drilldown-overlay').hide();
        $wrapper.find('.sm-drilldown-modal').hide();
    }
};
