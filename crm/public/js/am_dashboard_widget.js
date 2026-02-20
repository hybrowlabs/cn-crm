frappe.provide('crm.am_dashboard_widget');

crm.am_dashboard_widget = {

    render(wrapper) {
        const container = $(wrapper);
        container.empty();

        container.html(`
            <div class="am-dashboard-widget" style="padding: 15px; background: var(--card-bg, #fff); border-radius: 8px; box-shadow: var(--shadow-sm, 0px 1px 3px rgba(0,0,0,0.1));">
                <div class="am-dashboard-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <div class="am-dashboard-title" style="font-size: 16px; font-weight: 600; color: var(--text-color, #1f272e);">
                        Account Manager Dashboard
                    </div>
                    <button class="btn btn-sm btn-default refresh-btn">
                        Refresh
                    </button>
                </div>

                <div class="am-dashboard-loading" style="text-align: center; padding: 20px; color: var(--text-muted, #8d99a6);">
                    Loading...
                </div>

                <div class="am-dashboard-content" style="display:none;">
                    <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px;">
                        
                        <!-- Booked Volume -->
                        <div style="flex: 1; min-width: 200px; padding: 15px; background: var(--bg-color, #f8f9fa); border-radius: 6px; border: 1px solid var(--border-color, #d1d8dd);">
                            <div style="font-size: 13px; color: var(--text-muted, #8d99a6); margin-bottom: 5px;">My Booked Volume (Current Month)</div>
                            <div class="booked-volume-val" style="font-size: 24px; font-weight: 700; color: var(--text-color, #1f272e);">₹0</div>
                        </div>

                        <!-- Pipeline Volume -->
                        <div style="flex: 1; min-width: 200px; padding: 15px; background: var(--bg-color, #f8f9fa); border-radius: 6px; border: 1px solid var(--border-color, #d1d8dd);">
                            <div style="font-size: 13px; color: var(--text-muted, #8d99a6); margin-bottom: 5px;">My Pipeline Volume (Opp + Trial + Prop)</div>
                            <div class="pipeline-volume-val" style="font-size: 24px; font-weight: 700; color: var(--primary-color, #2490ef);">₹0</div>
                        </div>

                    </div>

                    <!-- Pain Mix -->
                    <div style="border: 1px solid var(--border-color, #d1d8dd); border-radius: 6px; padding: 15px;">
                        <div style="font-size: 14px; font-weight: 600; margin-bottom: 15px;">My Pain Mix (Active Deals)</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                            <div id="pain-mix-chart" style="flex: 1; min-width: 300px; min-height: 250px;"></div>
                            <div class="pain-mix-list" style="flex: 1; min-width: 200px; max-height: 250px; overflow-y: auto;">
                                <!-- List populated by JS -->
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        `);

        // Refresh
        container.off('click', '.refresh-btn');
        container.on('click', '.refresh-btn', () => {
            this.load_data(container);
        });

        this.load_data(container);
    },

    load_data(container) {
        const loading = container.find('.am-dashboard-loading');
        const content = container.find('.am-dashboard-content');

        loading.show();
        content.hide();

        frappe.call({
            method: 'crm.api.am_dashboard.get_am_dashboard_data',
            callback: (r) => {
                loading.hide();
                content.show();

                if (r.message) {
                    this.render_data(container, r.message);
                }
            }
        });
    },

    render_data(container, data) {
        // Render Volumes
        const formatCurrency = (val) => format_currency(val, frappe.boot.sysdefaults.currency || 'INR');

        container.find('.booked-volume-val').text(formatCurrency(data.booked_volume || 0));
        container.find('.pipeline-volume-val').text(formatCurrency(data.pipeline_volume || 0));

        // Render Pain Mix Chart & List
        const painMix = data.pain_mix || [];
        const listContainer = container.find('.pain-mix-list');
        listContainer.empty();

        if (painMix.length === 0) {
            listContainer.html('<div style="color: var(--text-muted); padding: 10px;">No deals found.</div>');
            container.find('#pain-mix-chart').empty();
            return;
        }

        let labels = [];
        let values = [];
        let htmlList = '<table class="table table-bordered table-hover" style="font-size: 13px; margin: 0;">';
        htmlList += '<thead><tr><th>Pain Category</th><th style="text-align: right;">Deals</th></tr></thead><tbody>';

        painMix.forEach(item => {
            labels.push(item.category);
            values.push(item.value);
            htmlList += `<tr><td>${item.category}</td><td style="text-align: right;">${item.value}</td></tr>`;
        });

        htmlList += '</tbody></table>';
        listContainer.html(htmlList);

        // Initialize Frappe Chart
        if (typeof frappe.Chart !== "undefined") {
            const chartData = {
                labels: labels,
                datasets: [
                    {
                        values: values
                    }
                ]
            };

            new frappe.Chart(container.find('#pain-mix-chart')[0], {
                title: "Deals by Pain Category",
                data: chartData,
                type: 'pie', // or 'donut'
                height: 250,
                colors: ['#2490ef', '#ff5858', '#ffa00a', '#1379b4', '#15cb86', '#eebb00']
            });
        }
    }
};
