import frappe

MODULE = "Work Order Management"
ROLE = "Work Order User"


def _perms(submittable):
    perms = []
    for role in ("System Manager", ROLE):
        p = {"role": role, "read": 1, "write": 1, "create": 1, "print": 1,
             "email": 1, "report": 1, "export": 1, "share": 1}
        if role == "System Manager":
            p["delete"] = 1
        if submittable:
            p.update(submit=1, cancel=1, amend=1)
        perms.append(p)
    return perms


def _make(spec):
    if frappe.db.exists("DocType", spec["name"]):
        print(f"{spec['name']}: pehle se maujood hai, chhod diya")
        return
    frappe.get_doc({"doctype": "DocType", "module": MODULE, "custom": 0, **spec}).insert()
    print(f"{spec['name']}: ban gaya")


PART_FIELDS = [
    {"fieldname": "part_name", "fieldtype": "Data", "label": "Part Name", "reqd": 1, "in_list_view": 1},
    {"fieldname": "action", "fieldtype": "Select", "label": "Action", "options": "Repaired\nReplaced",
     "default": "Repaired", "in_list_view": 1},
    {"fieldname": "qty", "fieldtype": "Float", "label": "Qty", "default": "1", "in_list_view": 1},
    {"fieldname": "remarks", "fieldtype": "Data", "label": "Remarks", "in_list_view": 1},
]

SLIP_FIELDS = [
    {"fieldname": "priority", "fieldtype": "Select", "label": "Priority", "options": "Urgent\nNormal\nEmergency",
     "default": "Normal", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
    {"fieldname": "reference_no", "fieldtype": "Data", "label": "Reference No."},
    {"fieldname": "cb_1", "fieldtype": "Column Break"},
    {"fieldname": "date", "fieldtype": "Date", "label": "Date", "default": "Today", "reqd": 1, "in_list_view": 1},
    {"fieldname": "time", "fieldtype": "Time", "label": "Time"},

    {"fieldname": "sb_dept", "fieldtype": "Section Break", "label": "Department / Machine"},
    {"fieldname": "requesting_department", "fieldtype": "Link", "label": "Requesting Department",
     "options": "Department", "reqd": 1, "in_standard_filter": 1},
    {"fieldname": "shift", "fieldtype": "Link", "label": "Shift", "options": "Shift Type"},
    {"fieldname": "cb_2", "fieldtype": "Column Break"},
    {"fieldname": "asset", "fieldtype": "Data", "label": "Asset (optional)"},
    {"fieldname": "machine_name", "fieldtype": "Data", "label": "Machine Name", "in_list_view": 1},

    {"fieldname": "sb_defect", "fieldtype": "Section Break", "label": "Defect Description"},
    {"fieldname": "defect_description", "fieldtype": "Small Text", "label": "Defect Description", "reqd": 1},

    {"fieldname": "sb_assign", "fieldtype": "Section Break", "label": "Assignment"},
    {"fieldname": "assigned_department", "fieldtype": "Link", "label": "Work Assigned To Department",
     "options": "Department", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
    {"fieldname": "cb_3", "fieldtype": "Column Break"},
    {"fieldname": "requested_by", "fieldtype": "Link", "label": "Requested By / Incharge", "options": "User"},

    {"fieldname": "sb_status", "fieldtype": "Section Break", "label": "Work Status"},
    {"fieldname": "work_status", "fieldtype": "Select", "label": "Work Status",
     "options": "Not Started\nPending\nCompleted", "default": "Not Started", "read_only": 1,
     "allow_on_submit": 1, "no_copy": 1, "in_list_view": 1, "in_standard_filter": 1},
    {"fieldname": "cb_4", "fieldtype": "Column Break"},
    {"fieldname": "amended_from", "fieldtype": "Link", "label": "Amended From", "options": "Work Order Slip",
     "read_only": 1, "no_copy": 1, "print_hide": 1},
]

COMPLETION_FIELDS = [
    {"fieldname": "work_order_slip", "fieldtype": "Link", "label": "Work Order Slip",
     "options": "Work Order Slip", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
    {"fieldname": "assigned_department", "fieldtype": "Link", "label": "Assigned Department",
     "options": "Department", "fetch_from": "work_order_slip.assigned_department", "read_only": 1,
     "in_list_view": 1, "in_standard_filter": 1},
    {"fieldname": "cb_1", "fieldtype": "Column Break"},
    {"fieldname": "priority", "fieldtype": "Data", "label": "Priority",
     "fetch_from": "work_order_slip.priority", "read_only": 1},
    {"fieldname": "reference_no", "fieldtype": "Data", "label": "Reference No.",
     "fetch_from": "work_order_slip.reference_no", "read_only": 1},
    {"fieldname": "cb_2", "fieldtype": "Column Break"},
    {"fieldname": "slip_date", "fieldtype": "Date", "label": "Slip Date",
     "fetch_from": "work_order_slip.date", "read_only": 1},
    {"fieldname": "slip_time", "fieldtype": "Time", "label": "Slip Time",
     "fetch_from": "work_order_slip.time", "read_only": 1},

    {"fieldname": "sb_slip", "fieldtype": "Section Break", "label": "Slip Details"},
    {"fieldname": "requesting_department", "fieldtype": "Link", "label": "Requesting Department",
     "options": "Department", "fetch_from": "work_order_slip.requesting_department", "read_only": 1},
    {"fieldname": "shift", "fieldtype": "Data", "label": "Shift",
     "fetch_from": "work_order_slip.shift", "read_only": 1},
    {"fieldname": "cb_3", "fieldtype": "Column Break"},
    {"fieldname": "machine_name", "fieldtype": "Data", "label": "Machine Name",
     "fetch_from": "work_order_slip.machine_name", "read_only": 1},
    {"fieldname": "asset", "fieldtype": "Data", "label": "Asset",
     "fetch_from": "work_order_slip.asset", "read_only": 1},
    {"fieldname": "sb_slip_defect", "fieldtype": "Section Break"},
    {"fieldname": "defect_description", "fieldtype": "Small Text", "label": "Defect Description",
     "fetch_from": "work_order_slip.defect_description", "read_only": 1},

    {"fieldname": "sb_repair", "fieldtype": "Section Break", "label": "Details of Defects, Repair and Parts"},
    {"fieldname": "details_of_defects", "fieldtype": "Text", "label": "Details of Defects Found & Repair Done",
     "reqd": 1},
    {"fieldname": "parts", "fieldtype": "Table", "label": "Repaired / Replaced Parts",
     "options": "Work Order Completion Part"},

    {"fieldname": "sb_status", "fieldtype": "Section Break", "label": "Status and Completion"},
    {"fieldname": "complaint_type", "fieldtype": "Select", "label": "Complaint Type", "options": "\nNew\nRepeated"},
    {"fieldname": "work_status", "fieldtype": "Select", "label": "Work Status", "options": "Pending\nCompleted",
     "default": "Pending", "reqd": 1, "in_list_view": 1, "in_standard_filter": 1},
    {"fieldname": "completed_by", "fieldtype": "Link", "label": "Completed By / Incharge", "options": "User",
     "mandatory_depends_on": "eval:doc.work_status=='Completed'"},
    {"fieldname": "cb_4", "fieldtype": "Column Break"},
    {"fieldname": "completion_date", "fieldtype": "Date", "label": "Completion Date",
     "mandatory_depends_on": "eval:doc.work_status=='Completed'"},
    {"fieldname": "completion_time", "fieldtype": "Time", "label": "Completion Time",
     "mandatory_depends_on": "eval:doc.work_status=='Completed'"},
    {"fieldname": "downtime_hours", "fieldtype": "Float", "label": "Downtime (Hours)", "read_only": 1,
     "precision": "1", "description": "Slip date/time se completion date/time tak"},
    {"fieldname": "cb_5", "fieldtype": "Column Break"},
    {"fieldname": "received_by", "fieldtype": "Link", "label": "Received By (Requesting Dept)", "options": "User",
     "description": "Jis ne machine wapas li"},
    {"fieldname": "sb_remarks", "fieldtype": "Section Break"},
    {"fieldname": "remarks", "fieldtype": "Small Text", "label": "Remarks"},
    {"fieldname": "amended_from", "fieldtype": "Link", "label": "Amended From",
     "options": "Work Order Completion", "read_only": 1, "no_copy": 1, "print_hide": 1},
]


def create():
    if not frappe.db.exists("Role", ROLE):
        frappe.get_doc({"doctype": "Role", "role_name": ROLE, "desk_access": 1}).insert()
        print(f"Role '{ROLE}' ban gaya")

    _make({"name": "Work Order Completion Part", "istable": 1, "editable_grid": 1, "fields": PART_FIELDS})

    _make({
        "name": "Work Order Slip", "is_submittable": 1, "track_changes": 1,
        "autoname": "WOS-.####", "naming_rule": "Expression (old style)",
        "title_field": "machine_name", "fields": SLIP_FIELDS, "permissions": _perms(True),
    })

    _make({
        "name": "Work Order Completion", "is_submittable": 1, "track_changes": 1,
        "autoname": "WOC-.####", "naming_rule": "Expression (old style)",
        "title_field": "work_order_slip", "fields": COMPLETION_FIELDS, "permissions": _perms(True),
    })

    # Completion banne ke baad Slip mein us ka link aur Connections
    slip = frappe.get_doc("DocType", "Work Order Slip")
    if not any(f.fieldname == "work_order_completion" for f in slip.fields):
        new_field = slip.append("fields", {
            "fieldname": "work_order_completion", "fieldtype": "Link", "label": "Work Order Completion",
            "options": "Work Order Completion", "read_only": 1, "allow_on_submit": 1, "no_copy": 1,
        })
        fields = [f for f in slip.fields if f is not new_field]
        fields.insert([f.fieldname for f in fields].index("cb_4") + 1, new_field)
        slip.fields = fields
        for i, f in enumerate(slip.fields, 1):
            f.idx = i
    if not any(l.link_doctype == "Work Order Completion" for l in slip.links):
        slip.append("links", {"link_doctype": "Work Order Completion", "link_fieldname": "work_order_slip"})
    slip.save()
    print("Work Order Slip mein Completion ka link aur Connections jud gaye")

    frappe.db.commit()
    print("SAB TAYYAR")
