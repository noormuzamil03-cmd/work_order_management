const WOS_COLORS = {
	"Not Started": "gray",
	"In Progress": "blue",
	"Pending Approval": "orange",
	"Rework Required": "red",
	"Completed": "green",
};

frappe.ui.form.on("Work Order Slip", {
	setup(frm) {
		frm.set_query("requested_by", () => ({ filters: { enabled: 1, user_type: "System User" } }));
	},

	onload(frm) {
		if (frm.is_new() && !frm.doc.time) {
			frm.set_value("time", frappe.datetime.now_time());
		}
	},

	refresh(frm) {
		if (frm.doc.docstatus !== 1) return;

		if (frm.doc.work_order_completion) {
			frm.add_custom_button(__("View Work Report"), () => {
				frappe.set_route("Form", "Work Order Completion", frm.doc.work_order_completion);
			});
		} else {
			frm.add_custom_button(
				__("{0} - Work Report", [frm.doc.assigned_department]),
				() => frappe.new_doc("Work Order Completion", { work_order_slip: frm.doc.name }),
				__("Create")
			);
		}

		frm.dashboard.add_indicator(
			__("Work Status: {0}", [__(frm.doc.work_status)]),
			WOS_COLORS[frm.doc.work_status] || "blue"
		);
	},
});