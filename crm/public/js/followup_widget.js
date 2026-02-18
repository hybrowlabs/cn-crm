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
		// Toggle Customers (CLASS BASED — NO jQuery animation)
		//-----------------------------------------

		container.off('click', '.customer-header');

		container.on('click', '.customer-header', function () {

			const card = $(this).closest('.customer-card');
			const items = card.find('.customer-items');
			const icon = $(this).find('.chevron');

			const isOpen = items.hasClass('open');

			// Close ALL
			container.find('.customer-items').removeClass('open');
			container.find('.chevron').removeClass('rotate');

			// If it was closed → open it
			if (!isOpen) {
				items.addClass('open');
				icon.addClass('rotate');
			}
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

		customers.forEach(customer => {

			const card = $(`
                <div class="customer-card">

                    <div class="customer-header">
                        
                        <div>
                            <strong>${customer.customer_name}</strong>
                        </div>

                        <div style="display:flex;gap:8px;align-items:center;">
                            <span class="badge badge-secondary">
                                ${customer.items.length}
                            </span>

                            <span class="chevron">
                                ▶
                            </span>
                        </div>

                    </div>

                    <div class="customer-items"></div>

                </div>
            `);

			const itemsContainer = card.find('.customer-items');

			//-------------------------------------

			customer.items.forEach(item => {

				const row = $(`
                    <div class="item-row" data-id="${item.log_id}">
                        
                        <div>
                            <div class="item-title">
                                ${item.item}
                            </div>

                            <div class="item-meta">
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
