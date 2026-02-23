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

				/* ---- Bucket Section ---- */
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
					background: #eef2ff;
					border-bottom: 1px solid #e2e8f0;
				}
				.freq-bucket-bar:hover {
					background: #e0e7ff;
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

				/* ---- Customer Row (flat list, no second accordion) ---- */
				.freq-cust-row {
					display: flex;
					align-items: flex-start;
					padding: 10px 16px;
					border-bottom: 1px solid #f1f5f9;
					background: #fff;
					transition: background 0.15s ease;
				}
				.freq-cust-row:last-child {
					border-bottom: none;
				}
				.freq-cust-row:hover {
					background: #f8fafc;
				}
				.freq-cust-name {
					font-size: 13px;
					font-weight: 600;
					color: #1e293b;
					cursor: pointer;
					transition: color 0.15s;
					white-space: nowrap;
					min-width: 140px;
					flex-shrink: 0;
				}
				.freq-cust-name:hover {
					color: #3b82f6;
				}
				.freq-cust-items-list {
					flex: 1;
					margin-left: 16px;
				}
				.freq-item-pill {
					display: inline-flex;
					align-items: center;
					gap: 6px;
					background: #f1f5f9;
					border: 1px solid #e2e8f0;
					border-radius: 6px;
					padding: 4px 10px;
					margin: 2px 4px 2px 0;
					font-size: 12px;
					color: #334155;
					transition: border-color 0.15s;
				}
				.freq-item-pill:hover {
					border-color: #94a3b8;
				}
				.freq-pill-item-name {
					font-weight: 600;
					color: #1e293b;
				}
				.freq-pill-sep {
					color: #cbd5e1;
				}
				.freq-pill-detail {
					color: #64748b;
					font-size: 11px;
				}
				.freq-pill-freq {
					background: #dbeafe;
					color: #1d4ed8;
					font-weight: 700;
					font-size: 10px;
					padding: 1px 6px;
					border-radius: 8px;
				}
				.freq-pill-date {
					font-size: 11px;
					font-weight: 500;
				}
				.freq-pill-date.overdue {
					color: #dc2626;
				}
				.freq-pill-date.due-today {
					color: #d97706;
				}
				.freq-pill-date.upcoming {
					color: #16a34a;
				}
				.freq-pill-date.no-date {
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

        // Open customer doc
        container.off('click', '.freq-cust-name');
        container.on('click', '.freq-cust-name', function (e) {
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

    // -------------------------------------------

    _bucket_colors: [
        { bg: '#10b981', bar: '#ecfdf5' },  // green
        { bg: '#3b82f6', bar: '#eff6ff' },  // blue
        { bg: '#8b5cf6', bar: '#f5f3ff' },  // violet
        { bg: '#f59e0b', bar: '#fffbeb' },  // amber
        { bg: '#ef4444', bar: '#fef2f2' },  // red
        { bg: '#6b7280', bar: '#f9fafb' },  // gray
    ],

    // -------------------------------------------

    render_buckets(container, buckets) {
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

                const row = $(`<div class="freq-cust-row"></div>`);

                // Customer name
                const nameEl = $(`
					<div class="freq-cust-name" data-name="${customer.customer_code}">
						${customer.customer_name}
					</div>
				`);

                // Items pills
                const pillsContainer = $(`<div class="freq-cust-items-list"></div>`);

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

                    const pill = $(`
						<span class="freq-item-pill">
							<span class="freq-pill-item-name">${item.item}</span>
							<span class="freq-pill-sep">|</span>
							<span class="freq-pill-freq">${item.frequency_day}d</span>
							<span class="freq-pill-sep">|</span>
							<span class="freq-pill-detail">Qty ${item.quantity || 0}</span>
							<span class="freq-pill-sep">|</span>
							<span class="freq-pill-date ${dateClass}">${dateLabel}</span>
						</span>
					`);

                    pillsContainer.append(pill);
                });

                row.append(nameEl);
                row.append(pillsContainer);
                body.append(row);
            });

            container.append(section);
        });
    }
};
