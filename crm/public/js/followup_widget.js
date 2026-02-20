frappe.provide('crm.followup_widget');

crm.followup_widget = {

	render(wrapper) {

		const container = $(wrapper);
		container.empty();

		container.html(`
            <div class="followup-widget">

                <div class="followup-header">
                    <div class="followup-title">
                        Follow-ups Needed
                    </div>

                    <button class="btn btn-sm btn-primary refresh-btn">
                        Refresh
                    </button>
                </div>

                <div class="followup-loading">
                    Loading...
                </div>

                <div class="followup-content" style="display:none;">
                    <div class="customer-list"></div>

                    <div class="empty-state" style="display:none;">
                        No follow-ups 🎉
                    </div>
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

                        <div style="display:flex;gap:8px;align-items:center;">
                            <span class="badge badge-secondary">
                                ${customer.items.length}
                            </span>
                            
                            ${customer.total_value > 0 ? `
                                <span class="badge badge-primary">
                                    ${frappe.format(customer.total_value, { fieldtype: 'Currency' })}
                                </span>
                            ` : ''}

                            <button class="btn btn-xs btn-primary create-quotation-btn" style="margin-left: 8px;">
                                Create Quotation
                            </button>

                            <span class="chevron" style="margin-left: 8px;">
                                ▶
                            </span>
                        </div>

                    </div>

                    <div class="customer-items"></div>

                </div>
            `);

			const itemsContainer = card.find('.customer-items');

			//-------------------------------------
			// CREATE QUOTATION LOGIC
			//-------------------------------------
			const createQuotBtn = card.find('.create-quotation-btn');
			createQuotBtn.on('click', (e) => {
				e.stopPropagation();
				createQuotBtn.prop('disabled', true).text('...');

				frappe.route_options = {
					quotation_to: "Customer",
					party_name: customer.customer_code,
					currency: customer.default_currency,
					custom_branch: customer.custom_branch,
					items: customer.items.map(i => ({
						item_code: i.item,
						qty: i.qty
					}))
				};

				frappe.model.with_doctype('Quotation', () => {
					const new_name = frappe.model.make_new_doc_and_get_name('Quotation');
					frappe.set_route('Form', 'Quotation', new_name);
				});

				setTimeout(() => {
					createQuotBtn.prop('disabled', false).text('Create Quotation');
				}, 1000);
			});

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
                    <div class="item-row ${urgencyClass}" data-id="${item.log_id}">
                        
                        <div>
                            <div class="item-title">
                                ${item.item}
                            </div>

                            <div class="item-meta">
                                Qty: ${item.qty} • Rate: ${frappe.format(item.rate, { fieldtype: 'Currency' })}
                                <br>
                                Next: ${frappe.datetime.str_to_user(item.next_order_date)}
                            </div>
                        </div>

                        <div class="item-right">

                            ${urgencyLabel ? `
                                <span class="urgency-badge ${urgencyClass}">
                                    ${urgencyLabel}
                                </span>
                            ` : ''}

                            <button class="btn btn-xs btn-success follow-btn">
                                Done
                            </button>

                        </div>

                    </div>
                `);

				//---------------------------------

				row.find('.follow-btn').on('click', (e) => {

					e.stopPropagation();

					this.mark_followup(
						item.log_id,
						row,
						widget
					);
				});

				itemsContainer.append(row);
			});

			container.append(card);
		});
	},

	//-----------------------------------------

	mark_followup(log_id, row, widget) {

		const btn = row.find('.follow-btn');

		btn.prop('disabled', true).text('...');

		frappe.call({
			method: 'crm.fcrm.doctype.frequency_log_list.frequency_log_list.mark_followup_done',
			args: { log_id },

			callback: (r) => {

				if (!r.message?.success) return;

				row.fadeOut(200, function () {

					const card = row.closest('.customer-card');
					row.remove();

					const remaining = card.find('.item-row').length;

					if (!remaining) {

						card.fadeOut(200, () => {

							card.remove();

							if (!widget.find('.customer-card').length) {

								widget.find('.customer-list').hide();
								widget.find('.empty-state').show();
							}
						});
					}
				});

				frappe.show_alert({
					message: "Follow-up marked",
					indicator: "green"
				});
			}
		});
	}

};
