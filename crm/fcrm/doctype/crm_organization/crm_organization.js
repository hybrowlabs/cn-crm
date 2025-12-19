// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Organization", {
	refresh(frm) {
		// Add button to manually refresh dormancy status
		if (!frm.is_new()) {
			frm.add_custom_button(__('Refresh Dormancy Status'), function() {
				frappe.call({
					method: 'crm.fcrm.doctype.crm_organization.crm_organization.update_dormancy_status_for_organization',
					args: {
						organization_name: frm.doc.name
					},
					freeze: true,
					freeze_message: __('Updating dormancy status...'),
					callback: function(r) {
						if (r.message && r.message.success) {
							frappe.show_alert({
								message: __('Dormancy status updated successfully'),
								indicator: 'green'
							});
							frm.reload_doc();
						} else {
							frappe.show_alert({
								message: __('Failed to update dormancy status'),
								indicator: 'red'
							});
						}
					}
				});
			});
		}
	},
});
