frappe.query_reports["UDISE Student Export"] = {
	filters: [
		{ fieldname: "company", label: __("School"), fieldtype: "Link", options: "Company",
		  default: frappe.defaults.get_user_default("company") },
		{ fieldname: "academic_year", label: __("Academic Year"), fieldtype: "Link", options: "Academic Year", reqd: 1,
		  default: frappe.defaults.get_user_default("academic_year") },
		{ fieldname: "program", label: __("Class"), fieldtype: "Link", options: "Program" },
		{ fieldname: "student_group", label: __("Section"), fieldtype: "Link", options: "Student Group",
		  get_query: () => ({ filters: { group_based_on: "Batch" } }) },
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "issues" && data && data.issues) return `<span style="color:var(--red-600)">${value}</span>`;
		if (column.fieldname === "issues" && data && !data.issues) return `<span style="color:var(--green-600)">${__("Ready")}</span>`;
		return value;
	},
};
