// Work Permit list: the chosen permit colour as the indicator
frappe.listview_settings["Work Permit"] = {
	add_fields: ["permit_color", "work_status"],
	get_indicator(doc) {
		const map = { Red: "red", Green: "green", Yellow: "yellow", Blue: "blue" };
		if (doc.permit_color) return [__(doc.permit_color), map[doc.permit_color], "permit_color,=," + doc.permit_color];
	},
};
