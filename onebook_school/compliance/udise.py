"""UDISE+ student data (SDMS) prepared from the school's own records, with what is missing named before entry.
UDISE+ offers schools no API, so the export is the hand-off: one row per student in the portal's field order."""

REQUIRED = (
	("date_of_birth", "Date of Birth"),
	("gender", "Gender"),
	("social_category", "Social Category"),
	("emis_id", "EMIS ID"),
	("pen", "PEN"),
	("apaar_consent", "APAAR Consent"),
)


def student_issues(row):
	issues = [label for key, label in REQUIRED if not row.get(key)]
	if not (row.get("father_name") or row.get("mother_name")):
		issues.insert(2, "Father's or Mother's Name")
	return issues
