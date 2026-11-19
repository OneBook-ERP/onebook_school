"""Synthetic demo school: one command loads Sri Aanoor Vidyalaya (or any school company) for a demo.

    bench --site <site> execute onebook_school.demo.load --kwargs '{"logo_path": "/path/logo.png"}'

Refuses unless the site is in developer mode or has `campus_demo_site` set. Every record is found by its natural key
first, so a second run creates nothing new. People are generated from a seed: Tamil names, phone numbers that start
with 0 (never dialable), e-mails at aanoor.example.edu, no Aadhaar numbers.
"""

import time

import frappe
from frappe import _

from onebook_school.demo import academics, classes, extras, fees, people, school, staff

STEPS = ("school", "classes", "staff", "people", "fees", "academics", "extras")


def check_allowed():
	if not (frappe.conf.get("developer_mode") or frappe.conf.get("campus_demo_site")):
		frappe.throw(_("The demo data is for developer-mode or demo sites only."))


class Context:
	def __init__(self, seed, scale, company, logo_path):
		self.seed, self.scale, self.logo_path = seed, scale, logo_path
		self.company = company or school.COMPANY
		self.created = 0
		self.year = school.YEAR

	def made(self, n=1):
		self.created += n


def load(seed=2026, scale="full", company=None, logo_path=None, steps=None):
	check_allowed()
	started = time.monotonic()
	ctx = Context(int(seed), scale, company, logo_path)
	modules = {"school": school, "classes": classes, "staff": staff, "people": people, "fees": fees, "academics": academics, "extras": extras}
	for step in steps or STEPS:
		modules[step].load(ctx)
		frappe.db.commit()  # nosemgrep: each step is a checkpoint for a long demo load
	return {"created": ctx.created, "seconds": round(time.monotonic() - started, 1)}
