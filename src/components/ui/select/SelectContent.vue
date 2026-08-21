<script setup lang="ts">
import { SelectContent, SelectPortal, SelectViewport } from "reka-ui";
import { cn } from "../../../lib/utils";
const props = defineProps<{ class?: string }>();
</script>
<template>
  <SelectPortal
    ><SelectContent
      :class="
        cn(
          'relative z-50 min-w-32 overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md data-[state=closed]:animate-out data-[state=open]:animate-in',
          props.class,
        )
      "
      position="popper"
      ><SelectViewport class="p-1"><slot /></SelectViewport></SelectContent
  ></SelectPortal>
</template>
