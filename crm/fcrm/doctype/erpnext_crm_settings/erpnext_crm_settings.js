// Copyright (c) 2024, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('ERPNext CRM Settings', {
	sync_territories_button: function(frm) {
		if (!frm.doc.enabled) {
			frappe.msgprint(__('Please enable ERPNext CRM integration first'));
			return;
		}
		
		if (!frm.doc.enable_territory_sync) {
			frappe.msgprint(__('Please enable Territory Sync first'));
			return;
		}
		
		frappe.confirm(
			__('This will sync all territories between ERPNext and CRM. This may take some time. Continue?'),
			function() {
				frappe.call({
					method: 'sync_all_territories',
					doc: frm.doc,
					btn: $('.btn-sync-territories'),
					callback: function(r) {
						if (r.message && r.message.success) {
							frappe.msgprint({
								title: __('Success'),
								indicator: 'green',
								message: r.message.message
							});
						} else {
							frappe.msgprint({
								title: __('Error'),
								indicator: 'red',
								message: r.message ? r.message.message : __('An error occurred during synchronization')
							});
						}
					}
				});
			}
		);
	}
});