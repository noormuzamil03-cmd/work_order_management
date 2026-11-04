# Work Permit Report: list of Work Permits with colour, department, issued to, timing and status

import frappe
from frappe.utils import add_to_date, getdate, nowdate


def short_dept(name):
    return str(name).rsplit(" - ", 1)[0] if name else ""


def hhmm(t):
    return str(t).zfill(8)[:5] if t else ""


def execute(filters=None):
    filters = frappe._dict(filters or {})
    from_date = getdate(filters.from_date or add_to_date(nowdate(), days=-30))
    to_date = getdate(filters.to_date or nowdate())

    flt = {"creation": ["between", [f"{from_date} 00:00:00", f"{to_date} 23:59:59"]]}
    for f in ("department", "receiver_department", "permit_color", "permit_issued_to", "site_supervisor"):
        if filters.get(f):
            flt[f] = filters.get(f)
    if filters.get("work_status") == "Open":
        flt["work_status"] = ["is", "not set"]
    elif filters.get("work_status"):
        flt["work_status"] = filters.get("work_status")

    permits = frappe.get_all(
        "Work Permit",
        filters=flt,
        fields=["name", "creation", "permit_no", "reference_no", "permit_color", "department",
                "permit_issued_to", "permit_issued_to_name", "receiver_department",
                "valid_from", "valid_until", "valid_day", "valid_until_work_complete",
                "site_supervisor_name", "work_status", "possible_hazards"],
        order_by="creation desc",
        limit_page_length=0,
    )

    data = []
    for p in permits:
        if p.valid_until_work_complete:
            validity = "Until work complete"
        else:
            validity = " - ".join(x for x in (hhmm(p.valid_from), hhmm(p.valid_until)) if x)
            if p.valid_day:
                validity = (validity + " (" + p.valid_day + ")").strip()
        data.append(
            {
                "name": p.name,
                "date": getdate(p.creation),
                "permit_no": p.permit_no or p.reference_no,
                "permit_color": p.permit_color,
                "department": short_dept(p.department),
                "issued_to": p.permit_issued_to_name or p.permit_issued_to,
                "receiver_department": short_dept(p.receiver_department),
                "validity": validity,
                "supervisor": p.site_supervisor_name,
                "hazards": (p.possible_hazards or "").replace("\n", " ")[:120],
                "status": p.work_status or "Open",
            }
        )

    def count(key, val):
        return len([d for d in data if d[key] == val])

    summary = [
        {"label": "Total Permits", "value": len(data), "datatype": "Int", "indicator": "blue"},
        {"label": "Red", "value": count("permit_color", "Red"), "datatype": "Int", "indicator": "red"},
        {"label": "Green", "value": count("permit_color", "Green"), "datatype": "Int", "indicator": "green"},
        {"label": "Yellow", "value": count("permit_color", "Yellow"), "datatype": "Int", "indicator": "yellow"},
        {"label": "Blue", "value": count("permit_color", "Blue"), "datatype": "Int", "indicator": "blue"},
        {"label": "Work complete", "value": count("status", "Work complete"), "datatype": "Int", "indicator": "green"},
        {"label": "Work incomplete", "value": count("status", "Work incomplete"), "datatype": "Int", "indicator": "orange"},
        {"label": "Open", "value": count("status", "Open"), "datatype": "Int", "indicator": "gray"},
    ]
    return get_columns(), data, None, None, summary


def get_columns():
    return [
        {"label": "Work Permit", "fieldname": "name", "fieldtype": "Link", "options": "Work Permit", "width": 120},
        {"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": "Permit No.", "fieldname": "permit_no", "fieldtype": "Data", "width": 100},
        {"label": "Colour", "fieldname": "permit_color", "fieldtype": "Data", "width": 90},
        {"label": "Department", "fieldname": "department", "fieldtype": "Data", "width": 150},
        {"label": "Issued To", "fieldname": "issued_to", "fieldtype": "Data", "width": 160},
        {"label": "Receiver Department", "fieldname": "receiver_department", "fieldtype": "Data", "width": 150},
        {"label": "Validity", "fieldname": "validity", "fieldtype": "Data", "width": 160},
        {"label": "Supervisor", "fieldname": "supervisor", "fieldtype": "Data", "width": 150},
        {"label": "Hazards", "fieldname": "hazards", "fieldtype": "Data", "width": 200},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 130},
    ]