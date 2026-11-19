app_name = "onebook_school"
app_title = "OneBook School"
app_publisher = "OneBook"
app_description = "K-12 school layer on OneBook Campus for Indian schools"
app_email = "tools.zenpivot@gmail.com"
app_license = "gpl-3.0"

# Apps
# ------------------

required_apps = ["campus"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "onebook_school",
# 		"logo": "/assets/onebook_school/logo.png",
# 		"title": "OneBook School",
# 		"route": "/onebook_school",
# 		"has_permission": "onebook_school.api.permission.has_app_permission",
# 	}
# ]

# The dock, the rail down the left of the desk, is a document rather than a hook. Author it in
# Manage Dock on a developer-mode site and press Export to App, and it is written to
# `onebook_school/dock/onebook_school/onebook_school.json` for git to carry. An app that ships none has no
# rail: its sidebar gets a switcher in the header instead.
#
# A companion app, one that extends a host app rather than standing on its own, says so with
# `mount_on` on that same record, and its entries are appended to the host's rail. Mounting keeps
# the companion off the apps screen, so it takes precedence over any add_to_apps_screen above.

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/onebook_school/css/onebook_school.css"
# app_include_js = "/assets/onebook_school/js/onebook_school.js"

# include js, css files in header of web template
# web_include_css = "/assets/onebook_school/css/onebook_school.css"
# web_include_js = "/assets/onebook_school/js/onebook_school.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "onebook_school/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_kanban_js = {"doctype" : "public/js/doctype_kanban.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "onebook_school/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "onebook_school.utils.jinja_methods",
# 	"filters": "onebook_school.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "onebook_school.install.before_install"
# after_install = "onebook_school.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "onebook_school.uninstall.before_uninstall"
# after_uninstall = "onebook_school.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "onebook_school.utils.before_app_install"
# after_app_install = "onebook_school.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "onebook_school.utils.before_app_uninstall"
# after_app_uninstall = "onebook_school.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "onebook_school.build.after_build"

# To hook into the build process of other apps
# The list of apps being built is passed as an argument

# after_app_build = "onebook_school.build.after_app_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "onebook_school.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["onebook_school.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"onebook_school.tasks.all"
# 	],
# 	"daily": [
# 		"onebook_school.tasks.daily"
# 	],
# 	"hourly": [
# 		"onebook_school.tasks.hourly"
# 	],
# 	"weekly": [
# 		"onebook_school.tasks.weekly"
# 	],
# 	"monthly": [
# 		"onebook_school.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "onebook_school.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "onebook_school.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "onebook_school.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "onebook_school.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["onebook_school.utils.before_request"]
# after_request = ["onebook_school.utils.after_request"]

# Job Events
# ----------
# before_job = ["onebook_school.utils.before_job"]
# after_job = ["onebook_school.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"onebook_school.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


after_install = "onebook_school.install.after_install"
after_migrate = "onebook_school.install.after_migrate"

doc_events = {
	"Fee Structure": {"validate": "onebook_school.fees.fee_cap.check_fee_structure"},
	"Sales Invoice": {"before_validate": "onebook_school.fees.sibling.apply_sibling_discount"},
}
