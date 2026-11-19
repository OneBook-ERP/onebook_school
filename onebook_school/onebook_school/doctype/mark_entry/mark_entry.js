frappe.ui.form.on("Mark Entry", {
	student_group(frm) {
		if (frm.doc.student_group) frm.call("get_students").then(() => frm.refresh_field("rows"));
	},
	refresh(frm) {
		if (frm.doc.docstatus === 0 && frm.doc.student_group) {
			frm.add_custom_button(__("Load Students"), () => frm.call("get_students").then(() => frm.refresh_field("rows")));
		}
	},
});
