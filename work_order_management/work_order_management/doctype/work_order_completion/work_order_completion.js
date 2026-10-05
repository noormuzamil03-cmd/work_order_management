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

/* ---------- Urdu / English typing and right-to-left display ---------- */
(function () {
	const MAP = {
		a: "ا", b: "ب", c: "چ", d: "د", e: "ع", f: "ف", g: "گ", h: "ھ", i: "ی", j: "ج",
		k: "ک", l: "ل", m: "م", n: "ن", o: "ہ", p: "پ", q: "ق", r: "ر", s: "س", t: "ت",
		u: "ء", v: "ط", w: "و", x: "ش", y: "ے", z: "ز",
		A: "آ", B: "ب", C: "ث", D: "ڈ", E: "ع", F: "ف", G: "غ", H: "ح", I: "ی", J: "ض",
		K: "خ", L: "ل", M: "م", N: "ں", O: "ۃ", P: "پ", Q: "ق", R: "ڑ", S: "ص", T: "ٹ",
		U: "ئ", V: "ظ", W: "و", X: "ژ", Y: "ۓ", Z: "ذ",
		",": "،", "?": "؟", ";": "؛", ".": "۔",
	};
	const KEY = "wom_urdu_typing";
	const TYPE_FIELDS = ["details_of_defects", "remarks", "approver_remarks"];
	const VIEW_FIELDS = ["defect_description", "details_of_defects", "remarks", "approver_remarks"];
	const is_on = () => localStorage.getItem(KEY) !== "0";

	function add_style() {
		if (document.getElementById("wom-woc-urdu-style-v3")) return;
		const selectors = VIEW_FIELDS.map((f) =>
			`[data-fieldname="${f}"] textarea, [data-fieldname="${f}"] .control-value, [data-fieldname="${f}"] .like-disabled-input`
		).join(", ");
		const style = document.createElement("style");
		style.id = "wom-woc-urdu-style-v3";
		style.textContent = `
			${selectors} {
				unicode-bidi: plaintext;
				text-align: start;
				font-family: "Noto Nastaliq Urdu", "Jameel Noori Nastaleeq", "Urdu Typesetting", "Noto Naskh Arabic", sans-serif;
				font-size: 16px;
				line-height: 2;
			}
			.wom-lang-switch {
				display: inline-flex; margin-left: 8px; vertical-align: middle; user-select: none;
				border: 1px solid var(--border-color); border-radius: 10px; overflow: hidden;
			}
			.wom-lang-switch [data-lang] { font-size: 11px; padding: 1px 10px; cursor: pointer; }
			.wom-lang-switch [data-lang].active { background: var(--primary); color: #fff; }
		`;
		document.head.appendChild(style);
	}

	function update_switches() {
		const on = is_on();
		$(".wom-lang-switch").each(function () {
			$(this).find('[data-lang="ur"]').toggleClass("active", on);
			$(this).find('[data-lang="en"]').toggleClass("active", !on);
		});
	}

	function setup_field(frm, fieldname) {
		const field = frm.fields_dict[fieldname];
		if (!field) return;

		if (frm.doc.docstatus !== 0) {
			field.$wrapper.find(".wom-lang-switch").remove();
			return;
		}
		if (!field.$input) return;
		const $input = field.$input;

		if (!field.$wrapper.find(".wom-lang-switch").length) {
			const $switch = $(
				'<span class="wom-lang-switch">' +
					'<span data-lang="ur" title="' + __("Type in Urdu") + '">اردو</span>' +
					'<span data-lang="en" title="' + __("Type in English") + '">English</span>' +
				"</span>"
			).appendTo(field.$wrapper.find(".control-label").first());

			$switch.on("click", "[data-lang]", function (e) {
				e.preventDefault();
				e.stopPropagation();
				localStorage.setItem(KEY, $(this).attr("data-lang") === "ur" ? "1" : "0");
				update_switches();
				$input.trigger("focus");
			});
		}
		update_switches();

		if ($input.data("wom-urdu")) return;
		$input.data("wom-urdu", true);

		$input.on("keydown", (e) => {
			if (!is_on() || e.ctrlKey || e.metaKey || e.altKey) return;
			const ch = MAP[e.key];
			if (!ch) return;
			e.preventDefault();
			if (!document.execCommand("insertText", false, ch)) {
				const el = $input[0];
				const start = el.selectionStart;
				const end = el.selectionEnd;
				el.value = el.value.slice(0, start) + ch + el.value.slice(end);
				el.selectionStart = el.selectionEnd = start + ch.length;
				$input.trigger("input");
			}
		});
	}

	frappe.ui.form.on("Work Order Completion", {
		refresh(frm) {
			add_style();
			TYPE_FIELDS.forEach((f) => setup_field(frm, f));
		},
	});
})();