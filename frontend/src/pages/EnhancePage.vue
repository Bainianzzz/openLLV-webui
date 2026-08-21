<script setup lang="ts">
import PageHeader from "../components/shared/PageHeader.vue";
</script>

<template>
  <PageHeader eyebrow="Workspace" title="Enhance images" description="Prepare an image, choose an openLLV method, and send an enhancement task to the local worker.">
    <template #actions><span class="rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700">Ready to run</span></template>
  </PageHeader>

  <section class="grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(280px,0.75fr)]">
    <div class="rounded-2xl border border-dashed border-slate-300 bg-white p-8 sm:p-12">
      <div class="flex min-h-72 flex-col items-center justify-center text-center">
        <div class="mb-5 flex size-14 items-center justify-center rounded-2xl bg-indigo-50 text-xl font-semibold text-indigo-600">+</div>
        <h2 class="text-lg font-semibold">Drop an image here</h2>
        <p class="mt-2 max-w-sm text-sm leading-6 text-slate-500">Upload a source image to start composing an enhancement task. File handling will connect here in the next stage.</p>
        <button type="button" class="mt-6 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800">Choose image</button>
      </div>
    </div>
    <div class="rounded-2xl border border-slate-200 bg-white p-6">
      <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Enhancement setup</p>
      <div class="mt-6 space-y-5 text-sm">
        <div><p class="text-slate-400">Method</p><p class="mt-1 font-medium">Select an available method</p></div>
        <div><p class="text-slate-400">Output</p><p class="mt-1 font-medium">Managed output artifact</p></div>
        <div><p class="text-slate-400">Device</p><p class="mt-1 font-medium">Auto-detected by the service</p></div>
      </div>
      <div class="mt-8 rounded-xl bg-slate-50 p-4 text-xs leading-5 text-slate-500">Your task will appear in Tasks after it is submitted.</div>
    </div>
  </section>
</template>
