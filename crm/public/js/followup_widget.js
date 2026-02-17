// Follow-up Needed Widget
// This file provides the widget for displaying frequency follow-up logs

frappe.provide('crm.followup_widget');

crm.followup_widget = {
    render: function (wrapper) {
        const container = $(wrapper);
        container.empty();

        // Add CSS
        this.add_styles(container);

        // Create main structure
        const html = `
			<div class="followup-widget">
				<div class="followup-header">
					<h3>Follow-up Needed</h3>
					<button class="btn btn-sm btn-primary refresh-btn">
						<i class="fa fa-refresh"></i> Refresh
					</button>
				</div>
				<div class="followup-loading">
					<i class="fa fa-spinner fa-spin"></i> Loading...
				</div>
				<div class="followup-content" style="display: none;">
					<div class="customer-list"></div>
					<div class="empty-state" style="display: none;">
						<p>No follow-ups needed at the moment.</p>
					</div>
				</div>
			</div>
		`;

        container.html(html);

        // Bind events
        container.find('.refresh-btn').on('click', () => {
            this.load_data(container);
        });

        // Load initial data
        this.load_data(container);
    },

    add_styles: function (container) {
        const style = `
			<style>
				.followup-widget {
					background: white;
					border-radius: 8px;
					padding: 20px;
					box-shadow: 0 2px 4px rgba(0,0,0,0.1);
				}
				
				.followup-header {
					display: flex;
					justify-content: space-between;
					align-items: center;
					margin-bottom: 20px;
					padding-bottom: 15px;
					border-bottom: 2px solid #f0f0f0;
				}
				
				.followup-header h3 {
					margin: 0;
					font-size: 18px;
					font-weight: 600;
					color: #333;
				}
				
				.followup-loading {
					text-align: center;
					padding: 40px;
					color: #888;
					font-size: 14px;
				}
				
				.customer-card {
					border: 1px solid #e0e0e0;
					border-radius: 6px;
					margin-bottom: 12px;
					overflow: hidden;
					transition: all 0.3s ease;
				}
				
				.customer-card:hover {
					box-shadow: 0 2px 8px rgba(0,0,0,0.1);
				}
				
				.customer-header {
					background: #f8f9fa;
					padding: 12px 15px;
					cursor: pointer;
					display: flex;
					justify-content: space-between;
					align-items: center;
					transition: background 0.2s ease;
				}
				
				.customer-header:hover {
					background: #e9ecef;
				}
				
				.customer-name {
					font-weight: 600;
					color: #333;
					font-size: 14px;
				}
				
				.item-count {
					background: #e74c3c;
					color: white;
					padding: 2px 8px;
					border-radius: 12px;
					font-size: 12px;
					font-weight: 600;
				}
				
				.customer-items {
					display: none;
					padding: 10px 15px;
					background: white;
				}
				
				.customer-items.expanded {
					display: block;
				}
				
				.item-row {
					display: flex;
					justify-content: space-between;
					align-items: center;
					padding: 10px;
					border-bottom: 1px solid #f0f0f0;
					transition: background 0.2s ease;
				}
				
				.item-row:last-child {
					border-bottom: none;
				}
				
				.item-row:hover {
					background: #f8f9fa;
				}
				
				.item-info {
					flex: 1;
				}
				
				.item-name {
					font-weight: 500;
					color: #333;
					font-size: 14px;
					margin-bottom: 4px;
				}
				
				.item-details {
					font-size: 12px;
					color: #666;
				}
				
				.followup-btn {
					background: #27ae60;
					color: white;
					border: none;
					padding: 6px 14px;
					border-radius: 4px;
					cursor: pointer;
					font-size: 12px;
					font-weight: 500;
					transition: background 0.2s ease;
				}
				
				.followup-btn:hover {
					background: #229954;
				}
				
				.followup-btn:disabled {
					background: #bdc3c7;
					cursor: not-allowed;
				}
				
				.empty-state {
					text-align: center;
					padding: 40px;
					color: #888;
					font-size: 14px;
				}
				
				.expand-icon {
					transition: transform 0.3s ease;
					color: #666;
					font-size: 12px;
					margin-left: 8px;
				}
				
				.expand-icon.expanded {
					transform: rotate(90deg);
				}
			</style>
		`;

        $('head').append(style);
    },

    load_data: function (container) {
        const loading = container.find('.followup-loading');
        const content = container.find('.followup-content');
        const customerList = container.find('.customer-list');
        const emptyState = container.find('.empty-state');

        loading.show();
        content.hide();

        frappe.call({
            method: 'crm.fcrm.doctype.frequency_log_list.frequency_log_list.get_followup_logs_for_user',
            callback: (r) => {
                loading.hide();
                content.show();

                if (r.message && r.message.customers && r.message.customers.length > 0) {
                    this.render_customers(customerList, r.message.customers);
                    emptyState.hide();
                    customerList.show();
                } else {
                    customerList.hide();
                    emptyState.show();
                }
            },
            error: () => {
                loading.hide();
                frappe.msgprint('Failed to load follow-up data');
            }
        });
    },

    render_customers: function (container, customers) {
        container.empty();

        customers.forEach(customer => {
            const card = $(`
				<div class="customer-card">
					<div class="customer-header" data-customer="${customer.customer_code}">
						<span class="customer-name">
							${customer.customer_name}
							<i class="fa fa-chevron-right expand-icon"></i>
						</span>
						<span class="item-count">${customer.items.length} item${customer.items.length > 1 ? 's' : ''}</span>
					</div>
					<div class="customer-items"></div>
				</div>
			`);

            const itemsContainer = card.find('.customer-items');

            customer.items.forEach(item => {
                const itemRow = $(`
					<div class="item-row" data-log-id="${item.log_id}">
						<div class="item-info">
							<div class="item-name">${item.item}</div>
							<div class="item-details">
								Qty: ${item.qty} | Next Order: ${frappe.datetime.str_to_user(item.next_order_date)}
							</div>
						</div>
						<button class="followup-btn">Mark as Followed Up</button>
					</div>
				`);

                // Bind follow-up button
                itemRow.find('.followup-btn').on('click', (e) => {
                    e.stopPropagation();
                    this.mark_followup(item.log_id, itemRow, container.closest('.followup-widget'));
                });

                itemsContainer.append(itemRow);
            });

            // Bind expand/collapse
            card.find('.customer-header').on('click', function () {
                const items = $(this).siblings('.customer-items');
                const icon = $(this).find('.expand-icon');

                items.toggleClass('expanded');
                icon.toggleClass('expanded');
            });

            container.append(card);
        });
    },

    mark_followup: function (log_id, row, widgetContainer) {
        const btn = row.find('.followup-btn');
        btn.prop('disabled', true).text('Processing...');

        frappe.call({
            method: 'crm.fcrm.doctype.frequency_log_list.frequency_log_list.mark_followup_done',
            args: { log_id: log_id },
            callback: (r) => {
                if (r.message && r.message.success) {
                    // Animate removal
                    row.fadeOut(300, function () {
                        const card = row.closest('.customer-card');
                        row.remove();

                        // Check if customer has any items left
                        const remainingItems = card.find('.item-row').length;
                        if (remainingItems === 0) {
                            card.fadeOut(300, function () {
                                card.remove();

                                // Check if any customers left
                                const remainingCustomers = widgetContainer.find('.customer-card').length;
                                if (remainingCustomers === 0) {
                                    widgetContainer.find('.customer-list').hide();
                                    widgetContainer.find('.empty-state').show();
                                }
                            });
                        } else {
                            // Update count
                            card.find('.item-count').text(`${remainingItems} item${remainingItems > 1 ? 's' : ''}`);
                        }
                    });

                    frappe.show_alert({
                        message: 'Marked as followed up',
                        indicator: 'green'
                    }, 3);
                }
            },
            error: () => {
                btn.prop('disabled', false).text('Mark as Followed Up');
                frappe.msgprint('Failed to mark as followed up');
            }
        });
    }
};
