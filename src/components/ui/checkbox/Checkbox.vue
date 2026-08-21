<script setup lang="ts">
import { CheckboxIndicator, CheckboxRoot } from "reka-ui";
import { Check } from "@lucide/vue";
import { cn } from "../../../lib/utils";

const props = defineProps<{ class?: string }>();
</script>

<template>
  <CheckboxRoot
    v-bind="$attrs"
    :class="
      cn(
        'peer size-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground',
        props.class,
      )
    "
  >
    <CheckboxIndicator class="flex items-center justify-center text-current">
      <Check />
    </CheckboxIndicator>
  </CheckboxRoot>
</template>
