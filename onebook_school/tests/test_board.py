from frappe.tests import UnitTestCase

from onebook_school.onebook_school.page.school_today import school_today as board


class TestBoard(UnitTestCase):
	def test_each_role_lands_on_its_own_board(self):
		self.assertEqual(board.home_board({"School Accountant"}), "Fees Office")
		self.assertEqual(board.home_board({"Class Teacher", "Instructor"}), "Class Teacher")
		self.assertEqual(board.home_board({"School Principal", "Class Teacher"}), "Principal")
		self.assertIsNone(board.home_board({"Student"}))

	def test_a_role_sees_only_the_boards_its_workspaces_allow(self):
		self.assertEqual(board.boards_for({"School Office"}), ["School Office"])
		self.assertNotIn("Correspondent", board.boards_for({"School Principal"}))

	def test_classes_and_grades_read_in_school_order(self):
		rows = [{"label": lbl, "value": 1} for lbl in ["Std XI - Science", "UKG", "Std IX", "LKG", "Std II"]]
		self.assertEqual([r["label"] for r in board.sort_rows(rows)], ["LKG", "UKG", "Std II", "Std IX", "Std XI - Science"])
		grades = [{"label": g, "value": 1} for g in ["B2", "A1", "E", "C1"]]
		self.assertEqual([r["label"] for r in board.sort_rows(grades)], ["A1", "B2", "C1", "E"])
		other = [{"label": "UPI", "value": 2}, {"label": "Cash", "value": 1}]
		self.assertEqual(board.sort_rows(other), other)

	def test_shortcuts_open_the_view_they_name(self):
		new = board.shortcut_of({"label": "New Fee Receipt", "type": "DocType", "link_to": "Family Receipt", "doc_view": "New"})
		self.assertEqual(new["to"], "/desk/family-receipt/new")
		self.assertTrue(new["primary"])
		report = board.shortcut_of({"label": "UDISE", "type": "Report", "link_to": "UDISE Student Export"})
		self.assertEqual(report["to"], "/desk/query-report/UDISE Student Export")

	def test_card_links_carry_simple_filters_only(self):
		route = board.list_route("Instructor", [["Instructor", "status", "=", "Active", False], ["Instructor", "docstatus", "=", 1, False]])
		self.assertEqual(route, "/desk/instructor?status=Active")
