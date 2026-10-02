frappe.query_reports["Daily Work Orders Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Open", "Not Started", "In Progress", "Pending Approval", "Rework Required", "Completed"].join("\n"),
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "status" && data && data.status) {
			const colors = {
				"Not Started": "gray",
				"In Progress": "blue",
				"Pending Approval": "orange",
				"Rework Required": "red",
				"Completed": "green",
			};
			value = `<span class="indicator-pill ${colors[data.status] || "gray"}">${value}</span>`;
		}
		if (column.fieldname === "downtime" && data && String(data.downtime || "").includes("(open)")) {
			value = `<span style="color: var(--red-500);">${value}</span>`;
		}
		return value;
	},
};