import frappe

# Roles that can see every Work Order Slip and Completion
FULL_ACCESS_ROLES = {"System Manager", "Work Order Approver"}


def has_full_access(user):
    if user == "Administrator":
        return True
    return bool(FULL_ACCESS_ROLES & set(frappe.get_roles(user)))


def get_user_departments(user):
    """User's department(s) from Employee, including all child departments."""
    cache = frappe.flags.setdefault("wom_dept_cache", {})
    if user in cache:
        return cache[user]

    result = set()
    for dept in frappe.get_all("Employee", filters={"user_id": user, "status": "Active"}, pluck="department"):
        if not dept:
            continue
        node = frappe.db.get_value("Department", dept, ["lft", "rgt"], as_dict=True)
        if not node:
            result.add(dept)
            continue
        result.update(frappe.get_all(
            "Department",
            filters={"lft": [">=", node.lft], "rgt": ["<=", node.rgt]},
            pluck="name",
        ))
    cache[user] = sorted(result)
    return cache[user]


def _sql_in(values):
    return ", ".join(frappe.db.escape(v) for v in values)


def _condition(user, alias, user_fields):
    """SQL condition: rows the user is involved in."""
    u = frappe.db.escape(user)
    parts = [f"{alias}.`{field}` = {u}" for field in user_fields]
    depts = get_user_departments(user)
    if depts:
        d = _sql_in(depts)
        parts.append(f"{alias}.`requesting_department` in ({d})")
        parts.append(f"{alias}.`assigned_department` in ({d})")
    return "(" + " or ".join(parts) + ")"


SLIP_USER_FIELDS = ("owner", "requested_by")
COMPLETION_USER_FIELDS = ("owner", "completed_by", "received_by")


def slip_condition_for(user, alias="`tabWork Order Slip`"):
    """Empty string means no restriction."""
    if has_full_access(user):
        return ""
    return _condition(user, alias, SLIP_USER_FIELDS)


# ---------------- Hooks: lists, reports, search ----------------

def slip_query(user=None):
    return slip_condition_for(user or frappe.session.user)


def completion_query(user=None):
    user = user or frappe.session.user
    if has_full_access(user):
        return ""
    return _condition(user, "`tabWork Order Completion`", COMPLETION_USER_FIELDS)


# ---------------- Hooks: opening a single document ----------------

def _involved(doc, user, user_fields):
    if any(doc.get(field) == user for field in user_fields):
        return True
    depts = set(get_user_departments(user))
    return doc.get("requesting_department") in depts or doc.get("assigned_department") in depts


def slip_has_permission(doc, ptype=None, user=None):
    user = user or frappe.session.user
    if has_full_access(user) or doc.is_new():
        return None  # normal role permissions apply
    return None if _involved(doc, user, SLIP_USER_FIELDS) else False


def completion_has_permission(doc, ptype=None, user=None):
    user = user or frappe.session.user
    if has_full_access(user) or doc.is_new():
        return None
    return None if _involved(doc, user, COMPLETION_USER_FIELDS) else False
