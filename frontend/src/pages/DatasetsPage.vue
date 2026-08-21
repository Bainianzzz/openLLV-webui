<script setup lang="ts">
import PageHeader from "../components/shared/PageHeader.vue";
</script>

<template>
  <PageHeader eyebrow="Library" title="Datasets" description="Managed datasets are the shared source of truth for training runs and downloads.">
    <template #actions><button type="button" class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700">Add dataset</button></template>
  </PageHeader>
  <section class="rounded-2xl border border-slate-200 bg-white">
    <div class="flex items-center justify-between border-b border-slate-100 px-6 py-5"><div><h2 class="font-semibold">Your datasets</h2><p class="mt-1 text-xs text-slate-400">0 available datasets</p></div><span class="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-500">Managed storage</span></div>
    <div class="flex min-h-64 flex-col items-center justify-center px-6 text-center"><p class="text-sm font-medium text-slate-700">No datasets yet</p><p class="mt-2 max-w-sm text-sm leading-6 text-slate-500">Download or add a dataset to make it available for future training runs.</p></div>
  </section>
</template>
