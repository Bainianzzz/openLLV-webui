<script setup lang="ts">
defineProps<{
  eyebrow?: string;
  title: string;
  description: string;
}>();
</script>

<template>
  <header
    class="mb-10 flex flex-col gap-5 border-b border-slate-200 pb-8 sm:flex-row sm:items-end sm:justify-between"
  >
    <div>
      <p
        v-if="eyebrow"
        class="mb-3 text-3xs font-semibold uppercase tracking-eyebrow text-indigo-600"
      >
        {{ eyebrow }}
      </p>
      <h1
        class="text-3xl font-semibold tracking-display text-slate-950 sm:text-4xl"
      >
        {{ title }}
      </h1>
      <p class="mt-3 max-w-2xl text-sm leading-6 text-slate-500">
        {{ description }}
      </p>
    </div>
    <div v-if="$slots.actions" class="max-w-full shrink-0">
      <slot name="actions" />
    </div>
  </header>
</template>
