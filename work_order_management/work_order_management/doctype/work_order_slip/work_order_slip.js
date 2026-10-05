const WOS_COLORS = {
	"Not Started": "gray",
	"In Progress": "blue",
	"Pending Approval": "orange",
	"Rework Required": "red",
	"Completed": "green",
};

/* ---------- Urdu / English typing for Defect Description ---------- */

const URDU_MAP = {
	a: "ا", b: "ب", c: "چ", d: "د", e: "ع", f: "ف", g: "گ", h: "ھ", i: "ی", j: "ج",
	k: "ک", l: "ل", m: "م", n: "ن", o: "ہ", p: "پ", q: "ق", r: "ر", s: "س", t: "ت",
	u: "ء", v: "ط", w: "و", x: "ش", y: "ے", z: "ز",
	A: "آ", B: "ب", C: "ث", D: "ڈ", E: "ع", F: "ف", G: "غ", H: "ح", I: "ی", J: "ض",
	K: "خ", L: "ل", M: "م", N: "ں", O: "ۃ", P: "پ", Q: "ق", R: "ڑ", S: "ص", T: "ٹ",
	U: "ئ", V: "ظ", W: "و", X: "ژ", Y: "ۓ", Z: "ذ",
	",": "،", "?": "؟", ";": "؛", ".": "۔",
};
const URDU_KEY = "wom_urdu_typing";

function wom_urdu_on() {
	return localStorage.getItem(URDU_KEY) !== "0";
}

function wom_add_urdu_style() {
	if (document.getElementById("wom-urdu-style-v2")) return;
	const style = document.createElement("style");
	style.id = "wom-urdu-style-v2";
	style.textContent = `
		[data-fieldname="defect_description"] textarea,
		[data-fieldname="defect_description"] .control-value,
		[data-fieldname="defect_description"] .like-disabled-input {
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

function wom_update_switches() {
	const on = wom_urdu_on();
	$(".wom-lang-switch").each(function () {
		$(this).find('[data-lang="ur"]').toggleClass("active", on);
		$(this).find('[data-lang="en"]').toggleClass("active", !on);
	});
}

function wom_setup_urdu(frm) {
	wom_add_urdu_style();
	const field = frm.fields_dict.defect_description;
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
			localStorage.setItem(URDU_KEY, $(this).attr("data-lang") === "ur" ? "1" : "0");
			wom_update_switches();
			$input.trigger("focus");
		});
	}
	wom_update_switches();

	if ($input.data("wom-urdu")) return;
	$input.data("wom-urdu", true);

	$input.on("keydown", (e) => {
		if (!wom_urdu_on() || e.ctrlKey || e.metaKey || e.altKey) return;
		const ch = URDU_MAP[e.key];
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

/* ---------- Form ---------- */

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
		wom_setup_urdu(frm);

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