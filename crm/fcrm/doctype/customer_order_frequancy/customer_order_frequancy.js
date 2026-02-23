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

            // Add "Generate Tasks" button
            frm.add_custom_button(__('Generate Tasks'), function () {
                frappe.call({
                    method: 'crm.fcrm.doctype.frequency_log_list.frequency_log_list.generate_crm_tasks_for_customer',
                    args: {
                        customer_id: frm.doc.customer_id
                    },
                    freeze: true,
                    freeze_message: __('Generating CRM Tasks for expiring items...'),
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.show_alert({
                                message: __('Task generation completed'),
                                indicator: 'green'
                            }, 5);
                        }
                    }
                });
            });
        }

        // Add "Generate Logs" button
        frm.add_custom_button(__('Generate Logs'), function () {
            frappe.confirm(
                'This will regenerate all frequency logs. Continue?',
                function () {
                    frappe.call({
                        method: 'crm.fcrm.doctype.frequency_log_list.frequency_log_list.generate_logs_for_all',
                        freeze: true,
                        freeze_message: __('Generating Frequency Logs...'),
                        callback: function (r) {
                            if (!r.exc) {
                                frappe.show_alert({
                                    message: __('Logs generated successfully'),
                                    indicator: 'green'
                                }, 5);
                            }
                        }
                    });
                }
            );
        });
    }
});
