// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.listview_settings['Frequency Log List'] = {
    onload: function (listview) {
        // Add "Generate Logs" button to the list view
        listview.page.add_inner_button(__('Generate Logs'), function () {
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
                                listview.refresh();
                            }
                        }
                    });
                }
            );
        });
    }
};
