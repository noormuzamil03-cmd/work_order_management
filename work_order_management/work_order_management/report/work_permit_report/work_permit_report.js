const WP_COLORS = { Red: "#d64545", Green: "#2e9b4f", Yellow: "#e0a800", Blue: "#2f6fd6" };

frappe.query_reports["Work Permit Report"] = {
	filters: [
		{ fieldname: "from_date", label: "From Date", fieldtype: "Date", default: frappe.datetime.add_months(frappe.datetime.get_today(), -1), reqd: 1 },
		{ fieldname: "to_date", label: "To Date", fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1 },
		{ fieldname: "permit_color", label: "Colour", fieldtype: "Select", options: "\nRed\nGreen\nYellow\nBlue" },
		{ fieldname: "work_status", label: "Status", fieldtype: "Select", options: "\nOpen\nWork complete\nWork incomplete" },
		{ fieldname: "department", label: "Department", fieldtype: "Link", options: "Department" },
		{ fieldname: "receiver_department", label: "Receiver Department", fieldtype: "Link", options: "Department" },
		{ fieldname: "permit_issued_to", label: "Issued To", fieldtype: "Link", options: "Employee" },
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;
		if (column.fieldname === "permit_color" && data.permit_color) {
			const c = WP_COLORS[data.permit_color] || "#888";
			value = `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${c};margin-right:6px"></span>${value}`;
		}
		if (column.fieldname === "status" && data.status) {
			const color = data.status === "Work complete" ? "green" : data.status === "Work incomplete" ? "orange" : "gray";
			value = `<span class="indicator-pill ${color}">${value}</span>`;
		}
		return value;
	},
	onload(report) {
		report.page.add_inner_button(__("Print"), () => wp_report_print(report)).addClass("btn-primary");
	},
};

function wp_report_print(report) {
	const rows = (report.data || []).filter((r) => r && r.name);
	if (!rows.length) {
		frappe.msgprint(__("Print ke liye koi record nahi hai."));
		return;
	}
	const f = report.get_filter_values() || {};
	const e = (v) => frappe.utils.escape_html(v == null ? "" : String(v));
	const logo = frappe.urllib.get_base_url() + "/files/atslogo.png";

	let filt = "From <b>" + e(frappe.datetime.str_to_user(f.from_date)) + "</b> to <b>" + e(frappe.datetime.str_to_user(f.to_date)) + "</b>";
	if (f.permit_color) filt += " &nbsp;|&nbsp; Colour: <b>" + e(f.permit_color) + "</b>";
	if (f.work_status) filt += " &nbsp;|&nbsp; Status: <b>" + e(f.work_status) + "</b>";
	if (f.department) filt += " &nbsp;|&nbsp; Department: <b>" + e(f.department) + "</b>";
	if (f.receiver_department) filt += " &nbsp;|&nbsp; Receiver: <b>" + e(f.receiver_department) + "</b>";
	if (f.permit_issued_to) filt += " &nbsp;|&nbsp; Issued To: <b>" + e(f.permit_issued_to) + "</b>";

	const summary = (report.raw_data && report.raw_data.report_summary) || [];
	const cards = summary.map((s) => `<div class="card"><span>${e(s.label)}</span><b>${e(s.value)}</b></div>`).join("");

	const body = rows.map((r, i) => {
		const c = WP_COLORS[r.permit_color] || "#888";
		const st = r.status === "Work complete" ? "ok" : r.status === "Work incomplete" ? "inc" : "";
		return `<tr>
			<td class="c">${i + 1}</td>
			<td>${e(r.name)}</td>
			<td class="c">${e(r.date ? frappe.datetime.str_to_user(r.date) : "")}</td>
			<td>${e(r.permit_no)}</td>
			<td>${r.permit_color ? `<span class="dot" style="background:${c}"></span>` + e(r.permit_color) : ""}</td>
			<td>${e(r.department)}</td>
			<td>${e(r.issued_to)}</td>
			<td>${e(r.receiver_department)}</td>
			<td>${e(r.validity)}</td>
			<td>${e(r.supervisor)}</td>
			<td class="${st}">${e(r.status)}</td>
		</tr>`;
	}).join("");

	const html = `<!doctype html><html><head><meta charset="utf-8"><title>Work Permit Report</title>
	<style>
		@page { size: A4 landscape; margin: 10mm; }
		* { box-sizing: border-box; }
		body { font-family: Arial, Helvetica, sans-serif; color: #111; font-size: 10.5px; margin: 0;
			-webkit-print-color-adjust: exact; print-color-adjust: exact; }
		.head { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #16233A; padding-bottom: 6px; margin-bottom: 8px; }
		.head img { height: 46px; }
		.title { text-align: right; }
		.title h2 { margin: 0; font-size: 18px; letter-spacing: 1px; color: #16233A; }
		.title div { font-size: 11px; margin-top: 3px; }
		.cards { display: flex; gap: 6px; margin-bottom: 8px; flex-wrap: wrap; }
		.card { flex: 1; min-width: 90px; border: 1px solid #ccd; border-radius: 4px; padding: 4px 7px; display: flex; justify-content: space-between; gap: 6px; }
		table { width: 100%; border-collapse: collapse; }
		thead { display: table-header-group; }
		tr { page-break-inside: avoid; }
		th { background: #16233A; color: #fff; text-align: left; padding: 5px; font-size: 10.5px; }
		td { padding: 4px 5px; border-bottom: 1px solid #ddd; vertical-align: top; }
		.c { text-align: center; }
		.dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 4px; }
		.ok { font-weight: bold; color: #2e7d32; }
		.inc { font-weight: bold; color: #c77700; }
		.foot { display: flex; justify-content: space-between; margin-top: 10px; }
		.sign { margin-top: 40px; display: flex; justify-content: space-between; }
		.sign div { width: 28%; border-top: 1px solid #111; text-align: center; padding-top: 3px; }
	</style></head><body>
		<div class="head">
			<img src="${logo}" onerror="this.style.display='none'">
			<div class="title"><h2>WORK PERMIT REPORT</h2><div>${filt}</div></div>
		</div>
		${cards ? `<div class="cards">${cards}</div>` : ""}
		<table>
			<thead><tr>
				<th class="c" style="width:3%">#</th>
				<th style="width:8%">Work Permit</th>
				<th class="c" style="width:7%">Date</th>
				<th style="width:7%">Permit No.</th>
				<th style="width:6%">Colour</th>
				<th style="width:11%">Department</th>
				<th style="width:13%">Issued To</th>
				<th style="width:11%">Receiver Dept.</th>
				<th style="width:11%">Validity</th>
				<th style="width:12%">Supervisor</th>
				<th style="width:11%">Status</th>
			</tr></thead>
			<tbody>${body}</tbody>
		</table>
		<div class="foot">
			<span>Total permits: <b>${rows.length}</b></span>
			<span>Printed on ${e(frappe.datetime.str_to_user(frappe.datetime.now_datetime()))}</span>
		</div>
		<div class="sign"><div>Prepared By</div><div>HSE In-charge</div><div>Approved By</div></div>
	</body></html>`;

	const old = document.getElementById("wp-report-print-frame");
	if (old) old.remove();
	const frame = document.createElement("iframe");
	frame.id = "wp-report-print-frame";
	frame.style.cssText = "position:fixed;right:0;bottom:0;width:0;height:0;border:0;";
	document.body.appendChild(frame);
	const doc = frame.contentWindow.document;
	doc.open();
	doc.write(html);
	doc.close();

	let done = false;
	const go = () => {
		if (done) return;
		done = true;
		frame.contentWindow.focus();
		frame.contentWindow.print();
	};
	const img = doc.querySelector("img");
	if (img && !img.complete) {
		img.onload = go;
		img.onerror = go;
		setTimeout(go, 2000);
	} else {
		setTimeout(go, 300);
	}
}