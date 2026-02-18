frappe.provide('crm.followup_widget');

crm.followup_widget = {

	render(wrapper) {

		const container = $(wrapper);
		container.empty();

		// Inject HTML
		container.html(`
            <div class="followup-widget">
                
                <div class="followup-header">
                    <div style="font-weight:600;font-size:16px;">
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

		// Refresh button
		container.off('click', '.refresh-btn');
		container.on('click', '.refresh-btn', () => {
			this.load_data(container);
		});

		this.load_data(container);
	},

	//-------------------------------------

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

					this.render_customers(list, r.message.customers);

					empty.hide();
					list.show();

				} else {

					list.hide();
					empty.show();
				}
			}
		});
	},

	//-------------------------------------

	render_customers(container, customers) {

		container.empty();

		//-------------------------------------
		// ✅ EVENT DELEGATION (FIXES CLICK)
		//-------------------------------------

		container.off('click', '.customer-header');

		container.on('click', '.customer-header', function () {

			const items = $(this).next('.customer-items');

			items.stop(true, true).slideToggle(150);
		});

		//-------------------------------------

		customers.forEach(customer => {

			const card = $(`
                <div class="customer-card">

                    <div class="customer-header">
                        <div>
                            <strong>${customer.customer_name}</strong>
                        </div>

                        <div>
                            ${customer.items.length}
                        </div>
                    </div>

                    <div class="customer-items" style="display:none;"></div>

                </div>
            `);

			const itemsContainer = card.find('.customer-items');

			//-------------------------------------

			customer.items.forEach(item => {

				const row = $(`
                    <div class="item-row" data-id="${item.log_id}">
                        
                        <div>
                            <div style="font-weight:500;">
                                ${item.item}
                            </div>

                            <div style="font-size:12px;color:#777;">
                                Qty: ${item.qty}
                                • Next: ${frappe.datetime.str_to_user(item.next_order_date)}
                            </div>
                        </div>

                        <button class="btn btn-xs btn-success follow-btn">
                            Done
                        </button>

                    </div>
                `);

				//-------------------------------------
				// FOLLOW BUTTON
				//-------------------------------------

				row.find('.follow-btn').on('click', (e) => {

					e.stopPropagation();

					this.mark_followup(
						item.log_id,
						row,
						container.closest('.followup-widget')
					);
				});

				itemsContainer.append(row);
			});

			container.append(card);
		});
	},

	//-------------------------------------

	mark_followup(log_id, row, widget) {

		const btn = row.find('.follow-btn');

		btn.prop('disabled', true).text('...');

		frappe.call({
			method: 'crm.fcrm.doctype.frequency_log_list.frequency_log_list.mark_followup_done',
			args: { log_id },

			callback: (r) => {

				if (!r.message?.success) return;

				row.slideUp(200, function () {

					const card = row.closest('.customer-card');

					row.remove();

					const remaining = card.find('.item-row').length;

					if (!remaining) {

						card.slideUp(200, () => {

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
