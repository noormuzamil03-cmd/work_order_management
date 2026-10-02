import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime


def execute(filters=None):
    filters = frappe._dict(filters or {})
    if filters.from_date and filters.to_date and filters.from_date > filters.to_date:
        frappe.throw(_("From Date cannot be after To Date"))
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": _("Work Order ID"), "fieldname": "work_order", "fieldtype": "Link",
         "options": "Work Order Slip", "width": 120},
        {"label": _("Reference"), "fieldname": "reference_no", "fieldtype": "Data", "width": 100},
        {"label": _("Fault Date"), "fieldname": "fault_date", "fieldtype": "Date", "width": 100},
        {"label": _("OK Date"), "fieldname": "ok_date", "fieldtype": "Date", "width": 100},
        {"label": _("Fault Time"), "fieldname": "fault_time", "fieldtype": "Data", "width": 85},
        {"label": _("OK Time"), "fieldname": "ok_time", "fieldtype": "Data", "width": 85},
        {"label": _("Downtime (DD:HH:MM)"), "fieldname": "downtime", "fieldtype": "Data", "width": 150},
        {"label": _("Shift"), "fieldname": "shift", "fieldtype": "Link", "options": "Shift Type", "width": 110},
        {"label": _("Issuing Department"), "fieldname": "issuing_department", "fieldtype": "Link",
         "options": "Department", "width": 160},
        {"label": _("Receiving Department"), "fieldname": "receiving_department", "fieldtype": "Link",
         "options": "Department", "width": 160},
        {"label": _("Fault Description"), "fieldname": "fault_description", "fieldtype": "Data", "width": 280},
        {"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 220},
        {"label": _("Completed By"), "fieldname": "completed_by", "fieldtype": "Link",
         "options": "User", "width": 180},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 140},
        {"label": _("Type"), "fieldname": "complaint_type", "fieldtype": "Data", "width": 90},
    ]


def get_data(filters):
    conditions = ["s.docstatus = 1"]
    params = {}

    if filters.from_date:
        conditions.append("s.date >= %(from_date)s")
        params["from_date"] = filters.from_date
    if filters.to_date:
        conditions.append("s.date <= %(to_date)s")
        params["to_date"] = filters.to_date
    if filters.status == "Open":
        conditions.append("IFNULL(s.work_status, '') != 'Completed'")
    elif filters.status:
        conditions.append("s.work_status = %(status)s")
        params["status"] = filters.status

    rows = frappe.db.sql(
        f"""
        SELECT
            s.name AS work_order, s.reference_no, s.date AS fault_date, s.time AS fault_time,
            s.shift, s.requesting_department AS issuing_department,
            s.assigned_department AS receiving_department,
            s.defect_description AS fault_description, s.work_status AS status,
            c.completion_date AS ok_date, c.completion_time AS ok_time,
            c.remarks, c.completed_by, c.complaint_type
        FROM `tabWork Order Slip` s
        LEFT JOIN `tabWork Order Completion` c
            ON c.work_order_slip = s.name AND c.docstatus != 2
        WHERE {" AND ".join(conditions)}
        ORDER BY s.date, s.time, s.name
        """,
        params,
        as_dict=True,
    )

    for r in rows:
        r.downtime = get_downtime(r)
        r.fault_time = hhmm(r.fault_time)
        r.ok_time = hhmm(r.ok_time)
    return rows


def hhmm(t):
    """Time value -> 'HH:MM'."""
    if not t:
        return ""
    parts = str(t).split(":")
    try:
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    except Exception:
        return str(t)


def get_downtime(r):
    """Fault date/time to OK date/time as DD:HH:MM. Still open: counted until now."""
    if not r.fault_date:
        return ""
    start = get_datetime(f"{r.fault_date} {r.fault_time or '00:00:00'}")

    if r.ok_date and r.status == "Completed":
        end = get_datetime(f"{r.ok_date} {r.ok_time or '00:00:00'}")
        suffix = ""
    else:
        end = now_datetime()
        suffix = " (open)"

    minutes = int((end - start).total_seconds() // 60)
    if minutes < 0:
        return ""
    days, rest = divmod(minutes, 1440)
    hours, mins = divmod(rest, 60)
    return f"{days:02d}:{hours:02d}:{mins:02d}{suffix}"