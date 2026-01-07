// Copyright (c) 2026, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('CRM Credit Settings', {
	refresh: function(frm) {
		// Add custom button to create credit roles
		frm.add_custom_button(__('Create Credit Roles'), function() {
			frappe.call({
				method: "create_credit_roles",
				doc: frm.doc,
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.msgprint({
							title: __('Success'),
							message: r.message.message,
							indicator: 'green'
						});
						frm.reload_doc();
					} else {
						frappe.msgprint({
							title: __('Error'),
							message: r.message ? r.message.error : __('Unknown error occurred'),
							indicator: 'red'
						});
					}
				}
			});
		}, __('Setup'));

		// Show warning if credit management is enabled but roles don't exist
		if (frm.doc.enabled) {
			check_credit_roles(frm);
		}
	},

	enabled: function(frm) {
		if (frm.doc.enabled) {
			check_credit_roles(frm);
		}
	},

	default_credit_limit: function(frm) {
		validate_credit_limits(frm);
	},

	max_credit_limit: function(frm) {
		validate_credit_limits(frm);
	},

	auto_approval_limit: function(frm) {
		validate_approval_limits(frm);
	},

	require_approval_above: function(frm) {
		validate_approval_limits(frm);
	}
});

function check_credit_roles(frm) {
	// Check if credit roles exist
	frappe.call({
		method: "frappe.client.get_value",
		args: {
			doctype: "Role",
			filters: {"name": ["in", ["Credit Manager", "Credit Analyst"]]},
			fieldname: ["name"]
		},
		callback: function(r) {
			if (r.message) {
				const existing_roles = r.message.map ? r.message.map(role => role.name) : [r.message.name];
				const missing_roles = [];

				if (!existing_roles.includes("Credit Manager")) {
					missing_roles.push("Credit Manager");
				}
				if (!existing_roles.includes("Credit Analyst")) {
					missing_roles.push("Credit Analyst");
				}

				if (missing_roles.length > 0) {
					frappe.msgprint({
						title: __('Missing Credit Roles'),
						message: __('The following credit roles do not exist: {0}. Click "Create Credit Roles" to create them.', [missing_roles.join(", ")]),
						indicator: 'orange'
					});
				}
			}
		}
	});
}

function validate_credit_limits(frm) {
	if (frm.doc.default_credit_limit && frm.doc.max_credit_limit) {
		if (frm.doc.default_credit_limit > frm.doc.max_credit_limit) {
			frappe.msgprint({
				title: __('Invalid Credit Limits'),
				message: __('Default Credit Limit cannot be greater than Maximum Credit Limit'),
				indicator: 'red'
			});
		}
	}
}

function validate_approval_limits(frm) {
	if (frm.doc.auto_approval_limit && frm.doc.require_approval_above) {
		if (frm.doc.auto_approval_limit >= frm.doc.require_approval_above) {
			frappe.msgprint({
				title: __('Invalid Approval Limits'),
				message: __('Auto Approval Limit must be less than Require Approval Above limit'),
				indicator: 'red'
			});
		}
	}
}