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
					max-height: 2000px;
				}
				.item-row {
					display: flex;
					justify-content: space-between;
					align-items: center;
					padding: 8px 16px 8px 28px;
					border-top: 1px solid #f1f5f9;
					transition: background 0.15s ease;
				}
				.item-row:hover {
					background: #f8fafc;
				}
				.item-title {
					font-size: 13px;
					font-weight: 500;
					color: #334155;
					margin-bottom: 2px;
				}
				.item-meta {
					font-size: 11px;
					color: #64748b;
					line-height: 1.5;
				}
				.item-meta span {
					display: inline-block;
					margin-right: 10px;
				}
				.item-right {
					flex-shrink: 0;
					margin-left: 12px;
				}
				.urgency-badge {
					font-size: 10px;
					font-weight: 600;
					padding: 2px 8px;
					border-radius: 10px;
					text-transform: uppercase;
					letter-spacing: 0.5px;
				}
				.urgency-overdue .urgency-badge,
				.urgency-overdue.urgency-badge {
					background: #fef2f2;
					color: #dc2626;
					border: 1px solid #fecaca;
				}
				.urgency-today .urgency-badge,
				.urgency-today.urgency-badge {
					background: #fffbeb;
					color: #d97706;
					border: 1px solid #fde68a;
				}
				.urgency-inactive .urgency-badge,
				.urgency-inactive.urgency-badge {
					background: #f0f9ff;
					color: #0284c7;
					border: 1px solid #bae6fd;
				}
				.urgency-escalated .urgency-badge,
				.urgency-escalated.urgency-badge {
					background: #fdf4ff;
					color: #a855f7;
					border: 1px solid #e9d5ff;
				}
				.urgency-dormant .urgency-badge,
				.urgency-dormant.urgency-badge {
					background: #f1f5f9;
					color: #64748b;
					border: 1px solid #cbd5e1;
				}
				.urgency-upcoming .urgency-badge,
				.urgency-upcoming.urgency-badge {
					background: #f0fdf4;
					color: #16a34a;
					border: 1px solid #bbf7d0;
				}
				.items-footer {
					display: flex;
					justify-content: space-between;
					align-items: center;
					padding: 10px 16px 10px 28px;
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
						<span class="chevron">▶</span>
					</div>
					<div class="customer-items"></div>
				</div>
			`);

			const itemsContainer = card.find('.customer-items');

			//-------------------------------------

			customer.items.forEach(item => {

				//---------------------------------
				// URGENCY CALCULATION
				//---------------------------------

				let urgencyClass = "urgency-upcoming";
				let urgencyLabel = "Upcoming";

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
				}
				else if (item.next_order_date === today) {
					urgencyClass = "urgency-today";
					urgencyLabel = "Due Today";
				}

				//---------------------------------

				const row = $(`
					<div class="item-row" data-id="${item.log_id}">
						<div>
							<div class="item-title">${item.item}</div>
							<div class="item-meta">
								<span>Qty: ${item.qty}</span>
								<span>Rate: ${format_currency(item.rate)}</span>
								<br>
								<span>Next Order Date: ${frappe.datetime.str_to_user(item.next_order_date)}</span>
							</div>
						</div>
						<div class="item-right">
							<span class="urgency-badge ${urgencyClass}">${urgencyLabel}</span>
						</div>
					</div>
				`);

				itemsContainer.append(row);
			});

			//-------------------------------------
			// FOOTER: Total Amount + Create Quotation
			//-------------------------------------

			const footer = $(`
				<div class="items-footer">
					<span class="total-amount">
						Total: ${format_currency(customer.total_value || 0)}
					</span>
					<button class="btn btn-xs btn-primary create-quotation-btn">
						Create Quotation
					</button>
				</div>
			`);

			footer.find('.create-quotation-btn').on('click', (e) => {
				e.stopPropagation();
				const btn = footer.find('.create-quotation-btn');
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

			itemsContainer.append(footer);

			container.append(card);
		});
	}

};
