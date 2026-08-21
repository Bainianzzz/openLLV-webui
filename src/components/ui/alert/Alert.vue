<script setup lang="ts">
import { cn } from "../../../lib/utils";
const props = defineProps<{ class?: string }>();
</script>
<template>
  <div
    role="alert"
    :class="cn('relative w-full rounded-lg border p-4', props.class)"
  >
    <slot />
  </div>
</template>
