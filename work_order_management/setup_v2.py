import frappe

CHILD = "Work Order Completion Employee"


def _insert_after(doc, after, field):
    if any(f.fieldname == field["fieldname"] for f in doc.fields):
        return
    new = doc.append("fields", field)
    fields = [f for f in doc.fields if f is not new]
    fields.insert([f.fieldname for f in fields].index(after) + 1, new)
    doc.fields = fields
    for i, f in enumerate(doc.fields, 1):
        f.idx = i


def _set(doc, fieldname, **props):
    for f in doc.fields:
        if f.fieldname == fieldname:
            for k, v in props.items():
                setattr(f, k, v)


def create():
    # Child table for multiple "Completed By" employees
    if not frappe.db.exists("DocType", CHILD):
        frappe.get_doc({
            "doctype": "DocType", "name": CHILD, "module": "Work Order Management", "custom": 0,
            "istable": 1, "editable_grid": 1,
            "fields": [
                {"fieldname": "employee", "fieldtype": "Link", "label": "Employee",
                 "options": "Employee", "reqd": 1, "in_list_view": 1},
                {"fieldname": "employee_name", "fieldtype": "Data", "label": "Employee Name",
                 "fetch_from": "employee.employee_name", "read_only": 1, "in_list_view": 1},
                {"fieldname": "card_no", "fieldtype": "Data", "label": "Card No",
                 "fetch_from": "employee.attendance_device_id", "read_only": 1, "in_list_view": 1},
            ],
        }).insert()
        print(f"{CHILD}: created")

    # Work Order Slip: Requested By from the logged-in user's Employee
    slip = frappe.get_doc("DocType", "Work Order Slip")
    _set(slip, "requested_by", hidden=1, read_only=1)
    after = "requested_by"
    for field in [
        {"fieldname": "requested_by_employee", "fieldtype": "Link", "label": "Requested By / Incharge",
         "options": "Employee", "read_only": 1},
        {"fieldname": "requested_by_name", "fieldtype": "Data", "label": "Requested By Name",
         "fetch_from": "requested_by_employee.employee_name", "read_only": 1},
        {"fieldname": "requested_by_card", "fieldtype": "Data", "label": "Requested By Card No",
         "fetch_from": "requested_by_employee.attendance_device_id", "read_only": 1},
    ]:
        _insert_after(slip, after, field)
        after = field["fieldname"]
    slip.save()
    print("Work Order Slip: updated")

    # Work Order Completion: multiple Completed By, Received By as Employee
    comp = frappe.get_doc("DocType", "Work Order Completion")
    _set(comp, "completed_by", hidden=1, read_only=1, mandatory_depends_on="")
    _set(comp, "received_by", hidden=1, read_only=1)
    _insert_after(comp, "completed_by", {
        "fieldname": "completed_by_employees", "fieldtype": "Table MultiSelect",
        "label": "Completed By / Incharge", "options": CHILD,
    })
    after = "received_by"
    for field in [
        {"fieldname": "received_by_employee", "fieldtype": "Link", "label": "Received By (Requesting Dept)",
         "options": "Employee", "description": "Person who accepted the machine back"},
        {"fieldname": "received_by_name", "fieldtype": "Data", "label": "Received By Name",
         "fetch_from": "received_by_employee.employee_name", "read_only": 1},
        {"fieldname": "received_by_card", "fieldtype": "Data", "label": "Received By Card No",
         "fetch_from": "received_by_employee.attendance_device_id", "read_only": 1},
    ]:
        _insert_after(comp, after, field)
        after = field["fieldname"]
    comp.save()
    print("Work Order Completion: updated")

    frappe.db.commit()
    print("ALL DONE")
