<script setup lang="ts">
import { ChevronDown } from "@lucide/vue";
import { SelectTrigger } from "reka-ui";
import { cn } from "../../../lib/utils";
const props = defineProps<{ class?: string }>();
</script>
<template>
  <SelectTrigger
    :class="
      cn(
        'flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-hidden focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50 [&>span]:line-clamp-1',
        props.class,
      )
    "
    ><slot /><ChevronDown class="size-4 opacity-50"
  /></SelectTrigger>
</template>
