frappe.provide('crm.followup_widget');

crm.followup_widget = {

	render(wrapper) {

		const container = $(wrapper);
		container.empty();

		container.html(`
			<style>
				.followup-widget {
					font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
				}
				.followup-header {
					display: flex;
					justify-content: space-between;
					align-items: center;
					padding: 12px 16px;
					background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
					border-radius: 10px 10px 0 0;
					color: #fff;
				}
				.followup-title {
					font-size: 15px;
					font-weight: 600;
					letter-spacing: 0.3px;
				}
				.followup-refresh-btn {
					background: rgba(255,255,255,0.15) !important;
					border: 1px solid rgba(255,255,255,0.2) !important;
					color: #fff !important;
					font-size: 12px;
					padding: 4px 12px;
					border-radius: 6px;
					transition: all 0.2s ease;
				}
				.followup-refresh-btn:hover {
					background: rgba(255,255,255,0.25) !important;
				}
				.followup-loading {
					text-align: center;
					padding: 24px;
					color: #94a3b8;
					font-size: 13px;
				}
				.followup-content {
					background: #f8fafc;
					border-radius: 0 0 10px 10px;
					border: 1px solid #e2e8f0;
					border-top: none;
					max-height: 450px;
					overflow-y: auto;
				}
				.followup-content::-webkit-scrollbar {
					width: 6px;
				}
				.followup-content::-webkit-scrollbar-thumb {
					background-color: #cbd5e1;
					border-radius: 10px;
				}
				.followup-empty {
					text-align: center;
					padding: 32px 16px;
					color: #94a3b8;
					font-size: 14px;
				}

				/* Bucket Summary Item */
				.followup-summary-item {
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
				.followup-summary-item:hover {
					opacity: 0.8;
				}
				.followup-summary-label {
					font-size: 14px;
					font-weight: 600;
					color: #1e293b;
					display: flex;
					align-items: center;
					gap: 10px;
				}
				.followup-summary-count {
					font-size: 11px;
					font-weight: 700;
					padding: 2px 8px;
					border-radius: 10px;
					color: #fff;
					min-width: 24px;
					text-align: center;
				}
			</style>

			<div class="followup-widget">
				<div class="followup-header">
					<div class="followup-title">Follow-ups by Value</div>
					<button class="btn btn-sm followup-refresh-btn">Refresh</button>
				</div>

				<div class="followup-loading">Loading...</div>

				<div class="followup-content" style="display:none;">
					<div class="followup-bucket-list"></div>
					<div class="followup-empty" style="display:none;">No follow-ups 🎉</div>
				</div>
			</div>
		`);

		// Refresh
		container.off('click', '.followup-refresh-btn');
		container.on('click', '.followup-refresh-btn', () => {
			this.load_data(container);
		});

		this.load_data(container);
	},

	// -------------------------------------------

	load_data(container) {
		const loading = container.find('.followup-loading');
		const content = container.find('.followup-content');
		const list = container.find('.followup-bucket-list');
		const empty = container.find('.followup-empty');

		loading.show();
		content.hide();

		frappe.call({
			method: 'crm.fcrm.doctype.frequency_log_list.frequency_log_list.get_followup_logs_for_user',
			callback: (r) => {
				loading.hide();
				content.show();

				if (r.message && r.message.customers && r.message.customers.length) {
					// Build buckets
					const buckets = this.build_buckets(r.message.customers);

					this.render_buckets(list, buckets, container);
					empty.hide();
					list.show();
				} else {
					list.hide();
					empty.show();
				}
			}
		});
	},

	build_buckets(customers) {
		const bucket_defs = [
			{ label: "0-1lac", min: 0, max: 100000 },
			{ label: "1lac-5lac", min: 100000, max: 500000 },
			{ label: "5lac-20lac", min: 500000, max: 2000000 },
			{ label: "20lac-50lac", min: 2000000, max: 5000000 },
			{ label: "50+", min: 5000000, max: Infinity }
		];

		let buckets = bucket_defs.map(b => ({ ...b, count: 0, customers: [] }));

		customers.forEach(customer => {
			const val = customer.total_value || 0;
			let target = buckets[buckets.length - 1]; // default 50+
			for (let b of buckets) {
				if (val >= b.min && val < b.max) {
					target = b;
					break;
				}
			}
			target.customers.push(customer);
			target.count += 1;
		});

		return buckets;
	},

	// -------------------------------------------

	_bucket_colors: [
		{ bg: '#3b82f6', bar: '#eff6ff' },
		{ bg: '#10b981', bar: '#ecfdf5' },
		{ bg: '#f59e0b', bar: '#fffbeb' },
		{ bg: '#8b5cf6', bar: '#f3e8ff' },
		{ bg: '#ec4899', bar: '#fdf2f8' },
		{ bg: '#6b7280', bar: '#f9fafb' },
	],

	// -------------------------------------------

	render_buckets(container, buckets, widget) {
		container.empty();

		// 1) Pie chart container
		const chartWrapper = $('<div class="followup-pie-chart" style="margin: 20px auto; max-width: 100%; padding: 10px;"></div>');
		container.append(chartWrapper);

		// 2) Summary list
		const listWrapper = $('<div class="followup-summary-list" style="padding: 0 16px 16px 16px;"></div>');

		buckets.forEach((bucket, bIdx) => {
			const palette = this._bucket_colors[bIdx % this._bucket_colors.length];

			const itemHtml = $(`
                <div class="followup-summary-item" style="background:${palette.bar};">
                    <span class="followup-summary-label">
                        <div style="width:12px; height:12px; border-radius:50%; background:${palette.bg}"></div>
                        ${bucket.label}
                    </span>
                    <span class="followup-summary-count" style="background:${palette.bg};">
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
						title: "Follow-ups by Value",
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

								const pathColor = path.getAttribute('fill') || path.style.fill;

								let bucketIdx = this._bucket_colors.findIndex(c => {
									let tempDiv = document.createElement('div');
									tempDiv.style.color = c.bg;
									document.body.appendChild(tempDiv);
									let rgbColor = getComputedStyle(tempDiv).color;
									document.body.removeChild(tempDiv);

									return rgbColor === pathColor || c.bg.toLowerCase() === pathColor.toLowerCase() ||
										(pathColor.includes('59, 130, 246') && c.bg === '#3b82f6') ||
										(pathColor.includes('16, 185, 129') && c.bg === '#10b981') ||
										(pathColor.includes('245, 158, 11') && c.bg === '#f59e0b') ||
										(pathColor.includes('139, 92, 246') && c.bg === '#8b5cf6') ||
										(pathColor.includes('236, 72, 153') && c.bg === '#ec4899') ||
										(pathColor.includes('107, 114, 128') && c.bg === '#6b7280');
								});

								if (bucketIdx === -1) {
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
		let html = `<div style="padding: 5px 0 20px 0;" class="followup-drawer-content">`;

		bucket.customers.forEach((customer, idx) => {
			html += `
                <div style="margin-bottom: 20px; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden; background: #fff;">
                    <div style="background: #f8fafc; padding: 12px 16px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; font-size: 14px; color: #1e293b;">
                            <a href="/app/customer/${encodeURIComponent(customer.customer_code)}" style="color: inherit; text-decoration: none;" target="_blank">
                                ${customer.customer_name}
                            </a>
                        </span>
                        <div style="display: flex; gap: 10px; align-items: center;">
							<span style="font-size: 13px; font-weight: 600; color: #1e293b;">
								Total: ${format_currency(customer.total_value || 0, customer.default_currency, 0).replace(/\.00$/, '')}
							</span>
							<span style="font-size: 12px; font-weight: 600; color: #64748b; background: #e2e8f0; padding: 2px 8px; border-radius: 10px;">
								${customer.items.length} item${customer.items.length !== 1 ? 's' : ''}
							</span>
							<button class="btn btn-xs btn-primary create-quotation-btn" data-idx="${idx}" style="margin-left: 10px;">
								Create Quotation
							</button>
                        </div>
                    </div>
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; font-size: 13px; border-collapse: collapse; min-width: 500px;">
                            <thead>
                                <tr style="background: #fff; text-align: left; color: #64748b; font-size: 12px; text-transform: uppercase;">
                                    <th style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">Item Name</th>
                                    <th style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; width: 80px;">Qty</th>
                                    <th style="padding: 10px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; width: 180px;">Rate</th>
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
                        <td style="padding: 10px 16px; color: #334155;">${item.qty}</td>
                        <td style="padding: 10px 16px; font-weight: 600; color: #1d4ed8;">${format_currency(item.rate, customer.default_currency, 0).replace(/\.00$/, '')}</td>
                        <td style="padding: 10px 16px; color: ${dateColor}; font-weight: 600;">${dateLabel}</td>
                    </tr>
                `;
			});

			html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
		});

		html += `</div>`;

		let d = new frappe.ui.Dialog({
			title: __(`Follow-ups: ${bucket.label}`),
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

			// Attach quotation click handlers
			setTimeout(() => {
				d.$wrapper.find('.create-quotation-btn').on('click', function (e) {
					e.stopPropagation();
					const btn = $(this);
					const idx = btn.data('idx');
					const customer = bucket.customers[idx];

					btn.prop('disabled', true).text('...');

					frappe.route_options = {
						quotation_to: "Customer",
						party_name: customer.customer_code,
						currency: customer.default_currency,
						custom_branch: customer.custom_branch,
						custom_sale_by: frappe.session.user,
						items: customer.items.map(i => ({
							item_code: i.item,
							qty: i.qty
						}))
					};

					frappe.new_doc('Quotation', frappe.route_options);

					setTimeout(() => {
						btn.prop('disabled', false).text('Create Quotation');
					}, 1000);
				});
			}, 100);
		}

		d.show();
	}
};
