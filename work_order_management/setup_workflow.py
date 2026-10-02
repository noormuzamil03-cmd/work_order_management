import frappe

DT = "Work Order Completion"
WF_NAME = "Work Order Completion Approval"
USER_ROLE = "Work Order User"
APPROVER_ROLE = "Work Order Approver"

STATES = [
    ("Draft", ""),
    ("Pending Approval", "Warning"),
    ("Rework Required", "Danger"),
    ("Approved", "Success"),
    ("Cancelled", "Inverse"),
]
ACTIONS = ["Send for Approval", "Approve", "Send Back for Rework", "Cancel"]
LOCK = "eval:doc.workflow_state != 'Pending Approval'"


def _insert_after(doc, after, field):
    if any(f.fieldname == field["fieldname"] for f in doc.fields):
        return
    new = doc.append("fields", field)
    fields = [f for f in doc.fields if f is not new]
    fields.insert([f.fieldname for f in fields].index(after) + 1, new)
    doc.fields = fields
    for i, f in enumerate(doc.fields, 1):
        f.idx = i


def _add_perm(doc, perm):
    if not any(p.role == perm["role"] for p in doc.permissions):
        doc.append("permissions", perm)


def create_masters():
    for role in (USER_ROLE, APPROVER_ROLE):
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert()
    for name, style in STATES:
        if not frappe.db.exists("Workflow State", name):
            frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": name, "style": style}).insert()
    for action in ACTIONS:
        if not frappe.db.exists("Workflow Action Master", action):
            frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert()
    print("Roles, states and actions ready")


def update_doctypes():
    comp = frappe.get_doc("DocType", DT)
    for f in comp.fields:
        if f.fieldname in ("complaint_type", "work_status"):
            f.read_only_depends_on = LOCK

    after = "remarks"
    for field in [
        {"fieldname": "sb_approval", "fieldtype": "Section Break", "label": "Approval"},
        {"fieldname": "approver_remarks", "fieldtype": "Small Text", "label": "Approver Remarks",
         "read_only_depends_on": LOCK, "description": "Required when sending back for rework"},
        {"fieldname": "cb_approval", "fieldtype": "Column Break"},
        {"fieldname": "approved_by", "fieldtype": "Link", "label": "Approved By", "options": "User",
         "read_only": 1, "allow_on_submit": 1, "no_copy": 1},
        {"fieldname": "approved_on", "fieldtype": "Datetime", "label": "Approved On",
         "read_only": 1, "allow_on_submit": 1, "no_copy": 1},
        {"fieldname": "workflow_state", "fieldtype": "Link", "label": "Workflow State",
         "options": "Workflow State", "hidden": 1, "read_only": 1, "allow_on_submit": 1, "no_copy": 1},
    ]:
        _insert_after(comp, after, field)
        after = field["fieldname"]

    _add_perm(comp, {"role": APPROVER_ROLE, "read": 1, "write": 1, "submit": 1, "print": 1,
                     "email": 1, "report": 1, "export": 1, "share": 1})
    comp.save()

    slip = frappe.get_doc("DocType", "Work Order Slip")
    for f in slip.fields:
        if f.fieldname == "work_status":
            f.options = "Not Started\nIn Progress\nPending Approval\nRework Required\nCompleted"
    _add_perm(slip, {"role": APPROVER_ROLE, "read": 1, "print": 1, "report": 1, "export": 1})
    slip.save()
    print("DocTypes updated")


def create_workflow():
    if frappe.db.exists("Workflow", WF_NAME):
        frappe.delete_doc("Workflow", WF_NAME, force=1)

    frappe.get_doc({
        "doctype": "Workflow",
        "workflow_name": WF_NAME,
        "document_type": DT,
        "is_active": 1,
        "send_email_alert": 1,
        "workflow_state_field": "workflow_state",
        "states": [
            {"state": "Draft", "doc_status": "0", "allow_edit": USER_ROLE},
            {"state": "Pending Approval", "doc_status": "0", "allow_edit": APPROVER_ROLE},
            {"state": "Rework Required", "doc_status": "0", "allow_edit": USER_ROLE},
            {"state": "Approved", "doc_status": "1", "allow_edit": APPROVER_ROLE},
            {"state": "Cancelled", "doc_status": "2", "allow_edit": "System Manager"},
        ],
        "transitions": [
            {"state": "Draft", "action": "Send for Approval", "next_state": "Pending Approval",
             "allowed": USER_ROLE, "allow_self_approval": 1},
            {"state": "Rework Required", "action": "Send for Approval", "next_state": "Pending Approval",
             "allowed": USER_ROLE, "allow_self_approval": 1},
            {"state": "Pending Approval", "action": "Approve", "next_state": "Approved",
             "allowed": APPROVER_ROLE, "allow_self_approval": 1,
             "condition": "doc.work_status == 'Completed'"},
            {"state": "Pending Approval", "action": "Send Back for Rework", "next_state": "Rework Required",
             "allowed": APPROVER_ROLE, "allow_self_approval": 1},
            {"state": "Approved", "action": "Cancel", "next_state": "Cancelled",
             "allowed": "System Manager", "allow_self_approval": 1},
        ],
    }).insert()
    print(f"Workflow '{WF_NAME}' created")


def create():
    create_masters()
    update_doctypes()
    create_workflow()
    frappe.db.commit()
    print("ALL DONE")


def ensure_workflow():
    """Runs automatically on install and migrate: roles, states, actions and workflow."""
    create_masters()
    if not frappe.db.exists("Workflow", WF_NAME):
        create_workflow()
    frappe.db.commit()
