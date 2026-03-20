/**
 * tech_team_requests_widget.js
 *
 * Renders technical team requests for the current user.
 */

frappe.provide('crm.tech_team_widget');

crm.tech_team_widget = {

    render(wrapper) {
        try {
            const container = $(wrapper);
            container.empty();

            container.html(`
                <style>
                    .tech-team-widget { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
                    .tech-team-header {
                        display: flex; justify-content: space-between; align-items: center;
                        padding: 12px 16px;
                        background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%);
                        border-radius: 10px 10px 0 0; color: #fff;
                    }
                    .tech-team-title { font-size: 15px; font-weight: 600; letter-spacing: 0.3px; }
                    .tech-refresh-btn {
                        background: rgba(255,255,255,0.15) !important;
                        border: 1px solid rgba(255,255,255,0.2) !important;
                        color: #fff !important; font-size: 12px; padding: 4px 12px;
                        border-radius: 6px; transition: all 0.2s ease;
                    }
                    .tech-refresh-btn:hover { background: rgba(255,255,255,0.25) !important; }
                    .tech-loading  { text-align: center; padding: 24px; color: #94a3b8; font-size: 13px; }
                    .tech-content  {
                        background: #f8fafc; border-radius: 0 0 10px 10px;
                        border: 1px solid #e2e8f0; border-top: none;
                        max-height: 500px; overflow-y: auto;
                    }
                    .tech-empty { text-align: center; padding: 48px 16px; color: #94a3b8; font-size: 14px; }
                    .ttr-card {
                        background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
                        margin: 12px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                    }
                    .ttr-header { display: flex; justify-content: space-between; margin-bottom: 12px; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; }
                    .ttr-deal-name { font-weight: 700; color: #1e293b; font-size: 14px; }
                    .ttr-meta { font-size: 12px; color: #64748b; margin-top: 4px; }
                    .ttr-body { font-size: 13px; color: #334155; line-height: 1.5; margin-bottom: 12px; }
                    .ttr-actions { display: flex; gap: 8px; justify-content: flex-end; }
                    .btn-fill { 
                        background: #4338ca; color: #fff; border: none; padding: 6px 12px; 
                        border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer;
                    }
                    
                    /* Multi-select styles */
                    .ttr-ms-container { position: relative; width: 100%; }
                    .ttr-ms-input-box {
                        display: flex; flex-wrap: wrap; gap: 4px; padding: 6px;
                        border: 1.5px solid #e2e8f0; border-radius: 6px; background: #fff;
                        min-height: 38px; cursor: text; align-items: center;
                    }
                    .ttr-ms-input-box:focus-within { border-color: #4338ca; box-shadow: 0 0 0 2px rgba(67, 56, 202, 0.1); }
                    .ttr-ms-tag {
                        background: #eef2ff; color: #4338ca; font-size: 12px; font-weight: 600;
                        padding: 2px 8px; border-radius: 4px; display: flex; align-items: center; gap: 4px;
                        border: 1px solid #c7d2fe;
                    }
                    .ttr-ms-tag-remove { cursor: pointer; color: #6366f1; font-weight: bold; margin-left: 2px; }
                    .ttr-ms-tag-remove:hover { color: #4338ca; }
                    .ttr-ms-search { border: none; outline: none; font-size: 13px; flex: 1; min-width: 100px; padding: 4px; background: transparent; }
                    .ttr-ms-placeholder { color: #94a3b8; font-size: 13px; padding-left: 4px; pointer-events: none; }
                    .ttr-ms-icon { color: #94a3b8; margin: 0 8px; flex-shrink: 0; }
                    .ttr-ms-dropdown {
                        position: absolute; top: 100%; left: 0; right: 0; z-index: 100;
                        background: #fff; border: 1px solid #e2e8f0; border-radius: 6px;
                        margin-top: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                        max-height: 200px; overflow-y: auto; display: none;
                    }
                    .ttr-ms-option {
                        padding: 10px 14px; font-size: 13px; color: #334155; cursor: pointer;
                        display: flex; justify-content: space-between; align-items: center; transition: all 0.1s;
                        border-bottom: 1px solid #f8fafc;
                    }
                    .ttr-ms-option:last-child { border-bottom: none; }
                    .ttr-ms-option:hover { background: #f8fafc; color: #4338ca; }
                    .ttr-ms-option.selected { background: #eff6ff; color: #1d4ed8; font-weight: 600; }
                    .ttr-ms-option-sub { font-size: 11px; color: #64748b; margin-top: 2px; font-weight: normal; }
                    .ttr-ms-no-results { padding: 16px; text-align: center; color: #94a3b8; font-size: 13px; }
                </style>
                <div class="tech-team-widget">
                    <div class="tech-team-header">
                        <div class="tech-team-title">Pending Technical Team Requests</div>
                        <button class="btn btn-sm tech-refresh-btn">Refresh</button>
                    </div>
                    <div class="tech-loading">Loading requests...</div>
                    <div class="tech-content" style="display:none;">
                        <div class="tech-requests-list"></div>
                        <div class="tech-empty" style="display:none;">All clear! No pending requests. 🎯</div>
                    </div>
                </div>
            `);

            container.off('click', '.tech-refresh-btn');
            container.on('click', '.tech-refresh-btn', () => this.load_data(container));

            this.load_data(container);
        } catch (err) {
            console.error("Error in tech_team_widget.render:", err);
            $(wrapper).html('<div style="padding:15px;color:red;">Failed to render Technical Team Requests.</div>');
        }
    },

    load_data(container) {
        const loading = container.find('.tech-loading');
        const content = container.find('.tech-content');
        const list = container.find('.tech-requests-list');
        const empty = container.find('.tech-empty');

        loading.show();
        content.hide();

        frappe.call({
            method: 'crm.api.tech_team.get_requests',
            callback: (r) => {
                loading.hide();
                content.show();
                if (r.message && r.message.length) {
                    this.render_requests(list, r.message);
                    empty.hide();
                    list.show();
                } else {
                    list.hide();
                    empty.show();
                }
            }
        });
    },

    render_requests(container, requests) {
        container.empty();
        requests.forEach(req => {
            const card = $(`
                <div class="ttr-card">
                    <div class="ttr-header">
                        <div>
                            <div class="ttr-deal-name">${req.organization || req.deal}</div>
                            <div class="ttr-meta">Req: ${req.name} | Category: ${req.product_category || 'N/A'}</div>
                        </div>
                    </div>
                    <div class="ttr-body">
                        <div><strong>Commercial Pain:</strong> ${req.commercial_pain_category || 'N/A'}</div>
                        <div><strong>Technical Pain:</strong> ${req.technical_pain_category || 'N/A'}</div>
                        <div style="margin-top:8px; font-style: italic; color: #475569;">"${req.notes_by_sales_team || 'No notes provided by sales.'}"</div>
                    </div>
                    <div class="ttr-actions">
                        <button class="btn-fill act-on-btn" data-name="${req.name}">Fill & Act</button>
                    </div>
                </div>
            `);
            
            card.find('.act-on-btn').on('click', () => this.open_action_modal(req));
            container.append(card);
        });
    },

    open_action_modal(req) {
        // Fetch products for multi-select
        frappe.call({
            method: 'crm.api.tech_team.get_products',
            callback: (r) => {
                const products = r.message || [];
                this.show_modal(req, products);
            }
        });
    },

    show_modal(req, product_options) {
        const title = `Act on Request: ${req.name}`;
        
        let product_html = product_options.map(p => `
            <div style="margin-bottom:4px;">
                <label style="display:flex; align-items:center; gap:8px; cursor:pointer; font-size:13px;">
                    <input type="checkbox" name="product" value="${p.name}" style="accent-color:#4338ca;">
                    ${p.product_name || p.name} (${p.product_category || 'No Category'})
                </label>
            </div>
        `).join('');

        const bodyHtml = `
            <div style="padding:4px;">
                <div style="margin-bottom:16px;">
                    <label style="display:block; font-size:13px; font-weight:600; color:#1e293b; margin-bottom:6px;">
                        Select Products <span style="color:red;">*</span>
                    </label>
                    
                    <div class="ttr-ms-container">
                        <div class="ttr-ms-input-box">
                            <span class="ttr-ms-icon search-icon">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                            </span>
                            <div class="ttr-ms-tags-list" style="display:flex; flex-wrap:wrap; gap:4px;"></div>
                            <input type="text" class="ttr-ms-search" placeholder="Search products...">
                            <span class="ttr-ms-icon chevron-icon">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                            </span>
                        </div>
                        <div class="ttr-ms-dropdown">
                            <div class="ttr-ms-options-list"></div>
                        </div>
                    </div>
                    
                    <p style="font-size:11px; color:#64748b; margin-top:4px;">At least one product is mandatory.</p>
                </div>
                
                <div style="margin-bottom:20px;">
                    <label style="display:block; font-size:13px; font-weight:600; color:#1e293b; margin-bottom:6px;">
                        Technical Description
                    </label>
                    <textarea class="ttr-desc" style="width:100%; height:80px; padding:10px; border-radius:6px; border:1.5px solid #e2e8f0; font-size:13px; resize:none;" placeholder="Enter technical details (optional)..."></textarea>
                </div>

                <div style="display:flex; gap:12px; justify-content:flex-end; margin-top:10px;">
                    <button class="modal-reject-btn" style="background:#ef4444; color:#fff; border:none; padding:8px 20px; border-radius:6px; font-size:13px; font-weight:600; cursor:pointer;">Reject</button>
                    <button class="modal-approve-btn" style="background:#10b981; color:#fff; border:none; padding:8px 20px; border-radius:6px; font-size:13px; font-weight:600; cursor:pointer;">Approve</button>
                </div>
            </div>
        `;

        crm._widget_utils._show_modal(title, bodyHtml, (overlay) => {
            const searchInput = overlay.querySelector('.ttr-ms-search');
            const dropdown = overlay.querySelector('.ttr-ms-dropdown');
            const optionsList = overlay.querySelector('.ttr-ms-options-list');
            const tagsList = overlay.querySelector('.ttr-ms-tags-list');
            
            let selected = [];

            const renderTags = () => {
                tagsList.innerHTML = '';
                selected.forEach(val => {
                    const opt = product_options.find(p => p.name === val);
                    const tag = document.createElement('div');
                    tag.className = 'ttr-ms-tag';
                    tag.innerHTML = `
                        <span>${opt ? opt.product_name || opt.name : val}</span>
                        <span class="ttr-ms-tag-remove" data-val="${val}">&times;</span>
                    `;
                    tag.querySelector('.ttr-ms-tag-remove').addEventListener('click', (e) => {
                        e.stopPropagation();
                        removeSelection(val);
                    });
                    tagsList.appendChild(tag);
                });
            };

            const renderOptions = (filter = '') => {
                optionsList.innerHTML = '';
                const filtered = product_options.filter(p => 
                    (p.product_name || '').toLowerCase().includes(filter.toLowerCase()) || 
                    (p.name || '').toLowerCase().includes(filter.toLowerCase()) ||
                    (p.product_category || '').toLowerCase().includes(filter.toLowerCase())
                );

                if (filtered.length === 0) {
                    optionsList.innerHTML = '<div class="ttr-ms-no-results">No matches found for "' + filter + '"</div>';
                    return;
                }

                filtered.forEach(p => {
                    const isSelected = selected.includes(p.name);
                    const opt = document.createElement('div');
                    opt.className = `ttr-ms-option ${isSelected ? 'selected' : ''}`;
                    opt.innerHTML = `
                        <div>
                            <div class="ttr-ms-option-name">${p.product_name || p.name}</div>
                            <div class="ttr-ms-option-sub">${p.product_category || 'General'} | ${p.name}</div>
                        </div>
                        ${isSelected ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="color:#1d4ed8;"><polyline points="20 6 9 17 4 12"></polyline></svg>' : ''}
                    `;
                    opt.addEventListener('click', () => {
                        toggleSelection(p.name);
                    });
                    optionsList.appendChild(opt);
                });
            };

            const toggleSelection = (val) => {
                if (selected.includes(val)) {
                    selected = selected.filter(v => v !== val);
                } else {
                    selected.push(val);
                }
                renderTags();
                renderOptions(searchInput.value);
            };

            const removeSelection = (val) => {
                selected = selected.filter(v => v !== val);
                renderTags();
                renderOptions(searchInput.value);
            };

            searchInput.addEventListener('focus', () => {
                dropdown.style.display = 'block';
                renderOptions(searchInput.value);
            });

            document.addEventListener('click', (e) => {
                if (!e.target.closest('.ttr-ms-container')) {
                    dropdown.style.display = 'none';
                }
            }, { capture: true });

            searchInput.addEventListener('input', (e) => {
                renderOptions(e.target.value);
            });

            const handleAction = (action) => {
                const description = overlay.querySelector('.ttr-desc').value;

                if (action === 'approve' && selected.length === 0) {
                    frappe.show_alert({ message: 'Please select at least one product for approval', indicator: 'red' });
                    return;
                }

                frappe.call({
                    method: 'crm.api.tech_team.act_on_request',
                    args: {
                        request_name: req.name,
                        action: action,
                        products: JSON.stringify(selected),
                        description: description
                    },
                    callback: (r) => {
                        if (r.message) {
                            frappe.show_alert({ message: `Request ${action}d successfully`, indicator: 'green' });
                            overlay.remove();
                            this.load_data($('.tech-team-widget').parent()); // Refresh widget
                        }
                    }
                });
            };

            overlay.querySelector('.modal-approve-btn').addEventListener('click', () => handleAction('approve'));
            overlay.querySelector('.modal-reject-btn').addEventListener('click', () => handleAction('reject'));
        });
    }
};
