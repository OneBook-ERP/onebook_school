"""The "Today" block: first thing on every school workspace. It asks `get_today` for the user's day and renders it as
short, actionable lines; "Assign cover" opens a picker of free teachers and assigns in one click."""

import frappe

NAME = "Today"

HTML = '<div class="obs-today"><div class="obs-today-loading">Loading your day…</div></div>'

STYLE = """
.obs-today { font-family: inherit; color: var(--text-color); }
.obs-today .hello { display: flex; justify-content: space-between; align-items: baseline; margin: 2px 0 14px; }
.obs-today .hello h3 { font-size: 20px; font-weight: 700; margin: 0; }
.obs-today .hello span { color: var(--text-muted); font-size: 13px; }
.obs-today .sec { border: 1px solid var(--border-color); border-radius: 12px; margin-bottom: 14px; overflow: hidden; background: var(--card-bg); }
.obs-today .sec h4 { margin: 0; padding: 10px 16px; font-size: 13px; font-weight: 700; letter-spacing: .3px; text-transform: uppercase; border-bottom: 1px solid var(--border-color); }
.obs-today .sec.alert h4 { color: #a3197b; background: #fbf0f7; }
.obs-today .sec.ok h4 { color: #2e7d32; background: #f1f8f2; }
.obs-today .sec.info h4 { color: #1565c0; background: #f2f6fc; }
.obs-today .row { display: flex; align-items: center; gap: 12px; padding: 10px 16px; border-bottom: 1px solid var(--border-color); }
.obs-today .row:last-child { border-bottom: 0; }
.obs-today .row.now { background: #fff8e1; }
.obs-today .row.alert .txt { font-weight: 600; }
.obs-today .tag { min-width: 44px; font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; }
.obs-today .tag.NOW { color: #e65100; } .obs-today .tag.NEXT { color: #1565c0; }
.obs-today .txt { flex: 1; font-size: 14px; }
.obs-today .sub { color: var(--text-muted); font-size: 12px; margin-top: 2px; font-weight: 400; }
.obs-today .btn { white-space: nowrap; }
.obs-today .empty { padding: 14px 16px; color: var(--text-muted); }
"""

SCRIPT = r"""
const box = root_element.querySelector('.obs-today');
const esc = (s) => frappe.utils.escape_html(s == null ? '' : String(s));
const render = (d) => {
	let html = `<div class="hello"><h3>${esc(d.greeting)}</h3><span>${esc(d.weekday)}, ${esc(frappe.datetime.str_to_user(d.date))}</span></div>`;
	if (!d.sections.length) html += `<div class="sec info"><div class="empty">${__('Nothing needs you right now.')}</div></div>`;
	d.sections.forEach((s, si) => {
		html += `<div class="sec ${esc(s.tone)}"><h4>${esc(s.title)}</h4>`;
		s.items.forEach((it, ii) => {
			const isTag = ['NOW', 'NEXT', 'done'].includes(it.sub);
			const tag = s.key === 'now_next' ? `<div class="tag ${esc(it.sub || '')}">${isTag ? esc(it.sub) : ''}</div>` : '';
			const sub = it.sub && !isTag ? `<div class="sub">${esc(it.sub)}</div>` : '';
			const btn = it.action ? `<button class="btn btn-xs ${it.action.kind === 'cover' ? 'btn-primary' : 'btn-default'}" data-s="${si}" data-i="${ii}">${esc(it.action.label)}</button>` : '';
			html += `<div class="row ${esc(it.tone || '')}">${tag}<div class="txt">${esc(it.text)}${sub}</div>${btn}</div>`;
		});
		html += `</div>`;
	});
	box.innerHTML = html;
	box.querySelectorAll('button[data-s]').forEach((b) => b.addEventListener('click', () => act(d.sections[b.dataset.s].items[b.dataset.i].action)));
};
const load = () => frappe.call('onebook_school.school_day.today.get_today').then((r) => render(r.message));
const act = (a) => {
	if (a.kind === 'route') return frappe.set_route(a.route.replace(/^\/desk\//, '').split('?')[0].split('/'), Object.fromEntries(new URLSearchParams(a.route.split('?')[1] || '')));
	if (a.kind === 'cover') {
		frappe.call('onebook_school.school_day.cover.suggest_cover', a.args).then((r) => {
			const options = (r.message || []).map((t) => ({ label: `${t.instructor_name}${t.same_subject ? ' · same subject' : ''} · ${t.load_today} ${t.load_today === 1 ? 'period' : 'periods'} today`, value: t.instructor }));
			if (!options.length) return frappe.msgprint(__('No teacher is free in this period.'));
			const dlg = new frappe.ui.Dialog({
				title: __('Cover {0}, {1}', [a.args.student_group, a.period_label || a.args.period_no]),
				fields: [{ fieldname: 'teacher', fieldtype: 'Select', label: __('Free teachers (best first)'), options, default: options[0].value, reqd: 1 }],
				primary_action_label: __('Assign'),
				primary_action: (v) => frappe.call('onebook_school.school_day.cover.assign', Object.assign({ cover_instructor: v.teacher }, a.args)).then(() => { dlg.hide(); frappe.show_alert({ message: __('Cover assigned'), indicator: 'green' }); load(); }),
			});
			dlg.show();
		});
	}
};
load();
"""


def build():
	values = {"html": HTML, "script": SCRIPT, "style": STYLE, "private": 0}
	if frappe.db.exists("Custom HTML Block", NAME):
		doc = frappe.get_doc("Custom HTML Block", NAME)
		doc.update(values)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.new_doc("Custom HTML Block")
		doc.update(values)
		doc.insert(ignore_permissions=True, set_name=NAME)
	return NAME
