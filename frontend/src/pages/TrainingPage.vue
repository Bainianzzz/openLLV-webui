<script setup lang="ts">
import PageHeader from "../components/shared/PageHeader.vue";
</script>

<template>
  <PageHeader eyebrow="Workspace" title="Train a model" description="Configure a training run from a managed dataset and follow its progress from the task history.">
    <template #actions><button type="button" class="rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white">New training run</button></template>
  </PageHeader>
  <section class="grid gap-5 md:grid-cols-3">
    <div v-for="item in ['Model and method', 'Dataset', 'Run settings']" :key="item" class="min-h-48 rounded-2xl border border-slate-200 bg-white p-6">
      <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">{{ item }}</p>
      <p class="mt-6 text-sm text-slate-400">Configuration options will be available here.</p>
    </div>
  </section>
</template>
