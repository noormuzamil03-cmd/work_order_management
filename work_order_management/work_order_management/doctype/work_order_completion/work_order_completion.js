const WOC_HELP = {
	"Draft": ["Fill in the repair details, then use Actions → Send for Approval.", "blue"],
	"Rework Required": ["Sent back for rework. Read the Approver Remarks, correct the report, then Send for Approval again.", "red"],
	"Pending Approval": ["Waiting for approval. Approver: set Complaint Type and Work Status, save, then Approve or Send Back for Rework.", "orange"],
	"Approved": ["This report is approved and locked.", "green"],
};

frappe.ui.form.on("Work Order Completion", {
	setup(frm) {
		frm.set_query("work_order_slip", () => ({
			filters: { docstatus: 1, work_order_completion: ["is", "not set"] },
		}));
		const users = () => ({ filters: { enabled: 1, user_type: "System User" } });
		frm.set_query("completed_by", users);
		frm.set_query("received_by", users);
	},

	refresh(frm) {
		if (frm.doc.work_order_slip) {
			frm.add_custom_button(__("Back to Slip"), () => {
				frappe.set_route("Form", "Work Order Slip", frm.doc.work_order_slip);
			});
		}

		const help = WOC_HELP[frm.doc.workflow_state || "Draft"];
		frm.set_intro(help ? __(help[0]) : "", help ? help[1] : "");

		if (frm.doc.downtime_hours) {
			frm.dashboard.add_indicator(__("Downtime: {0} hours", [frm.doc.downtime_hours]), "blue");
		}
	},

	work_status(frm) {
		if (frm.doc.work_status === "Completed") {
			if (!frm.doc.completion_date) frm.set_value("completion_date", frappe.datetime.get_today());
			if (!frm.doc.completion_time) frm.set_value("completion_time", frappe.datetime.now_time());
		}
		frm.trigger("calc_downtime");
	},

	completion_date(frm) { frm.trigger("calc_downtime"); },
	completion_time(frm) { frm.trigger("calc_downtime"); },

	calc_downtime(frm) {
		const d = frm.doc;
		if (!d.slip_date || !d.completion_date) {
			frm.set_value("downtime_hours", 0);
			return;
		}
		const start = moment(`${d.slip_date} ${d.slip_time || "00:00:00"}`);
		const end = moment(`${d.completion_date} ${d.completion_time || "00:00:00"}`);
		const hours = end.diff(start, "minutes") / 60;
		frm.set_value("downtime_hours", hours >= 0 ? Math.round(hours * 10) / 10 : 0);
	},
});