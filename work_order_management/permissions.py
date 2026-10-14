import json

import frappe

# Only these see every Work Order Slip / Completion (Administrator always does)
FULL_ACCESS_ROLES = {"System Manager", "Work Order Approver"}

SLIP = "Work Order Slip"
COMPLETION = "Work Order Completion"


def has_full_access(user):
    if user == "Administrator":
        return True
    return bool(FULL_ACCESS_ROLES & set(frappe.get_roles(user)))


def _mine_sql(alias, user):
    """Created by the user, or assigned to the user (Assigned To)."""
    u = frappe.db.escape(user)
    like = frappe.db.escape(f'%"{user}"%')
    return f"({alias}.`owner` = {u} or {alias}.`_assign` like {like})"


def slip_condition_for(user, alias="`tabWork Order Slip`"):
    """Empty string means no restriction (also used by the Daily Work Orders Report)."""
    if has_full_access(user):
        return ""
    return _mine_sql(alias, user)


# ---------------- Hooks: lists, reports, search ----------------
# Documents shared with a user (Share button) are added by Frappe automatically.

def slip_query(user=None):
    return slip_condition_for(user or frappe.session.user)


def completion_query(user=None):
    user = user or frappe.session.user
    if has_full_access(user):
        return ""
    alias = "`tabWork Order Completion`"
    # Own / assigned completions, plus completions of slips the user created or was assigned
    return (
        f"({_mine_sql(alias, user)} or {alias}.`work_order_slip` in "
        f"(select s.name from `tabWork Order Slip` s where {_mine_sql('s', user)}))"
    )


# ---------------- Hooks: opening a single document ----------------

def _assigned_users(doc):
    try:
        return json.loads(doc.get("_assign") or "[]")
    except Exception:
        return []


def _is_shared(doctype, name, user):
    return bool(frappe.db.exists("DocShare", {"share_doctype": doctype, "share_name": name, "user": user}))


def _is_mine(doc, user):
    return doc.get("owner") == user or user in _assigned_users(doc) or _is_shared(doc.doctype, doc.name, user)


def slip_has_permission(doc, ptype=None, user=None):
    user = user or frappe.session.user
    if has_full_access(user) or doc.is_new():
        return None  # normal role permissions apply
    return None if _is_mine(doc, user) else False


def completion_has_permission(doc, ptype=None, user=None):
    user = user or frappe.session.user
    if has_full_access(user) or doc.is_new() or _is_mine(doc, user):
        return None
    slip_name = doc.get("work_order_slip")
    if slip_name and frappe.db.exists(SLIP, slip_name):
        slip = frappe.get_doc(SLIP, slip_name)
        if _is_mine(slip, user):
            return None
    return False