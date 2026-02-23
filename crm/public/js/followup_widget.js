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
				.refresh-btn {
					background: rgba(255,255,255,0.15) !important;
					border: 1px solid rgba(255,255,255,0.2) !important;
					color: #fff !important;
					font-size: 12px;
					padding: 4px 12px;
					border-radius: 6px;
					transition: all 0.2s ease;
				}
				.refresh-btn:hover {
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
				}
				.customer-card {
					border-bottom: 1px solid #e2e8f0;
				}
				.customer-card:last-child {
					border-bottom: none;
				}
				.customer-header {
					display: flex;
					justify-content: space-between;
					align-items: center;
					padding: 10px 16px;
					cursor: pointer;
					transition: background 0.15s ease;
					background: #fff;
				}
				.customer-header:hover {
					background: #eef2f7;
				}
				.customer-link {
					font-size: 13px;
					font-weight: 600;
					color: #1e293b;
					cursor: pointer;
					transition: color 0.15s ease;
				}
				.customer-link:hover {
					color: #3b82f6;
				}
				.cust-right {
					display: flex;
					align-items: center;
					gap: 8px;
				}
				.cust-item-count {
					font-size: 11px;
					color: #64748b;
				}
				.chevron {
					font-size: 10px;
					color: #94a3b8;
					transition: transform 0.25s ease;
					display: inline-block;
				}
				.chevron.rotate {
					transform: rotate(90deg);
				}
				.customer-items {
					max-height: 0;
					overflow: hidden;
					transition: max-height 0.3s ease;
					background: #ffffff;
				}
				.customer-items.open {
					max-height: 3000px;
				}

				/* Table */
				.followup-table {
					width: 100%;
					border-collapse: collapse;
					font-size: 12px;
				}
				.followup-table thead th {
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
				.followup-table tbody td {
					padding: 8px 12px;
					color: #334155;
					border-bottom: 1px solid #f1f5f9;
					vertical-align: middle;
				}
				.followup-table tbody tr:last-child td {
					border-bottom: none;
				}
				.followup-table tbody tr:hover td {
					background: #f8fafc;
				}
				.followup-table .td-item {
					font-weight: 500;
				}
				.followup-table .td-date.overdue {
					color: #dc2626;
					font-weight: 600;
				}
				.followup-table .td-date.due-today {
					color: #d97706;
					font-weight: 600;
				}
				.followup-table .td-date.upcoming {
					color: #16a34a;
				}
				.urgency-badge {
					font-size: 10px;
					font-weight: 600;
					padding: 2px 8px;
					border-radius: 10px;
					text-transform: uppercase;
					letter-spacing: 0.5px;
					white-space: nowrap;
				}
				.urgency-overdue { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
				.urgency-today { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
				.urgency-inactive { background: #f0f9ff; color: #0284c7; border: 1px solid #bae6fd; }
				.urgency-escalated { background: #fdf4ff; color: #a855f7; border: 1px solid #e9d5ff; }
				.urgency-dormant { background: #f1f5f9; color: #64748b; border: 1px solid #cbd5e1; }
				.urgency-upcoming { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }

				/* Footer */
				.items-footer {
					display: flex;
					justify-content: space-between;
					align-items: center;
					padding: 10px 12px;
					border-top: 1px solid #e2e8f0;
					background: #f8fafc;
				}
				.items-footer .total-amount {
					font-size: 13px;
					font-weight: 600;
					color: #1e293b;
				}
				.items-footer .create-quotation-btn {
					font-size: 12px;
					padding: 5px 14px;
					border-radius: 6px;
					font-weight: 500;
					transition: all 0.2s ease;
				}
				.empty-state {
					text-align: center;
					padding: 32px 16px;
					color: #94a3b8;
					font-size: 14px;
				}
			</style>

			<div class="followup-widget">
				<div class="followup-header">
					<div class="followup-title">Follow-ups Needed</div>
					<button class="btn btn-sm refresh-btn">Refresh</button>
				</div>

				<div class="followup-loading">Loading...</div>

				<div class="followup-content" style="display:none;">
					<div class="customer-list"></div>
					<div class="empty-state" style="display:none;">No follow-ups 🎉</div>
				</div>
			</div>
		`);

		//-----------------------------------------
		// Refresh
		//-----------------------------------------

		container.off('click', '.refresh-btn');
		container.on('click', '.refresh-btn', () => {
			this.load_data(container);
		});

		//-----------------------------------------
		// Toggle Customers
		//-----------------------------------------

		container.off('click', '.customer-header');

		container.on('click', '.customer-header', function () {

			const card = $(this).closest('.customer-card');
			const items = card.find('.customer-items');
			const icon = $(this).find('.chevron');

			const isOpen = items.hasClass('open');

			// Close all
			container.find('.customer-items').removeClass('open');
			container.find('.chevron').removeClass('rotate');

			// Open if previously closed
			if (!isOpen) {
				items.addClass('open');
				icon.addClass('rotate');
			}
		});

		//-----------------------------------------
		// OPEN CUSTOMER DOC
		//-----------------------------------------

		container.off('click', '.customer-link');

		container.on('click', '.customer-link', function (e) {

			e.stopPropagation();

			const customerName = $(this).data('name');

			frappe.set_route(
				'Form',
				'Customer',
				customerName
			);
		});

		this.load_data(container);
	},

	//-----------------------------------------

	load_data(container) {

		const loading = container.find('.followup-loading');
		const content = container.find('.followup-content');
		const list = container.find('.customer-list');
		const empty = container.find('.empty-state');

		loading.show();
		content.hide();

		frappe.call({
			method: 'crm.fcrm.doctype.frequency_log_list.frequency_log_list.get_followup_logs_for_user',

			callback: (r) => {

				loading.hide();
				content.show();

				if (r.message?.customers?.length) {

					this.render_customers(
						list,
						r.message.customers,
						container
					);

					empty.hide();
					list.show();

				} else {

					list.hide();
					empty.show();
				}
			}
		});
	},

	//-----------------------------------------

	render_customers(container, customers, widget) {

		container.empty();

		const today = frappe.datetime.get_today();

		customers.forEach(customer => {

			const card = $(`
				<div class="customer-card">
					<div class="customer-header">
						<div>
							<strong class="customer-link"
									data-name="${customer.name}">
								${customer.customer_name}
							</strong>
						</div>
						<div class="cust-right">
							<span class="cust-item-count">${customer.items.length} item${customer.items.length !== 1 ? 's' : ''}</span>
							<span class="chevron">▶</span>
						</div>
					</div>
					<div class="customer-items"></div>
				</div>
			`);

			const itemsContainer = card.find('.customer-items');

			//-------------------------------------
			// BUILD TABLE
			//-------------------------------------

			let tableHTML = `
				<table class="followup-table">
					<thead>
						<tr>
							<th>Item Name</th>
							<th>Qty</th>
							<th>Rate</th>
							<th>Next Order Date</th>
							<th>Status</th>
						</tr>
					</thead>
					<tbody>
			`;

			customer.items.forEach(item => {

				//---------------------------------
				// URGENCY CALCULATION
				//---------------------------------

				let urgencyClass = "urgency-upcoming";
				let urgencyLabel = "Upcoming";
				let dateClass = "upcoming";

				if (item.next_order_date < today) {
					const diffDays = frappe.datetime.get_diff(today, item.next_order_date);

					if (diffDays > 180) {
						urgencyClass = "urgency-dormant";
						urgencyLabel = "Dormant";
					} else if (diffDays > 90) {
						urgencyClass = "urgency-escalated";
						urgencyLabel = "Escalated";
					} else if (diffDays > 60) {
						urgencyClass = "urgency-inactive";
						urgencyLabel = "Inactive";
					} else {
						urgencyClass = "urgency-overdue";
						urgencyLabel = "Overdue";
					}
					dateClass = "overdue";
				}
				else if (item.next_order_date === today) {
					urgencyClass = "urgency-today";
					urgencyLabel = "Due Today";
					dateClass = "due-today";
				}

				const dateLabel = item.next_order_date
					? frappe.datetime.str_to_user(item.next_order_date)
					: 'N/A';

				tableHTML += `
					<tr>
						<td class="td-item">${item.item}</td>
						<td>${item.qty}</td>
						<td>${format_currency(item.rate)}</td>
						<td class="td-date ${dateClass}">${dateLabel}</td>
						<td><span class="urgency-badge ${urgencyClass}">${urgencyLabel}</span></td>
					</tr>
				`;
			});

			tableHTML += `</tbody></table>`;

			//-------------------------------------
			// FOOTER: Total Amount + Create Quotation
			//-------------------------------------

			const footerHTML = `
				<div class="items-footer">
					<span class="total-amount">
						Total: ${format_currency(customer.total_value || 0)}
					</span>
					<button class="btn btn-xs btn-primary create-quotation-btn">
						Create Quotation
					</button>
				</div>
			`;

			itemsContainer.html(tableHTML + footerHTML);

			//-------------------------------------
			// Create Quotation handler
			//-------------------------------------

			itemsContainer.find('.create-quotation-btn').on('click', (e) => {
				e.stopPropagation();
				const btn = itemsContainer.find('.create-quotation-btn');
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

			container.append(card);
		});
	}

};
