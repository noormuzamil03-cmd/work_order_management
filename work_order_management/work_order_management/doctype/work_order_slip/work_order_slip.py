import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class WorkOrderSlip(Document):
    def before_insert(self):
        # Date and time are always the server time of the first save.
        # An amended slip keeps the original date and time.
        if self.amended_from:
            return
        current = now_datetime()
        self.date = current.strftime("%Y-%m-%d")
        self.time = current.strftime("%H:%M:%S")

    def on_submit(self):
        self.db_set("work_status", "Not Started")

    def on_cancel(self):
        active = frappe.db.get_value(
            "Work Order Completion", {"work_order_slip": self.name, "docstatus": ["!=", 2]}
        )
        if active:
            frappe.throw(_("Work Order Completion {0} exists for this slip. Please cancel it first.")
                         .format(active))