frappe.query_reports["Employee Leave Encashment Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("Date From"),
			fieldtype: "Date",
			default: (() => {
				const t = frappe.datetime.str_to_obj(frappe.datetime.get_today());
				const y = t.getMonth() >= 6 ? t.getFullYear() : t.getFullYear() - 1;
				return `${y}-07-01`;
			})(),
		},
		{
			fieldname: "to_date",
			label: __("To"),
			fieldtype: "Date",
			default: (() => {
				const t = frappe.datetime.str_to_obj(frappe.datetime.get_today());
				const y = t.getMonth() >= 6 ? t.getFullYear() : t.getFullYear() - 1;
				return `${y + 1}-06-30`;
			})(),
		},
		{
			fieldname: "pay_mode",
			label: __("Pay Mode"),
			fieldtype: "Select",
			options: ["All", "Bank", "Cash", "Cheque"].join("\n"),
			default: "All",
		},
		{
			fieldname: "cadre",
			label: __("Cader ID"),
			fieldtype: "Link",
			options: "Employee Grade",
		},
		{
			fieldname: "summary",
			label: __("Summary"),
			fieldtype: "Select",
			options: ["None", "Department", "Designation", "Pay Mode"].join("\n"),
			default: "None",
		},
		{
			fieldname: "bank_sheet",
			label: __("Bank Sheet"),
			fieldtype: "Check",
		},
		{
			fieldname: "show_cadre",
			label: __("Cader"),
			fieldtype: "Check",
		},
	],

	onload: function (report) {
		const open_print = (as_pdf) => {
			frappe.ui.get_print_settings(
				as_pdf,
				(settings) => (as_pdf ? report.pdf_report(settings) : report.print_report(settings)),
				report.report_doc && report.report_doc.letter_head,
				report.get_visible_columns()
			);
		};
		report.page.add_inner_button(__("Print"), () => open_print(false));
		report.page.add_inner_button(__("PDF"), () => open_print(true));
	},

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.is_total) {
			value = `<b>${value}</b>`;
		}
		return value;
	},
};