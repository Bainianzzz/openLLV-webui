<script setup lang="ts">
import { ToggleGroupRoot } from "reka-ui";
import { cn } from "../../../lib/utils";

const props = defineProps<{ class?: string }>();
</script>

<template>
  <ToggleGroupRoot
    v-bind="$attrs"
    :class="cn('flex items-center justify-center gap-1', props.class)"
  >
    <slot />
  </ToggleGroupRoot>
</template>
