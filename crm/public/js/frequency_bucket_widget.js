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
				}
				.freq-empty {
					text-align: center;
					padding: 32px 16px;
					color: #94a3b8;
					font-size: 14px;
				}

				/* Bucket sections */
				.freq-bucket-section {
					border-bottom: 1px solid #e2e8f0;
				}
				.freq-bucket-section:last-child {
					border-bottom: none;
				}
				.freq-bucket-bar {
					display: flex;
					justify-content: space-between;
					align-items: center;
					padding: 10px 16px;
					cursor: pointer;
					transition: background 0.15s ease;
					background: #fff;
				}
				.freq-bucket-bar:hover {
					background: #f1f5f9;
				}
				.freq-bucket-bar-left {
					display: flex;
					align-items: center;
					gap: 10px;
				}
				.freq-bucket-label {
					font-size: 14px;
					font-weight: 600;
					color: #1e293b;
				}
				.freq-bucket-count {
					font-size: 11px;
					font-weight: 700;
					padding: 2px 8px;
					border-radius: 10px;
					color: #fff;
				}
				.freq-bucket-chevron {
					font-size: 10px;
					color: #94a3b8;
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
					background: #f8fafc;
				}
				.freq-bucket-body.open {
					max-height: 5000px;
				}

				/* Customer inside bucket */
				.freq-customer-card {
					border-top: 1px solid #e2e8f0;
				}
				.freq-customer-header {
					display: flex;
					justify-content: space-between;
					align-items: center;
					padding: 8px 16px 8px 28px;
					cursor: pointer;
					transition: background 0.15s ease;
				}
				.freq-customer-header:hover {
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
					max-height: 2000px;
				}

				/* Item rows */
				.freq-item-row {
					display: flex;
					justify-content: space-between;
					align-items: center;
					padding: 8px 16px 8px 44px;
					border-top: 1px solid #f1f5f9;
					transition: background 0.15s ease;
				}
				.freq-item-row:hover {
					background: #f8fafc;
				}
				.freq-item-name {
					font-size: 13px;
					font-weight: 500;
					color: #334155;
					margin-bottom: 2px;
				}
				.freq-item-meta {
					font-size: 11px;
					color: #64748b;
					line-height: 1.5;
				}
				.freq-item-meta span {
					display: inline-block;
					margin-right: 10px;
				}
				.freq-day-badge {
					font-size: 11px;
					font-weight: 600;
					padding: 2px 8px;
					border-radius: 10px;
					background: #f0f9ff;
					color: #0284c7;
					border: 1px solid #bae6fd;
					white-space: nowrap;
				}

				/* Next order date status colours */
				.freq-next-date-overdue {
					color: #dc2626;
					font-weight: 600;
				}
				.freq-next-date-today {
					color: #d97706;
					font-weight: 600;
				}
				.freq-next-date-upcoming {
					color: #16a34a;
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

        // ----- Refresh -----
        container.off('click', '.freq-refresh-btn');
        container.on('click', '.freq-refresh-btn', () => {
            this.load_data(container);
        });

        // ----- Toggle bucket -----
        container.off('click', '.freq-bucket-bar');
        container.on('click', '.freq-bucket-bar', function () {
            const section = $(this).closest('.freq-bucket-section');
            const body = section.find('.freq-bucket-body');
            const icon = $(this).find('.freq-bucket-chevron');

            const isOpen = body.hasClass('open');

            // close all buckets
            container.find('.freq-bucket-body').removeClass('open');
            container.find('.freq-bucket-chevron').removeClass('rotate');

            if (!isOpen) {
                body.addClass('open');
                icon.addClass('rotate');
            }
        });

        // ----- Toggle customer inside bucket -----
        container.off('click', '.freq-customer-header');
        container.on('click', '.freq-customer-header', function () {
            const card = $(this).closest('.freq-customer-card');
            const items = card.find('.freq-customer-items');
            const icon = $(this).find('.freq-cust-chevron');

            const isOpen = items.hasClass('open');

            // close all customers inside THIS bucket
            card.closest('.freq-bucket-body').find('.freq-customer-items').removeClass('open');
            card.closest('.freq-bucket-body').find('.freq-cust-chevron').removeClass('rotate');

            if (!isOpen) {
                items.addClass('open');
                icon.addClass('rotate');
            }
        });

        // ----- Open customer doc -----
        container.off('click', '.freq-customer-link');
        container.on('click', '.freq-customer-link', function (e) {
            e.stopPropagation();
            const customerName = $(this).data('name');
            frappe.set_route('Form', 'Customer', customerName);
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

    _bucket_color(index) {
        const colors = [
            '#10b981', // green
            '#3b82f6', // blue
            '#8b5cf6', // violet
            '#f59e0b', // amber
            '#ef4444', // red
            '#6b7280', // gray
        ];
        return colors[index % colors.length];
    },

    // -------------------------------------------

    render_buckets(container, buckets, widget) {
        container.empty();

        const today = frappe.datetime.get_today();

        buckets.forEach((bucket, bIdx) => {
            const color = this._bucket_color(bIdx);

            const section = $(`
				<div class="freq-bucket-section">
					<div class="freq-bucket-bar">
						<div class="freq-bucket-bar-left">
							<span class="freq-bucket-chevron">▶</span>
							<span class="freq-bucket-label">${bucket.label}</span>
							<span class="freq-bucket-count" style="background:${color};">${bucket.count} item${bucket.count !== 1 ? 's' : ''}</span>
						</div>
					</div>
					<div class="freq-bucket-body"></div>
				</div>
			`);

            const body = section.find('.freq-bucket-body');

            bucket.customers.forEach(customer => {
                const custCard = $(`
					<div class="freq-customer-card">
						<div class="freq-customer-header">
							<div>
								<strong class="freq-customer-link"
										data-name="${customer.customer_code}">
									${customer.customer_name}
								</strong>
								<span style="font-size:11px;color:#94a3b8;margin-left:6px;">(${customer.items.length})</span>
							</div>
							<span class="freq-cust-chevron">▶</span>
						</div>
						<div class="freq-customer-items"></div>
					</div>
				`);

                const itemsContainer = custCard.find('.freq-customer-items');

                customer.items.forEach(item => {
                    // Next order date styling
                    let dateClass = 'freq-next-date-upcoming';
                    let dateLabel = '';
                    if (item.next_order_date) {
                        dateLabel = frappe.datetime.str_to_user(item.next_order_date);
                        if (item.next_order_date < today) {
                            dateClass = 'freq-next-date-overdue';
                        } else if (item.next_order_date === today) {
                            dateClass = 'freq-next-date-today';
                        }
                    } else {
                        dateLabel = 'N/A';
                    }

                    const row = $(`
						<div class="freq-item-row">
							<div>
								<div class="freq-item-name">${item.item}</div>
								<div class="freq-item-meta">
									<span>Qty: ${item.quantity || 0}</span>
									<span>Every <b>${item.frequency_day}</b> days</span>
									<br>
									<span>Next Order: <span class="${dateClass}">${dateLabel}</span></span>
								</div>
							</div>
							<div>
								<span class="freq-day-badge">${item.frequency_day}d</span>
							</div>
						</div>
					`);

                    itemsContainer.append(row);
                });

                body.append(custCard);
            });

            container.append(section);
        });
    }
};
