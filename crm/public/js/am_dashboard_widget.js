frappe.provide('crm.am_dashboard_widget');

crm.am_dashboard_widget = {

    render(wrapper) {

        let $wrapper = $(wrapper);
        $wrapper.empty();

        let widget_html = `
            <div class="am-dashboard-widget" style="padding: 15px; background: var(--card-bg, #fff); border-radius: 8px; box-shadow: var(--shadow-sm, 0px 1px 3px rgba(0,0,0,0.1));">
                <div class="am-dashboard-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <div class="am-dashboard-title" style="font-size: 16px; font-weight: 600; color: var(--text-color, #1f272e);">
                        Account Manager Dashboard
                    </div>
                    <button class="btn btn-sm btn-default refresh-btn">Refresh</button>
                </div>

                <div class="am-dashboard-loading" style="text-align: center; padding: 20px; color: var(--text-muted, #8d99a6);">
                    Loading Data...
                </div>

                <div class="am-dashboard-content" style="display:none; width: 100%;">
                    <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px;">
                        
                        <!-- Booked Volume -->
                        <div style="flex: 1; min-width: 200px; padding: 15px; background: var(--bg-color, #f8f9fa); border-radius: 6px; border: 1px solid var(--border-color, #d1d8dd);">
                            <div style="font-size: 13px; color: var(--text-muted, #8d99a6); margin-bottom: 5px;">My Booked Volume (Current Month)</div>
                            <div class="booked-volume-val" style="font-size: 24px; font-weight: 700; color: var(--text-color, #1f272e);">0</div>
                        </div>

                        <!-- Pipeline Volume -->
                        <div style="flex: 1; min-width: 200px; padding: 15px; background: var(--bg-color, #f8f9fa); border-radius: 6px; border: 1px solid var(--border-color, #d1d8dd);">
                            <div style="font-size: 13px; color: var(--text-muted, #8d99a6); margin-bottom: 5px;">My Pipeline Volume (Opp + Trial + Prop)</div>
                            <div class="pipeline-volume-val" style="font-size: 24px; font-weight: 700; color: var(--primary-color, #2490ef);">0</div>
                        </div>

                    </div>

                    <!-- Pain Mix Row -->
                    <div style="display: flex; gap: 20px; flex-wrap: wrap;">

                        <!-- Commercial Pain Category -->
                        <div style="flex: 1; min-width: 300px; border: 1px solid var(--border-color, #d1d8dd); border-radius: 6px; padding: 15px;">
                            <div style="font-size: 14px; font-weight: 600; margin-bottom: 15px;">Commercial Pain Category (Active Deals)</div>
                            <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                                <div class="pain-mix-chart" style="flex: 1; min-width: 280px; min-height: 250px;"></div>
                                <div class="pain-mix-list" style="flex: 1; min-width: 180px; max-height: 250px; overflow-y: auto;"></div>
                            </div>
                        </div>

                        <!-- Technical Pain Category -->
                        <div style="flex: 1; min-width: 300px; border: 1px solid var(--border-color, #d1d8dd); border-radius: 6px; padding: 15px;">
                            <div style="font-size: 14px; font-weight: 600; margin-bottom: 15px;">Technical Pain Category (Active Deals)</div>
                            <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                                <div class="tech-pain-mix-chart" style="flex: 1; min-width: 280px; min-height: 250px;"></div>
                                <div class="tech-pain-mix-list" style="flex: 1; min-width: 180px; max-height: 250px; overflow-y: auto;"></div>
                            </div>
                        </div>

                    </div>

                </div>
            </div>
        `;

        $wrapper.append(widget_html);

        // Attach refresh
        $wrapper.off('click', '.refresh-btn');
        $wrapper.on('click', '.refresh-btn', () => {
            this.load_data($wrapper);
        });

        // Load data immediately
        this.load_data($wrapper);
    },

    load_data($wrapper) {
        const loading = $wrapper.find('.am-dashboard-loading');
        const content = $wrapper.find('.am-dashboard-content');

        loading.show();
        content.hide();

        frappe.call({
            method: 'crm.api.am_dashboard.get_am_dashboard_data',
            callback: (r) => {
                loading.hide();
                content.show();
                content.css('display', 'block'); // Force display block

                if (r && r.message) {
                    this.render_data($wrapper, r.message);
                } else {
                }
            }
        });
    },

    render_data($wrapper, data) {
        console.log("AM Dashboard: rendering data onto DOM");
        try {
            // Render Volumes
            const formatFloatFallback = (val) => {
                return parseFloat(val || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 });
            };

            $wrapper.find('.booked-volume-val').text(formatFloatFallback(data.booked_volume || 0));
            $wrapper.find('.pipeline-volume-val').text(formatFloatFallback(data.pipeline_volume || 0));

            // ── Helper to render a pie chart + table ──────────────────────────────
            const renderPainSection = (data_items, chartSelector, listSelector, chartTitle) => {
                const listContainer = $wrapper.find(listSelector);
                listContainer.empty();

                if (!data_items || data_items.length === 0) {
                    listContainer.html('<div style="color: var(--text-muted); padding: 10px;">No deals found.</div>');
                    $wrapper.find(chartSelector).empty();
                    return;
                }

                let labels = [];
                let values = [];
                let htmlList = '<table class="table table-bordered table-hover" style="font-size: 13px; margin: 0;">';
                htmlList += '<thead><tr><th>Category</th><th style="text-align: right;">Deals</th></tr></thead><tbody>';

                data_items.forEach(item => {
                    labels.push(item.category);
                    values.push(item.value);
                    htmlList += `<tr><td>${item.category}</td><td style="text-align: right;">${item.value}</td></tr>`;
                });

                htmlList += '</tbody></table>';
                listContainer.html(htmlList);

                setTimeout(() => {
                    if (typeof frappe.Chart !== 'undefined') {
                        try {
                            const chartContainer = $wrapper.find(chartSelector)[0];
                            if (chartContainer) {
                                if (chartContainer._frappe_chart) {
                                    try {
                                        if (chartContainer._frappe_chart.destroy) chartContainer._frappe_chart.destroy();
                                    } catch (e) { /* ignore */ }
                                    delete chartContainer._frappe_chart;
                                }
                                $(chartContainer).empty();
                                chartContainer._frappe_chart = new frappe.Chart(chartContainer, {
                                    title: chartTitle,
                                    data: { labels, datasets: [{ values }] },
                                    type: 'pie',
                                    height: 250,
                                    colors: ['#2490ef', '#ff5858', '#ffa00a', '#1379b4', '#15cb86', '#eebb00']
                                });
                            }
                        } catch (err) {
                            console.error("AM Dashboard: Chart rendering failed", err);
                        }
                    } else {
                        $wrapper.find(chartSelector).html('<div style="color: var(--text-muted); padding: 10px;">Pie chart library not loaded.</div>');
                    }
                }, 100);
            };

            // Render Commercial Pain Category
            renderPainSection(data.pain_mix || [], '.pain-mix-chart', '.pain-mix-list', 'Deals by Commercial Pain Category');

            // Render Technical Pain Category
            renderPainSection(data.technical_pain_mix || [], '.tech-pain-mix-chart', '.tech-pain-mix-list', 'Deals by Technical Pain Category');

        } catch (e) {
            console.error("AM Dashboard: Render Error caught in Try-Catch!", e);
        }
    }
};
