import json

import frappe

NAME = "Work Order Management"
MODULE = "Work Order Management"


def _filter(doctype, field, op, value):
    return json.dumps([[doctype, field, op, value, False]])


SHORTCUTS = [
    {"label": "New Work Order Slip", "type": "DocType", "link_to": "Work Order Slip",
     "doc_view": "New", "color": "Blue"},
    {"label": "Open Work Orders", "type": "DocType", "link_to": "Work Order Slip", "doc_view": "List",
     "color": "Orange", "stats_filter": _filter("Work Order Slip", "work_status", "!=", "Completed")},
    {"label": "Pending Approval", "type": "DocType", "link_to": "Work Order Completion", "doc_view": "List",
     "color": "Yellow", "stats_filter": _filter("Work Order Completion", "workflow_state", "=", "Pending Approval")},
    {"label": "Rework Required", "type": "DocType", "link_to": "Work Order Completion", "doc_view": "List",
     "color": "Red", "stats_filter": _filter("Work Order Completion", "workflow_state", "=", "Rework Required")},
    {"label": "Daily Work Orders Report", "type": "Report", "link_to": "Daily Work Orders Report",
     "color": "Green"},
]

CARDS = [
    ("Work Orders", [
        ("Work Order Slip", "DocType", "Work Order Slip", 0),
        ("Work Order Completion", "DocType", "Work Order Completion", 0),
    ]),
    ("Reports", [
        ("Daily Work Orders Report", "Report", "Daily Work Orders Report", 1),
        ("Employee Leave Encashment Report", "Report", "Employee Leave Encashment Report", 1),
    ]),
    ("Setup", [
        ("Employee", "DocType", "Employee", 0),
        ("Department", "DocType", "Department", 0),
        ("Shift Type", "DocType", "Shift Type", 0),
    ]),
]

ROLES = ["Work Order User", "Work Order Approver", "System Manager"]


def _content():
    blocks = [{"id": "hdr1", "type": "header",
               "data": {"text": '<span class="h4"><b>Work Orders</b></span>', "col": 12}}]
    for i, s in enumerate(SHORTCUTS, 1):
        blocks.append({"id": f"sc{i}", "type": "shortcut", "data": {"shortcut_name": s["label"], "col": 3}})
    blocks.append({"id": "sp1", "type": "spacer", "data": {"col": 12}})
    blocks.append({"id": "hdr2", "type": "header",
                   "data": {"text": '<span class="h4"><b>Reports &amp; Masters</b></span>', "col": 12}})
    for i, (card, _links) in enumerate(CARDS, 1):
        blocks.append({"id": f"cd{i}", "type": "card", "data": {"card_name": card, "col": 4}})
    return json.dumps(blocks)


def create():
    if frappe.db.exists("Workspace", NAME):
        frappe.delete_doc("Workspace", NAME, force=1)

    ws = frappe.new_doc("Workspace")
    ws.update({
        "label": NAME,
        "title": NAME,
        "module": MODULE,
        "public": 1,
        "icon": "tool",
        "content": _content(),
    })

    for s in SHORTCUTS:
        ws.append("shortcuts", s)

    for card, links in CARDS:
        ws.append("links", {"type": "Card Break", "label": card, "link_count": len(links)})
        for label, link_type, link_to, is_report in links:
            if link_type == "Report" and not frappe.db.exists("Report", link_to):
                continue
            ws.append("links", {"type": "Link", "label": label, "link_type": link_type,
                                "link_to": link_to, "is_query_report": is_report, "onboard": 0})

    for role in ROLES:
        if frappe.db.exists("Role", role):
            ws.append("roles", {"role": role})

    ws.insert(ignore_permissions=True)
    frappe.db.commit()
    print("WORKSPACE CREATED:", ws.name)
