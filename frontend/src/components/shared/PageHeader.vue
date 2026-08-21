<script setup lang="ts">
defineProps<{
  eyebrow?: string;
  title: string;
  description: string;
}>();
</script>

<template>
  <header class="mb-10 flex flex-col gap-5 border-b border-slate-200 pb-8 sm:flex-row sm:items-end sm:justify-between">
    <div>
      <p v-if="eyebrow" class="mb-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-indigo-600">{{ eyebrow }}</p>
      <h1 class="text-3xl font-semibold tracking-[-0.03em] text-slate-950 sm:text-4xl">{{ title }}</h1>
      <p class="mt-3 max-w-2xl text-sm leading-6 text-slate-500">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="shrink-0">
      <slot name="actions" />
    </div>
  </header>
</template>
