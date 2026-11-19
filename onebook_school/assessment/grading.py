"""Tamil Nadu term grading: percentage to grade letter (absent shows AB)."""

SCALE = ((91, "A1"), (81, "A2"), (71, "B1"), (61, "B2"), (51, "C1"), (41, "C2"), (35, "D"))
ABSENT = "AB"


def grade_for(percent):
	for floor, grade in SCALE:
		if percent >= floor:
			return grade
	return "E"
