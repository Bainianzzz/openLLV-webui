<script setup lang="ts">
import { RouterLink } from "vue-router";
import PageHeader from "../components/shared/PageHeader.vue";
</script>

<template>
  <PageHeader eyebrow="Activity" title="Tasks" description="Every enhancement, training, and dataset download is tracked here from queue to completion." />
  <section class="overflow-hidden rounded-2xl border border-slate-200 bg-white">
    <div class="flex items-center justify-between border-b border-slate-100 px-6 py-5"><h2 class="font-semibold">Recent activity</h2><span class="text-xs text-slate-400">All task types</span></div>
    <div class="flex min-h-64 flex-col items-center justify-center px-6 text-center"><p class="text-sm font-medium text-slate-700">No tasks to show</p><p class="mt-2 text-sm text-slate-500">Submitted work will appear in this activity log.</p><RouterLink to="/enhance" class="mt-5 text-sm font-semibold text-indigo-600 hover:text-indigo-500">Start an enhancement</RouterLink></div>
  </section>
</template>
