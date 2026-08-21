<script setup lang="ts">
import { ToggleGroupItem } from "reka-ui";
import { cn } from "../../../lib/utils";

const props = defineProps<{ class?: string; value: string }>();
</script>

<template>
  <ToggleGroupItem
    v-bind="$attrs"
    :value="props.value"
    :class="
      cn(
        'inline-flex items-center justify-center rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-muted focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 data-[state=on]:bg-background data-[state=on]:text-foreground data-[state=on]:shadow-sm',
        props.class,
      )
    "
  >
    <slot />
  </ToggleGroupItem>
</template>
