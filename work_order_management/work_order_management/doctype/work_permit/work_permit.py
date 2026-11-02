# Work Permit (Written Authorization) - same as the ATS work permit paper / HTML form.
from frappe.model.document import Document


class WorkPermit(Document):
    def validate(self):
        if self.valid_until_work_complete:
            self.valid_until = None
