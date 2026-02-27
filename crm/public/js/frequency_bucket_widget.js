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
					max-height: 350px;
					overflow-y: auto;
				}
				.freq-content::-webkit-scrollbar {
					width: 6px;
				}
				.freq-content::-webkit-scrollbar-thumb {
					background-color: #cbd5e1;
					border-radius: 10px;
				}
				.freq-empty {
					text-align: center;
					padding: 32px 16px;
					color: #94a3b8;
					font-size: 14px;
				}

				/* Bucket Summary Item */
				.freq-summary-item {
					display: flex;
					justify-content: space-between;
					align-items: center;
					padding: 11px 16px;
					cursor: pointer;
					transition: background 0.15s ease;
					border: 1px solid #e2e8f0;
					border-radius: 6px;
					margin-bottom: 8px;
				}
				.freq-summary-item:hover {
					opacity: 0.8;
				}
				.freq-summary-label {
					font-size: 14px;
					font-weight: 600;
					color: #1e293b;
					display: flex;
					align-items: center;
					gap: 10px;
				}
				.freq-summary-count {
					font-size: 11px;
					font-weight: 700;
					padding: 2px 8px;
					border-radius: 10px;
					color: #fff;
					min-width: 24px;
					text-align: center;
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

		// Refresh
		container.off('click', '.freq-refresh-btn');
		container.on('click', '.freq-refresh-btn', () => {
			this.load_data(container);
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

		// 1) Pie chart container
		const chartWrapper = $('<div class="freq-pie-chart" style="margin: 20px auto; max-width: 100%; padding: 10px;"></div>');
		container.append(chartWrapper);

		// 2) Summary list
		const listWrapper = $('<div class="freq-summary-list" style="padding: 0 16px 16px 16px;"></div>');

		buckets.forEach((bucket, bIdx) => {
			const palette = this._bucket_colors[bIdx % this._bucket_colors.length];

			const itemHtml = $(`
                <div class="freq-summary-item" style="background:${palette.bar};">
                    <span class="freq-summary-label">
                        <div style="width:12px; height:12px; border-radius:50%; background:${palette.bg}"></div>
                        ${bucket.label}
                    </span>
                    <span class="freq-summary-count" style="background:${palette.bg};">
                        ${bucket.count}
                    </span>
                </div>
            `);

			itemHtml.on('click', () => {
				this.open_bucket_drawer(bucket);
			});

			listWrapper.append(itemHtml);
		});

		container.append(listWrapper);

		// Render standard Frappe pie chart
		setTimeout(() => {
			if (typeof frappe !== 'undefined' && typeof frappe.Chart !== 'undefined') {
				try {
					let hasData = buckets.some(b => b.count > 0);
					if (!hasData) {
						chartWrapper.html('<div style="text-align:center;color:#94a3b8;padding:20px;">No Data</div>');
						return;
					}

					const chart = new frappe.Chart(chartWrapper[0], {
						data: {
							labels: buckets.map(b => b.label),
							datasets: [{ values: buckets.map(b => b.count) }]
						},
						title: "Breakdown by Days",
						type: 'pie',
						height: 350,
						colors: this._bucket_colors.map(c => c.bg),
						isNavigable: 1
					});

					// Add click event for slices
					chartWrapper[0].addEventListener('data-select', (e) => {
						let selected_bucket = null;

						if (e && e.detail) {
							if (e.detail.label) {
								selected_bucket = buckets.find(b => b.label === e.detail.label);
							} else if (e.detail.index !== undefined) {
								selected_bucket = buckets[e.detail.index];
							}
						} else if (e && typeof e.detail === 'number') {
							selected_bucket = buckets[e.detail];
						}

						if (selected_bucket) {
							this.open_bucket_drawer(selected_bucket);
						}
					});

					// Fallback DOM click event for slices
					setTimeout(() => {
						const paths = chartWrapper[0].querySelectorAll('.pie-path');
						paths.forEach((path, idx) => {
							path.style.cursor = 'pointer';
							path.addEventListener('click', (e) => {
								e.stopPropagation();

								// We can also identify the bucket by the path's color
								const pathColor = path.getAttribute('fill') || path.style.fill;

								let bucketIdx = this._bucket_colors.findIndex(c => {
									let tempDiv = document.createElement('div');
									tempDiv.style.color = c.bg;
									document.body.appendChild(tempDiv);
									let rgbColor = getComputedStyle(tempDiv).color;
									document.body.removeChild(tempDiv);

									return rgbColor === pathColor || c.bg.toLowerCase() === pathColor.toLowerCase() ||
										(pathColor.includes('16, 185, 129') && c.bg === '#10b981') ||
										(pathColor.includes('59, 130, 246') && c.bg === '#3b82f6') ||
										(pathColor.includes('245, 158, 11') && c.bg === '#f59e0b') ||
										(pathColor.includes('107, 114, 128') && c.bg === '#6b7280');
								});

								if (bucketIdx === -1) {
									// If color matching fails, map positionally
									bucketIdx = idx;
								}

								if (bucketIdx >= 0 && bucketIdx < buckets.length) {
									this.open_bucket_drawer(buckets[bucketIdx]);
								}
							});
						});
					}, 500);

				} catch (err) {
					console.error("Error drawing pie chart:", err);
				}
			} else {
				chartWrapper.hide();
			}
		}, 100);
	},

	open_bucket_drawer(bucket) {
		if (!bucket || !bucket.customers || bucket.customers.length === 0) {
			frappe.show_alert({ message: __('No data in ' + bucket.label), indicator: 'orange' });
			return;
		}

		const today = frappe.datetime.get_today();
		let html = `<div style="padding: 5px 0 20px 0;">`;

		bucket.customers.forEach(customer => {
			html += `
                <div style="margin-bottom: 20px; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden; background: #fff;">
                    <div style="background: #f8fafc; padding: 12px 16px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; font-size: 14px; color: #1e293b;">
                            <a href="/app/customer/${encodeURIComponent(customer.customer_code)}" style="color: inherit; text-decoration: none;" target="_blank">
                                ${customer.customer_name}
                            </a>
                        </span>
                        <span style="font-size: 12px; font-weight: 600; color: #64748b; background: #e2e8f0; padding: 2px 8px; border-radius: 10px;">
                            ${customer.items.length} item${customer.items.length !== 1 ? 's' : ''}
                        </span>
                    </div>
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; font-size: 13px; border-collapse: collapse; min-width: 500px;">
                            <thead>
                                <tr style="background: #fff; text-align: left; color: #64748b; font-size: 12px; text-transform: uppercase;">
                                    <th style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">Item Name</th>
                                    <th style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; width: 80px;">Qty</th>
                                    <th style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; width: 180px;">Rate</th>
                                    <th style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; width: 100px;">Freq Day</th>
                                    <th style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; width: 120px;">Next Order</th>
                                </tr>
                            </thead>
                            <tbody>
            `;

			customer.items.forEach(item => {
				let dateColor = '#16a34a'; // Default green (upcoming)
				let dateLabel = 'N/A';
				if (item.next_order_date) {
					dateLabel = frappe.datetime.str_to_user(item.next_order_date);
					if (item.next_order_date < today) {
						dateColor = '#dc2626'; // Overdue (red)
					} else if (item.next_order_date === today) {
						dateColor = '#d97706'; // Due today (orange)
					}
				} else {
					dateColor = '#94a3b8'; // No date (gray)
				}

				html += `
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 16px; color: #334155;">${item.item}</td>
                        <td style="padding: 10px 16px; color: #334155;">${item.quantity || 0}</td>
                        <td style="padding: 10px 16px; font-weight: 600; color: #1d4ed8;">${format_currency(item.rate || 0, customer.default_currency, 0).replace(/\.00$/, '')}</td>
                        <td style="padding: 10px 16px; font-weight: 600; color: #1d4ed8;">${item.frequency_day}</td>
                        <td style="padding: 10px 16px; color: ${dateColor}; font-weight: 600;">${dateLabel}</td>
                    </tr>
                `;
			});

			html += `</tbody></table></div></div>`;
		});

		html += `</div>`;

		let d = new frappe.ui.Dialog({
			title: __(`Frequency Data: ${bucket.label}`),
			size: 'extra-large',
			fields: [
				{
					fieldname: 'html_content',
					fieldtype: 'HTML',
					options: html
				}
			]
		});

		if (d.$body) {
			d.$body.css('background-color', '#f8fafc');
			d.$body.css('padding', '20px');
		}

		d.show();
	}
};
