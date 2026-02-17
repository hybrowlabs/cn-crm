// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Order Frequancy', {
    refresh: function (frm) {
        // Add "Refresh Frequency" button
        if (frm.doc.customer_id && !frm.is_new()) {
            frm.add_custom_button(__('Refresh Frequency'), function () {
                frappe.call({
                    method: 'crm.fcrm.doctype.customer_order_frequancy.customer_order_frequancy.calculate_frequency_for_customer',
                    args: {
                        customer_id: frm.doc.customer_id
                    },
                    freeze: true,
                    freeze_message: __('Calculating Order Frequency...'),
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.show_alert({
                                message: __('Frequency calculation completed'),
                                indicator: 'green'
                            }, 5);
                            frm.reload_doc();
                        }
                    }
                });
            });
        }
    }
});
