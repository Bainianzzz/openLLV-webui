<script setup lang="ts">
import PageHeader from "../components/shared/PageHeader.vue";
</script>

<template>
  <PageHeader eyebrow="Project" title="About openLLV" description="A focused local workspace for image enhancement, model training, and managed experiment tasks." />
  <section class="grid gap-5 md:grid-cols-2">
    <div class="rounded-2xl bg-slate-950 p-7 text-white"><p class="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-300">Architecture</p><h2 class="mt-5 text-xl font-semibold tracking-tight">FastAPI outside, workers inside.</h2><p class="mt-3 text-sm leading-6 text-slate-300">The browser submits work through a stable API while fixed local workers handle long-running openLLV operations.</p></div>
    <div class="rounded-2xl border border-slate-200 bg-white p-7"><p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Principles</p><ul class="mt-5 space-y-4 text-sm text-slate-600"><li>Managed artifacts instead of filesystem paths</li><li>Persistent task status from queue to result</li><li>Simple local deployment with no extra services</li></ul></div>
  </section>
</template>
