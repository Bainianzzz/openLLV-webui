<script setup lang="ts">
import { computed } from "vue";
import { RouterLink, useRoute } from "vue-router";
import PageHeader from "../components/shared/PageHeader.vue";

const route = useRoute();
const taskId = computed(() => String(route.params.id));
</script>

<template>
  <PageHeader eyebrow="Task detail" title="Task details" :description="`Task ${taskId} is ready for status and result data from the API.`">
    <template #actions><RouterLink to="/tasks" class="text-sm font-medium text-slate-500 hover:text-slate-950">Back to tasks</RouterLink></template>
  </PageHeader>
  <section class="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
    <div class="rounded-2xl border border-slate-200 bg-white p-6"><p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Timeline</p><div class="mt-8 flex items-center gap-4"><span class="size-3 rounded-full bg-slate-300"></span><div><p class="text-sm font-medium">Waiting for task data</p><p class="mt-1 text-xs text-slate-400">The live status timeline will be rendered here.</p></div></div></div>
    <div class="rounded-2xl border border-slate-200 bg-white p-6"><p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Task ID</p><p class="mt-4 break-all font-mono text-sm text-slate-700">{{ taskId }}</p><p class="mt-8 text-xs leading-5 text-slate-400">Results and managed artifacts will be linked here when the task completes.</p></div>
  </section>
</template>
