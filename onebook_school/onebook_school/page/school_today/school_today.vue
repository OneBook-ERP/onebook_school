<script setup>
// School boards: `/desk/school-today/<board>`, one per school workspace. The user's day comes first (decisions,
// then the timetable), then the workspace's numbers in its own groups, then its charts. Every number, line and
// chart opens the records behind it. Data: one GET (`get_board`); cover reuses `school_day.cover`.
import { computed, onMounted, ref, watch } from "vue";
import { Badge, Button, Dialog, TabButtons, createResource, frappeRequest } from "frappe-ui";
import { BarChart, DonutChart, LineChart, NumberCard } from "frappe-ui/charts";
import { useHost } from "@framework/ui/island";

const props = defineProps({
	route: { type: Array, default: () => [] },
	query: { type: Object, default: () => ({}) },
});
const emit = defineEmits(["title", "actions"]);
const host = useHost();
const __ = (message) => globalThis.__?.(message) ?? message;

// frappe-ui posts with `window.csrf_token`; desk keeps it on `frappe.csrf_token`.
if (!window.csrf_token && window.frappe?.csrf_token) window.csrf_token = window.frappe.csrf_token;

const API = "onebook_school.onebook_school.page.school_today.school_today";
const COVER = "onebook_school.school_day.cover";

const boardSlug = computed(() => props.route?.[0] || undefined);
const board = createResource({
	url: `${API}.get_board`,
	method: "GET",
	makeParams: () => ({ board: boardSlug.value }),
	resourceFetcher: frappeRequest,
	auto: true,
});
watch(boardSlug, () => board.reload());

const data = computed(() => board.data);
const loading = computed(() => board.loading && !board.data);
const error = computed(() => board.error?.messages?.[0] || board.error?.message || null);

const go = (path) => path && host.navigate?.(path);
const text = (html) => String(html ?? "").replace(/<[^>]+>/g, "").trim();
const format = (value, df) => (host.format ? text(host.format(value, df)) : String(value ?? ""));
const money = (v) => format(v, { fieldtype: "Currency", options: "INR", precision: 0 });
const shown = (c) => {
	if (c.value == null) return null;
	if (c.fieldtype === "Currency") return money(c.value);
	if (c.fieldtype === "Percent") return `${Number(c.value).toFixed(1)}%`;
	if (c.fieldtype === "Data") return String(c.value);
	return Number(c.value).toLocaleString("en-IN", { maximumFractionDigits: 1 });
};

watch(data, (d) => {
	if (!d) return;
	emit("title", d.title);
	// land on the board's own sidebar: /desk/<board>/school-today/<board>
	const want = `/${d.board}/school-today/${d.board}`;
	if (!window.location.pathname.endsWith(want)) go(`/desk${want}`);
});

const tabs = computed(() => (data.value?.boards || []).map((b) => ({ label: __(b.title), value: b.slug })));
const activeTab = computed({
	get: () => data.value?.board,
	set: (slug) => slug !== data.value?.board && go(`/desk/${slug}/school-today/${slug}`),
});

// ---- the day ---------------------------------------------------------------------------------------------------
const sections = computed(() => data.value?.sections || []);
const wide = (s) => ["attention", "now_next", "call_list"].includes(s.key);
const tag = (it) => (["NOW", "NEXT", "done"].includes(it.sub) ? it.sub : null);
const tagTheme = { NOW: "amber", NEXT: "blue", done: "gray" };
const toneTitle = { alert: "text-ink-red-6", ok: "text-ink-green-6", info: "text-ink-blue-6" };

// ---- charts ----------------------------------------------------------------------------------------------------
const palette = ["var(--ink-blue-5)", "var(--ink-green-5)", "var(--ink-amber-5)", "var(--ink-red-4)", "var(--ink-violet-5)", "var(--ink-cyan-5)"];
const STATUS = { Present: "var(--ink-green-5)", Absent: "var(--ink-red-4)", "On Leave": "var(--ink-amber-5)", "Half Day": "var(--ink-blue-4)", "Work From Home": "var(--ink-cyan-5)" };
const charts = computed(() =>
	(data.value?.charts || []).map((c) => {
		const series = { value: { name: c.money ? __("Amount (₹)") : __("Count"), color: c.color || palette[0] } };
		const common = { title: __(c.title), data: c.rows, error: null };
		if (c.kind === "donut") {
			const colors = Object.fromEntries(c.rows.map((r, i) => [r.label, STATUS[r.label] || palette[i % palette.length]]));
			return { ...c, is: DonutChart, span: "", props: { ...common, category: "label", value: "value", colors, centerLabel: c.money ? __("₹") : __("Total") } };
		}
		const is = c.kind === "line" ? LineChart : BarChart;
		const span = c.time || c.rows.length > 8 ? "lg:col-span-2 xl:col-span-3" : "";
		return { ...c, is, span, props: { ...common, x: "label", y: "value", seriesConfig: series, showDataLabels: !c.time && c.rows.length <= 16 } };
	})
);

// ---- cover a period --------------------------------------------------------------------------------------------
const coverOpen = ref(false);
const coverFor = ref(null);
const suggestions = createResource({ url: `${COVER}.suggest_cover`, method: "GET", resourceFetcher: frappeRequest });
const assigning = ref(null);

function act(action) {
	if (action.kind === "route") return go(action.route);
	if (action.kind === "cover") {
		coverFor.value = action;
		coverOpen.value = true;
		suggestions.submit(action.args);
	}
}

async function assign(teacher) {
	assigning.value = teacher.instructor;
	try {
		await frappeRequest({ url: `${COVER}.assign`, params: { ...coverFor.value.args, cover_instructor: teacher.instructor } });
		window.frappe?.show_alert?.({ message: `${teacher.instructor_name} ${__("covers")} ${coverFor.value.args.student_group}`, indicator: "green" });
		coverOpen.value = false;
		board.reload();
	} catch (e) {
		window.frappe?.msgprint?.(e.messages?.[0] || e.message);
	} finally {
		assigning.value = null;
	}
}

const coverTitle = computed(() => {
	const a = coverFor.value;
	return a ? `${__("Cover")} ${a.args.student_group} · ${a.period_label || "P" + a.args.period_no}` : "";
});

const dateLabel = computed(() => (data.value ? `${data.value.weekday}, ${format(data.value.date, { fieldtype: "Date" })}` : ""));
const card = "flex min-w-0 flex-col rounded-xl border border-outline-gray-1 bg-surface-elevation-2";

onMounted(() => {
	emit("title", __("Today"));
	emit("actions", [{ label: __("Refresh"), onClick: () => board.reload() }]);
});
</script>

<template>
	<div class="flex h-full flex-col gap-6 overflow-y-auto p-5">
		<!-- who, when, which board -->
		<header class="flex flex-wrap items-end justify-between gap-4">
			<div class="min-w-0">
				<p class="text-p-sm font-medium uppercase tracking-wide text-ink-gray-5">{{ dateLabel }}</p>
				<h2 class="text-2xl font-semibold text-ink-gray-9">{{ data?.greeting || __("Today") }}</h2>
				<p v-if="data?.intro" class="mt-1 text-p-base text-ink-gray-6">{{ data.intro }}</p>
			</div>
			<div class="flex flex-wrap items-center gap-2">
				<TabButtons v-if="tabs.length > 1" v-model="activeTab" :options="tabs" />
				<Button :label="__('Refresh')" variant="subtle" icon-left="lucide-refresh-cw" :loading="board.loading" @click="board.reload()" />
			</div>
		</header>

		<div v-if="error" :class="[card, 'p-6 text-base text-ink-red-6']">{{ error }}</div>

		<!-- quick actions -->
		<div v-if="data?.shortcuts?.length" class="flex flex-wrap gap-2">
			<Button
				v-for="s in data.shortcuts"
				:key="s.label"
				:label="__(s.label)"
				:variant="s.primary ? 'solid' : 'outline'"
				@click="go(s.to)"
			/>
		</div>

		<!-- the day: decisions first -->
		<div v-if="sections.length" class="grid grid-cols-1 gap-4 lg:grid-cols-2">
			<section v-for="s in sections" :key="s.key" :class="[card, wide(s) ? 'lg:col-span-2' : '', 'overflow-hidden']">
				<div class="flex items-center justify-between border-b border-outline-gray-1 px-4 py-2.5">
					<h3 :class="['text-sm font-semibold uppercase tracking-wide', toneTitle[s.tone] || 'text-ink-gray-7']">{{ s.title }}</h3>
					<Badge :label="s.items.length" variant="subtle" :theme="s.tone === 'alert' ? 'red' : 'gray'" />
				</div>
				<div
					v-for="(it, i) in s.items"
					:key="i"
					:class="[
						'flex items-center gap-3 border-b border-outline-gray-1 px-4 py-2.5 last:border-b-0',
						it.sub === 'NOW' ? 'bg-surface-amber-1' : '',
						it.sub === 'done' ? 'opacity-50' : '',
					]"
				>
					<div v-if="s.key === 'now_next'" class="w-14 shrink-0">
						<Badge v-if="tag(it)" :label="tag(it)" :theme="tagTheme[tag(it)]" variant="subtle" size="sm" />
					</div>
					<div class="min-w-0 flex-1">
						<div :class="['text-base text-ink-gray-8', it.tone === 'alert' ? 'font-medium' : '']">{{ it.text }}</div>
						<div v-if="it.sub && !tag(it)" class="mt-0.5 text-p-sm text-ink-gray-5">{{ it.sub }}</div>
					</div>
					<Button
						v-if="it.action"
						:label="it.action.label"
						size="sm"
						:variant="it.action.kind === 'cover' ? 'solid' : 'subtle'"
						@click="act(it.action)"
					/>
				</div>
			</section>
		</div>

		<!-- the workspace's numbers, in its own groups -->
		<div v-if="loading" class="grid grid-cols-2 gap-4 md:grid-cols-4">
			<NumberCard v-for="n in 4" :key="n" title="" :value="null" loading />
		</div>
		<section v-for="g in data?.groups || []" :key="g.title" class="flex flex-col gap-2">
			<h3 v-if="g.title" class="text-sm font-semibold uppercase tracking-wide text-ink-gray-6">{{ __(g.title) }}</h3>
			<div class="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4">
				<NumberCard
					v-for="c in g.cards"
					:key="c.title"
					:title="__(c.title)"
					:value="shown(c)"
					:color="c.alert && c.value ? 'var(--ink-red-6)' : undefined"
					:class="c.to ? 'cursor-pointer transition hover:shadow-md' : ''"
					@click="go(c.to)"
				/>
			</div>
		</section>

		<!-- the workspace's charts -->
		<div v-if="charts.length" class="flex flex-col gap-2">
			<h3 class="text-sm font-semibold uppercase tracking-wide text-ink-gray-6">{{ __("Trends") }}</h3>
			<div class="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3">
				<section v-for="c in charts" :key="c.title" :class="[card, c.span, 'h-80 px-4 py-3']">
					<component :is="c.is" v-bind="c.props" :loading="board.loading && !data" />
				</section>
			</div>
		</div>

		<Dialog v-model:open="coverOpen" :title="coverTitle" size="md">
			<template #default>
				<p class="mb-3 text-p-sm text-ink-gray-6">{{ __("Free in this period. Same subject first, then the lightest day.") }}</p>
				<div v-if="suggestions.loading" class="py-6 text-center text-ink-gray-5">{{ __("Finding free teachers…") }}</div>
				<div v-else-if="!(suggestions.data || []).length" class="py-6 text-center text-ink-gray-5">{{ __("No teacher is free in this period.") }}</div>
				<div v-else class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-1">
					<div v-for="(t, i) in suggestions.data" :key="t.instructor" class="flex items-center gap-3 px-3 py-2">
						<div class="min-w-0 flex-1">
							<div class="text-base font-medium text-ink-gray-8">{{ t.instructor_name }}</div>
							<div class="text-p-sm text-ink-gray-5">
								{{ t.load_today }} {{ t.load_today === 1 ? __("period") : __("periods") }} {{ __("today") }}
							</div>
						</div>
						<Badge v-if="t.same_subject" :label="__('Same subject')" theme="green" variant="subtle" size="sm" />
						<Button
							:label="__('Assign')"
							size="sm"
							:variant="i === 0 ? 'solid' : 'subtle'"
							:loading="assigning === t.instructor"
							@click="assign(t)"
						/>
					</div>
				</div>
			</template>
		</Dialog>
	</div>
</template>
