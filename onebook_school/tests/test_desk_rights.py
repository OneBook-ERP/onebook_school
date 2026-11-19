import frappe
from frappe.tests.utils import FrappeTestCase

from onebook_school.setup.desk import grant


class TestDeskRights(FrappeTestCase):
	def test_grant_creates_missing_rights(self):
		role = "OBS Test Rights Role"
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)
		frappe.db.delete("Custom DocPerm", {"parent": "Report Card", "role": role})
		grant("Report Card", role, ("read", "report"))
		self.assertEqual(frappe.db.get_value("Custom DocPerm", {"parent": "Report Card", "role": role, "permlevel": 0}, "read"), 1)

	def test_grant_does_not_undo_an_admins_revocation(self):
		role = "OBS Test Rights Role"
		grant("Report Card", role, ("read", "report"))
		frappe.db.set_value("Custom DocPerm", {"parent": "Report Card", "role": role, "permlevel": 0}, "read", 0)
		grant("Report Card", role, ("read", "report"))
		self.assertEqual(frappe.db.get_value("Custom DocPerm", {"parent": "Report Card", "role": role, "permlevel": 0}, "read"), 0)
