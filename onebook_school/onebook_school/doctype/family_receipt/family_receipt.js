frappe.ui.form.on("Family Receipt", {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Get Dues"), () => {
				if (!frm.doc.guardian || !frm.doc.company) {
					frappe.msgprint(__("Choose the parent and the school first."));
					return;
				}
				frm.call("allocate_from_client").then(() => frm.refresh_fields());
			});
		}
	},
	guardian(frm) {
		if (frm.doc.guardian && frm.doc.company && frm.doc.amount_paid) frm.call("allocate_from_client");
	},
	amount_paid(frm) {
		if (frm.doc.guardian && frm.doc.company) frm.call("allocate_from_client");
	},
});
