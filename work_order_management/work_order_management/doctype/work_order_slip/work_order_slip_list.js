frappe.listview_settings["Work Order Slip"] = {
	add_fields: ["work_status"],
	get_indicator(doc) {
		if (doc.docstatus === 0) return [__("Draft"), "red", "docstatus,=,0"];
		if (doc.docstatus === 2) return [__("Cancelled"), "red", "docstatus,=,2"];
		const colors = {
			"Not Started": "gray",
			"In Progress": "blue",
			"Pending Approval": "orange",
			"Rework Required": "red",
			"Completed": "green",
		};
		return [__(doc.work_status), colors[doc.work_status] || "blue", "work_status,=," + doc.work_status];
	},
};