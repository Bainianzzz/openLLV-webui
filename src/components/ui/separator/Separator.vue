<script setup lang="ts">
import { cn } from "../../../lib/utils";
const props = withDefaults(
  defineProps<{ class?: string; orientation?: "horizontal" | "vertical" }>(),
  { orientation: "horizontal" },
);
</script>
<template>
  <div
    role="separator"
    :class="
      cn(
        'shrink-0 bg-border',
        orientation === 'horizontal' ? 'h-px w-full' : 'h-full w-px',
        props.class,
      )
    "
  />
</template>
