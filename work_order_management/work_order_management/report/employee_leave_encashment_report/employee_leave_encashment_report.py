import frappe
from frappe import _
from frappe.utils import flt, getdate, today

# Possible names of a CNIC custom field on Employee (the first one found is used)
CNIC_FIELDS = ("cnic", "cnic_no", "cnic_number", "custom_cnic", "custom_cnic_no", "custom_cnic_number", "national_id")
# Leave Encashment "days" field name differs between HRMS versions
DAYS_FIELDS = ("encashment_days", "encashable_days", "actual_encashable_days")
# Set to False if outstanding Employee Advances should not be deducted
DEDUCT_ADVANCE = True
SUMMARY_FIELD = {"Department": "department", "Designation": "designation", "Pay Mode": "pay_mode"}


def execute(filters=None):
    filters = frappe._dict(filters or {})
    if filters.from_date and filters.to_date and getdate(filters.from_date) > getdate(filters.to_date):
        frappe.throw(_("From Date cannot be after To Date"))

    rows = get_rows(filters)
    if filters.summary and filters.summary != "None":
        return get_summary_columns(filters), get_summary(rows, filters)
    return get_columns(filters), add_total(rows)


# ---------------- Columns ----------------

def get_columns(filters):
    cols = [
        {"label": _("Sr.No"), "fieldname": "sr_no", "fieldtype": "Int", "width": 60},
        {"label": _("Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": _("CNIC"), "fieldname": "cnic", "fieldtype": "Data", "width": 130},
        {"label": _("Code"), "fieldname": "code", "fieldtype": "Data", "width": 80},
        {"label": _("Designation"), "fieldname": "designation", "fieldtype": "Data", "width": 180},
        {"label": _("DOA"), "fieldname": "doa", "fieldtype": "Date", "width": 100},
        {"label": _("G.Salary"), "fieldname": "gross_salary", "fieldtype": "Currency", "width": 110},
        {"label": _("L.Days"), "fieldname": "leave_days", "fieldtype": "Float", "width": 80},
        {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Advance"), "fieldname": "advance", "fieldtype": "Currency", "width": 100},
        {"label": _("Inc.Tax"), "fieldname": "income_tax", "fieldtype": "Currency", "width": 90},
        {"label": _("Paid Leave"), "fieldname": "paid_leave", "fieldtype": "Currency", "width": 120},
    ]
    if filters.show_cadre:
        cols.append({"label": _("Cadre"), "fieldname": "cadre", "fieldtype": "Data", "width": 110})
    if filters.bank_sheet:
        cols += [
            {"label": _("Pay Mode"), "fieldname": "pay_mode", "fieldtype": "Data", "width": 90},
            {"label": _("Bank"), "fieldname": "bank_name", "fieldtype": "Data", "width": 140},
            {"label": _("Account No"), "fieldname": "bank_ac_no", "fieldtype": "Data", "width": 160},
        ]
    cols.append({"label": _("Signature"), "fieldname": "signature", "fieldtype": "Data", "width": 110})
    return cols


def get_summary_columns(filters):
    return [
        {"label": _(filters.summary), "fieldname": "group", "fieldtype": "Data", "width": 240},
        {"label": _("Employees"), "fieldname": "employees", "fieldtype": "Int", "width": 100},
        {"label": _("L.Days"), "fieldname": "leave_days", "fieldtype": "Float", "width": 90},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 130},
        {"label": _("Advance"), "fieldname": "advance", "fieldtype": "Currency", "width": 120},
        {"label": _("Inc.Tax"), "fieldname": "income_tax", "fieldtype": "Currency", "width": 100},
        {"label": _("Paid Leave"), "fieldname": "paid_leave", "fieldtype": "Currency", "width": 130},
    ]


# ---------------- Data ----------------

def get_rows(filters):
    meta = frappe.get_meta("Leave Encashment")
    days_field = next((f for f in DAYS_FIELDS if meta.has_field(f)), None)

    enc_filters = {"docstatus": 1}
    if filters.from_date and filters.to_date:
        enc_filters["encashment_date"] = ["between", [filters.from_date, filters.to_date]]
    elif filters.from_date:
        enc_filters["encashment_date"] = [">=", filters.from_date]
    elif filters.to_date:
        enc_filters["encashment_date"] = ["<=", filters.to_date]

    fields = ["employee", "encashment_amount"]
    if days_field:
        fields.append(f"{days_field} as days")
    encashments = frappe.get_all("Leave Encashment", filters=enc_filters, fields=fields)
    if not encashments:
        return []

    employees = get_employees({e.employee for e in encashments}, filters)
    gross = get_gross_salaries(employees, filters)
    advances = get_advances(employees, filters) if DEDUCT_ADVANCE else {}

    # One line per employee (several encashments in the period are added up)
    per_emp = {}
    for e in encashments:
        if e.employee not in employees:
            continue
        acc = per_emp.setdefault(e.employee, frappe._dict(days=0.0, amount=0.0))
        acc.days += flt(e.get("days"))
        acc.amount += flt(e.encashment_amount)

    ordered = sorted(per_emp, key=lambda emp_id: str(employees[emp_id].get("employee_number") or emp_id))
    rows = []
    for i, emp_id in enumerate(ordered, 1):
        emp = employees[emp_id]
        enc = per_emp[emp_id]
        rate = enc.amount / enc.days if enc.days else 0
        advance = min(flt(advances.get(emp_id)), enc.amount)
        income_tax = 0.0
        rows.append(frappe._dict(
            sr_no=i,
            employee=emp_id,
            employee_name=emp.employee_name,
            cnic=emp.get("cnic") or "",
            code=emp.get("employee_number") or emp_id,
            designation=emp.get("designation"),
            doa=emp.get("date_of_joining"),
            gross_salary=round(flt(gross.get(emp_id))),
            leave_days=round(enc.days, 2),
            rate=round(rate, 2),
            amount=round(enc.amount),
            advance=round(advance),
            income_tax=income_tax,
            paid_leave=round(enc.amount - advance - income_tax),
            pay_mode=emp.get("salary_mode"),
            bank_name=emp.get("bank_name"),
            bank_ac_no=emp.get("bank_ac_no"),
            cadre=emp.get("grade"),
            department=emp.get("department"),
            signature="",
        ))
    return rows


def get_employees(ids, filters):
    meta = frappe.get_meta("Employee")
    wanted = ["employee_name", "employee_number", "designation", "date_of_joining", "department",
              "salary_mode", "bank_name", "bank_ac_no", "grade"]
    fields = ["name"] + [f for f in wanted if meta.has_field(f)]
    cnic_field = next((f for f in CNIC_FIELDS if meta.has_field(f)), None)
    if cnic_field:
        fields.append(f"{cnic_field} as cnic")

    emp_filters = {"name": ["in", list(ids)]}
    if filters.pay_mode and filters.pay_mode != "All":
        emp_filters["salary_mode"] = filters.pay_mode
    if filters.cadre:
        emp_filters["grade"] = filters.cadre
    return {e.name: e for e in frappe.get_all("Employee", filters=emp_filters, fields=fields)}


def get_gross_salaries(employees, filters):
    """Latest Salary Structure Assignment base on or before To Date."""
    if not employees:
        return {}
    rows = frappe.get_all(
        "Salary Structure Assignment",
        filters={"docstatus": 1, "employee": ["in", list(employees)], "from_date": ["<=", filters.to_date or today()]},
        fields=["employee", "base"],
        order_by="from_date desc",
    )
    out = {}
    for r in rows:
        out.setdefault(r.employee, flt(r.base))
    return out


def get_advances(employees, filters):
    """Outstanding Employee Advance per employee up to To Date."""
    if not employees or not frappe.db.exists("DocType", "Employee Advance"):
        return {}
    meta = frappe.get_meta("Employee Advance")
    returned = "IFNULL(return_amount, 0)" if meta.has_field("return_amount") else "0"
    rows = frappe.db.sql(
        f"""
        SELECT employee,
               SUM(IFNULL(paid_amount, 0) - IFNULL(claimed_amount, 0) - {returned}) AS pending
        FROM `tabEmployee Advance`
        WHERE docstatus = 1 AND employee IN %(emps)s AND posting_date <= %(to_date)s
        GROUP BY employee
        """,
        {"emps": tuple(employees), "to_date": filters.to_date or today()},
        as_dict=True,
    )
    return {r.employee: max(flt(r.pending), 0) for r in rows}


# ---------------- Totals and summary ----------------

def add_total(rows):
    if not rows:
        return rows
    total = frappe._dict(employee_name=_("Total"), is_total=1)
    for f in ("leave_days", "amount", "advance", "income_tax", "paid_leave"):
        total[f] = sum(flt(r[f]) for r in rows)
    return rows + [total]


def get_summary(rows, filters):
    key = SUMMARY_FIELD.get(filters.summary)
    groups = {}
    for r in rows:
        name = r.get(key) or _("Not Set")
        g = groups.setdefault(name, frappe._dict(group=name, employees=0, leave_days=0.0, amount=0.0,
                                                 advance=0.0, income_tax=0.0, paid_leave=0.0))
        g.employees += 1
        for f in ("leave_days", "amount", "advance", "income_tax", "paid_leave"):
            g[f] += flt(r[f])

    data = sorted(groups.values(), key=lambda g: str(g.group))
    if data:
        total = frappe._dict(group=_("Total"), is_total=1, employees=sum(g.employees for g in data))
        for f in ("leave_days", "amount", "advance", "income_tax", "paid_leave"):
            total[f] = sum(flt(g[f]) for g in data)
        data.append(total)
    return data