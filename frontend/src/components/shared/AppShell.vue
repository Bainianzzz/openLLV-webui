<script setup lang="ts">
import { RouterLink } from "vue-router";

const primaryNavigation = [
  { label: "Enhance", to: "/enhance", description: "Improve images with openLLV" },
  { label: "Training", to: "/training", description: "Create and monitor runs" },
  { label: "Datasets", to: "/datasets", description: "Manage training data" },
  { label: "Tasks", to: "/tasks", description: "View recent work" },
];
</script>

<template>
  <div class="min-h-dvh bg-slate-50 text-slate-950">
    <aside class="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-slate-200 bg-white lg:flex lg:flex-col">
      <div class="flex h-20 items-center gap-3 border-b border-slate-100 px-7">
        <div class="flex size-9 items-center justify-center rounded-xl bg-slate-950 text-sm font-bold text-white">L</div>
        <div>
          <p class="text-sm font-semibold tracking-tight">openLLV</p>
          <p class="text-xs text-slate-400">image intelligence</p>
        </div>
      </div>

      <nav class="flex-1 space-y-1 px-3 py-6" aria-label="Main navigation">
        <p class="px-3 pb-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">Workspace</p>
        <RouterLink
          v-for="item in primaryNavigation"
          :key="item.to"
          :to="item.to"
          class="group flex items-center gap-3 rounded-xl px-3 py-3 text-sm text-slate-500 transition hover:bg-slate-50 hover:text-slate-950"
          active-class="bg-slate-100 font-semibold text-slate-950"
        >
          <span class="flex size-7 items-center justify-center rounded-lg bg-slate-100 text-[11px] font-bold text-slate-500 group-[.router-link-active]:bg-white group-[.router-link-active]:text-slate-950">{{ item.label.slice(0, 1) }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="space-y-1 border-t border-slate-100 p-3">
        <RouterLink to="/about" class="flex items-center gap-3 rounded-xl px-3 py-3 text-sm text-slate-500 transition hover:bg-slate-50 hover:text-slate-950" active-class="bg-slate-100 font-semibold text-slate-950">
          <span class="flex size-7 items-center justify-center rounded-lg bg-slate-100 text-xs font-bold">?</span>
          <span>About openLLV</span>
        </RouterLink>
        <div class="flex items-center gap-3 px-3 py-4 text-xs text-slate-400">
          <span class="size-2 rounded-full bg-emerald-400"></span>
          <span>Local workspace ready</span>
        </div>
      </div>
    </aside>

    <div class="lg:pl-64">
      <header class="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-5 lg:hidden">
        <RouterLink to="/enhance" class="flex items-center gap-2 text-sm font-semibold">
          <span class="flex size-8 items-center justify-center rounded-lg bg-slate-950 text-xs font-bold text-white">L</span>
          openLLV
        </RouterLink>
        <RouterLink to="/tasks" class="text-xs font-medium text-slate-500">Tasks</RouterLink>
      </header>

      <main class="mx-auto min-h-[calc(100dvh-4rem)] max-w-7xl px-5 py-8 sm:px-8 lg:px-12 lg:py-12">
        <slot />
      </main>
    </div>
  </div>
</template>
