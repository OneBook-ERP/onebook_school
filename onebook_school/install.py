"""Install and migrate hooks for OneBook School."""


def after_install():
	from onebook_school.setup.custom_fields import create_all

	create_all()


def after_migrate():
	from onebook_school.setup.custom_fields import create_all
	from onebook_school.setup.desk import build

	create_all()
	build()
