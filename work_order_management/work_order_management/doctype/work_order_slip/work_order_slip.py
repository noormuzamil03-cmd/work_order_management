import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class WorkOrderSlip(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        amended_from: DF.Link | None
        asset: DF.Data | None
        assigned_department: DF.Link
        date: DF.Date
        defect_description: DF.SmallText
        machine_name: DF.Data | None
        priority: DF.Literal["Urgent", "Normal", "Emergency"]
        reference_no: DF.Data | None
        requested_by: DF.Link | None
        requested_by_card: DF.Data | None
        requested_by_employee: DF.Link | None
        requested_by_name: DF.Data | None
        requesting_department: DF.Link
        shift: DF.Link | None
        time: DF.Time | None
        work_order_completion: DF.Link | None
        work_status: DF.Literal["Not Started", "In Progress", "Pending Approval", "Rework Required", "Completed"]
    # end: auto-generated types

    def before_insert(self):
        # Date and time are always the server time of the first save.
        # An amended slip keeps the original date and time.
        if self.amended_from:
            return
        current = now_datetime()
        self.date = current.strftime("%Y-%m-%d")
        self.time = current.strftime("%H:%M:%S")
        self.set_requester()

    def set_requester(self):
        """Requested By = the logged-in user and his Employee record."""
        user = frappe.session.user
        self.requested_by = user
        self.requested_by_employee = frappe.db.get_value(
            "Employee", {"user_id": user, "status": "Active"}, "name"
        )
        if not self.requested_by_employee:
            # No Employee record (e.g. Administrator): show the user's full name
            self.requested_by_name = frappe.db.get_value("User", user, "full_name") or user

    def on_submit(self):
        self.db_set("work_status", "Not Started")

    def on_cancel(self):
        active = frappe.db.get_value(
            "Work Order Completion", {"work_order_slip": self.name, "docstatus": ["!=", 2]}
        )
        if active:
            frappe.throw(_("Work Order Completion {0} exists for this slip. Please cancel it first.")
                         .format(active))