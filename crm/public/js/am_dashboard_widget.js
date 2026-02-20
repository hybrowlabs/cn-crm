frappe.provide('crm.am_dashboard_widget');

crm.am_dashboard_widget = {

    render(wrapper) {
        console.log("AM Dashboard: Starting execution on wrapper", wrapper);

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
                            <div class="pain-mix-chart" style="flex: 1; min-width: 300px; min-height: 250px;"></div>
                            <div class="pain-mix-list" style="flex: 1; min-width: 200px; max-height: 250px; overflow-y: auto;">
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        `;

        $wrapper.append(widget_html);
        console.log("AM Dashboard: HTML appended successfully to wrapper.");

        // Attach refresh
        $wrapper.off('click', '.refresh-btn');
        $wrapper.on('click', '.refresh-btn', () => {
            console.log("AM Dashboard: Refresh clicked");
            this.load_data($wrapper);
        });

        // Load data immediately
        this.load_data($wrapper);
    },

    load_data($wrapper) {
        console.log("AM Dashboard: load_data started");
        const loading = $wrapper.find('.am-dashboard-loading');
        const content = $wrapper.find('.am-dashboard-content');

        loading.show();
        content.hide();

        frappe.call({
            method: 'crm.api.am_dashboard.get_am_dashboard_data',
            callback: (r) => {
                console.log("AM Dashboard: API Response received", r);
                loading.hide();
                content.show();
                content.css('display', 'block'); // Force display block

                if (r && r.message) {
                    this.render_data($wrapper, r.message);
                } else {
                    console.log("AM Dashboard: No message in API response");
                }
            }
        });
    },

    render_data($wrapper, data) {
        console.log("AM Dashboard: rendering data onto DOM");
        try {
            // Render Volumes
            const getValidCurrency = () => {
                if (typeof frappe !== 'undefined' && frappe.boot && frappe.boot.sysdefaults && frappe.boot.sysdefaults.currency) {
                    return frappe.boot.sysdefaults.currency;
                }
                return 'INR';
            };

            const formatCurrencyFallback = (val) => {
                if (typeof format_currency === 'function') {
                    return format_currency(val, getValidCurrency());
                }
                return '₹' + parseFloat(val || 0).toLocaleString('en-IN');
            };

            $wrapper.find('.booked-volume-val').text(formatCurrencyFallback(data.booked_volume || 0));
            $wrapper.find('.pipeline-volume-val').text(formatCurrencyFallback(data.pipeline_volume || 0));

            // Render Pain Mix List
            const painMix = data.pain_mix || [];
            const listContainer = $wrapper.find('.pain-mix-list');
            listContainer.empty();

            if (painMix.length === 0) {
                console.log("AM Dashboard: No Pain Mix data.");
                listContainer.html('<div style="color: var(--text-muted); padding: 10px;">No deals found.</div>');
                $wrapper.find('.pain-mix-chart').empty();
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
            console.log("AM Dashboard: Pain Mix list rendered");

            // Chart Render - Safe fallback for Custom HTML blocks
            setTimeout(() => {
                if (typeof frappe.Chart !== 'undefined') {
                    console.log("AM Dashboard: Creating pie chart...");
                    try {
                        const chartData = {
                            labels: labels,
                            datasets: [{ values: values }]
                        };

                        new frappe.Chart($wrapper.find('.pain-mix-chart')[0], {
                            title: "Deals by Pain Category",
                            data: chartData,
                            type: 'pie',
                            height: 250,
                            colors: ['#2490ef', '#ff5858', '#ffa00a', '#1379b4', '#15cb86', '#eebb00']
                        });
                        console.log("AM Dashboard: Pie chart rendered safely");
                    } catch (err) {
                        console.error("AM Dashboard: Chart rendering failed", err);
                    }
                } else {
                    console.warn("AM Dashboard: frappe.Chart is undefined! Cannot draw Pie chart.");
                    $wrapper.find('.pain-mix-chart').html('<div style="color: var(--text-muted); padding: 10px; border: 1px dashed var(--border-color); border-radius: 4px; display: flex; align-items: center; justify-content: center; height: 100%;">Pie chart library not loaded by workspace.</div>');
                }
            }, 100);

        } catch (e) {
            console.error("AM Dashboard: Render Error caught in Try-Catch!", e);
        }
    }
};
