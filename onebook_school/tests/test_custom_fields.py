import frappe
from frappe.tests.utils import FrappeTestCase

STUDENT_FIELDS = {
	"obs_admission_no": "Data",
	"obs_emis_id": "Data",
	"obs_pen": "Data",
	"obs_apaar_id": "Data",
	"obs_apaar_consent": "Select",
	"obs_mother_tongue": "Data",
	"obs_social_category": "Select",
	"obs_religion": "Select",
	"obs_rte": "Check",
	"obs_cwsn": "Check",
}


class TestCustomFields(FrappeTestCase):
	def test_student_fields_exist(self):
		meta = frappe.get_meta("Student")
		for fieldname, fieldtype in STUDENT_FIELDS.items():
			field = meta.get_field(fieldname)
			self.assertIsNotNone(field, fieldname)
			self.assertEqual(field.fieldtype, fieldtype, fieldname)

	def test_class_teacher_on_student_group(self):
		field = frappe.get_meta("Student Group").get_field("obs_class_teacher")
		self.assertIsNotNone(field)
		self.assertEqual(field.options, "Instructor")
