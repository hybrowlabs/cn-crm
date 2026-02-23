frappe.provide('crm.frequency_bucket_widget');

crm.frequency_bucket_widget = {

    render(wrapper) {

        const container = $(wrapper);
        container.empty();

        container.html(`
			<style>
				.freq-bucket-widget {
					font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
				}
				.freq-bucket-header {
					display: flex;
					justify-content: space-between;
					align-items: center;
					padding: 12px 16px;
					background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
					border-radius: 10px 10px 0 0;
					color: #fff;
				}
				.freq-bucket-title {
					font-size: 15px;
					font-weight: 600;
					letter-spacing: 0.3px;
				}
				.freq-refresh-btn {
					background: rgba(255,255,255,0.15) !important;
					border: 1px solid rgba(255,255,255,0.2) !important;
					color: #fff !important;
					font-size: 12px;
					padding: 4px 12px;
					border-radius: 6px;
					transition: all 0.2s ease;
				}
				.freq-refresh-btn:hover {
					background: rgba(255,255,255,0.25) !important;
				}
				.freq-loading {
					text-align: center;
					padding: 24px;
					color: #94a3b8;
					font-size: 13px;
				}
				.freq-content {
					background: #f8fafc;
					border-radius: 0 0 10px 10px;
					border: 1px solid #e2e8f0;
					border-top: none;
				}
				.freq-empty {
					text-align: center;
					padding: 32px 16px;
					color: #94a3b8;
					font-size: 14px;
				}

				/* Bucket Section */
				.freq-bucket-section {
					border-bottom: 2px solid #e2e8f0;
				}
				.freq-bucket-section:last-child {
					border-bottom: none;
				}
				.freq-bucket-bar {
					display: flex;
					justify-content: space-between;
					align-items: center;
					padding: 11px 16px;
					cursor: pointer;
					transition: background 0.15s ease;
				}
				.freq-bucket-bar:hover {
					background: #e0e7ff !important;
				}
				.freq-bucket-bar-left {
					display: flex;
					align-items: center;
					gap: 10px;
				}
				.freq-bucket-label {
					font-size: 14px;
					font-weight: 700;
					color: #1e293b;
				}
				.freq-bucket-count {
					font-size: 10px;
					font-weight: 700;
					padding: 2px 8px;
					border-radius: 10px;
					color: #fff;
					min-width: 22px;
					text-align: center;
				}
				.freq-bucket-chevron {
					font-size: 10px;
					color: #64748b;
					transition: transform 0.25s ease;
					display: inline-block;
				}
				.freq-bucket-chevron.rotate {
					transform: rotate(90deg);
				}
				.freq-bucket-body {
					max-height: 0;
					overflow: hidden;
					transition: max-height 0.35s ease;
				}
				.freq-bucket-body.open {
					max-height: 8000px;
				}

				/* Customer card inside bucket */
				.freq-customer-card {
					border-bottom: 1px solid #e2e8f0;
				}
				.freq-customer-card:last-child {
					border-bottom: none;
				}
				.freq-customer-hdr {
					display: flex;
					justify-content: space-between;
					align-items: center;
					padding: 10px 16px;
					cursor: pointer;
					transition: background 0.15s ease;
					background: #fff;
				}
				.freq-customer-hdr:hover {
					background: #eef2f7;
				}
				.freq-customer-link {
					font-size: 13px;
					font-weight: 600;
					color: #1e293b;
					cursor: pointer;
					transition: color 0.15s ease;
				}
				.freq-customer-link:hover {
					color: #3b82f6;
				}
				.freq-cust-right {
					display: flex;
					align-items: center;
					gap: 8px;
				}
				.freq-cust-item-count {
					font-size: 11px;
					color: #64748b;
				}
				.freq-cust-chevron {
					font-size: 9px;
					color: #94a3b8;
					transition: transform 0.25s ease;
					display: inline-block;
				}
				.freq-cust-chevron.rotate {
					transform: rotate(90deg);
				}
				.freq-customer-items {
					max-height: 0;
					overflow: hidden;
					transition: max-height 0.3s ease;
					background: #ffffff;
				}
				.freq-customer-items.open {
					max-height: 3000px;
				}

				/* Table inside customer */
				.freq-table {
					width: 100%;
					border-collapse: collapse;
					font-size: 12px;
				}
				.freq-table thead th {
					background: #f1f5f9;
					color: #475569;
					font-weight: 600;
					font-size: 11px;
					text-transform: uppercase;
					letter-spacing: 0.5px;
					padding: 8px 12px;
					text-align: left;
					border-bottom: 2px solid #e2e8f0;
				}
				.freq-table tbody td {
					padding: 8px 12px;
					color: #334155;
					border-bottom: 1px solid #f1f5f9;
					vertical-align: middle;
				}
				.freq-table tbody tr:last-child td {
					border-bottom: none;
				}
				.freq-table tbody tr:hover td {
					background: #f8fafc;
				}
				.freq-table .td-item {
					font-weight: 500;
				}
				.freq-table .td-freq {
					font-weight: 600;
					color: #1d4ed8;
				}
				.freq-table .td-date.overdue {
					color: #dc2626;
					font-weight: 600;
				}
				.freq-table .td-date.due-today {
					color: #d97706;
					font-weight: 600;
				}
				.freq-table .td-date.upcoming {
					color: #16a34a;
				}
				.freq-table .td-date.no-date {
					color: #94a3b8;
				}
			</style>

			<div class="freq-bucket-widget">
				<div class="freq-bucket-header">
					<div class="freq-bucket-title">Order Frequency Buckets</div>
					<button class="btn btn-sm freq-refresh-btn">Refresh</button>
				</div>

				<div class="freq-loading">Loading...</div>

				<div class="freq-content" style="display:none;">
					<div class="freq-bucket-list"></div>
					<div class="freq-empty" style="display:none;">No frequency data available</div>
				</div>
			</div>
		`);

        // Refresh
        container.off('click', '.freq-refresh-btn');
        container.on('click', '.freq-refresh-btn', () => {
            this.load_data(container);
        });

        // Toggle bucket
        container.off('click', '.freq-bucket-bar');
        container.on('click', '.freq-bucket-bar', function () {
            const section = $(this).closest('.freq-bucket-section');
            const body = section.find('.freq-bucket-body');
            const icon = $(this).find('.freq-bucket-chevron');
            const isOpen = body.hasClass('open');

            container.find('.freq-bucket-body').removeClass('open');
            container.find('.freq-bucket-chevron').removeClass('rotate');

            if (!isOpen) {
                body.addClass('open');
                icon.addClass('rotate');
            }
        });

        // Toggle customer items
        container.off('click', '.freq-customer-hdr');
        container.on('click', '.freq-customer-hdr', function () {
            const card = $(this).closest('.freq-customer-card');
            const items = card.find('.freq-customer-items');
            const icon = $(this).find('.freq-cust-chevron');
            const isOpen = items.hasClass('open');

            // close all in this bucket
            card.closest('.freq-bucket-body').find('.freq-customer-items').removeClass('open');
            card.closest('.freq-bucket-body').find('.freq-cust-chevron').removeClass('rotate');

            if (!isOpen) {
                items.addClass('open');
                icon.addClass('rotate');
            }
        });

        // Open customer doc
        container.off('click', '.freq-customer-link');
        container.on('click', '.freq-customer-link', function (e) {
            e.stopPropagation();
            const name = $(this).data('name');
            frappe.set_route('Form', 'Customer', name);
        });

        this.load_data(container);
    },

    // -------------------------------------------

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
                    this.render_buckets(list, r.message.buckets, container);
                    empty.hide();
                    list.show();
                } else {
                    list.hide();
                    empty.show();
                }
            }
        });
    },

    // -------------------------------------------

    _bucket_colors: [
        { bg: '#10b981', bar: '#ecfdf5' },
        { bg: '#3b82f6', bar: '#eff6ff' },
        { bg: '#f59e0b', bar: '#fffbeb' },
        { bg: '#6b7280', bar: '#f9fafb' },
    ],

    // -------------------------------------------

    render_buckets(container, buckets, widget) {
        container.empty();
        const today = frappe.datetime.get_today();

        buckets.forEach((bucket, bIdx) => {
            const palette = this._bucket_colors[bIdx % this._bucket_colors.length];

            const section = $(`
				<div class="freq-bucket-section">
					<div class="freq-bucket-bar" style="background:${palette.bar};">
						<div class="freq-bucket-bar-left">
							<span class="freq-bucket-chevron">▶</span>
							<span class="freq-bucket-label">${bucket.label}</span>
							<span class="freq-bucket-count" style="background:${palette.bg};">
								${bucket.count}
							</span>
						</div>
					</div>
					<div class="freq-bucket-body"></div>
				</div>
			`);

            const body = section.find('.freq-bucket-body');

            bucket.customers.forEach(customer => {

                const custCard = $(`
					<div class="freq-customer-card">
						<div class="freq-customer-hdr">
							<div>
								<strong class="freq-customer-link"
										data-name="${customer.customer_code}">
									${customer.customer_name}
								</strong>
							</div>
							<div class="freq-cust-right">
								<span class="freq-cust-item-count">${customer.items.length} item${customer.items.length !== 1 ? 's' : ''}</span>
								<span class="freq-cust-chevron">▶</span>
							</div>
						</div>
						<div class="freq-customer-items"></div>
					</div>
				`);

                const itemsContainer = custCard.find('.freq-customer-items');

                // Build table
                let tableHTML = `
					<table class="freq-table">
						<thead>
							<tr>
								<th>Item Name</th>
								<th>Qty</th>
								<th>Frequency Day</th>
								<th>Next Order Date</th>
							</tr>
						</thead>
						<tbody>
				`;

                customer.items.forEach(item => {
                    let dateClass = 'upcoming';
                    let dateLabel = '';
                    if (item.next_order_date) {
                        dateLabel = frappe.datetime.str_to_user(item.next_order_date);
                        if (item.next_order_date < today) dateClass = 'overdue';
                        else if (item.next_order_date === today) dateClass = 'due-today';
                    } else {
                        dateLabel = 'N/A';
                        dateClass = 'no-date';
                    }

                    tableHTML += `
						<tr>
							<td class="td-item">${item.item}</td>
							<td>${item.quantity || 0}</td>
							<td class="td-freq">${item.frequency_day}</td>
							<td class="td-date ${dateClass}">${dateLabel}</td>
						</tr>
					`;
                });

                tableHTML += `</tbody></table>`;
                itemsContainer.html(tableHTML);

                body.append(custCard);
            });

            container.append(section);
        });
    }
};
