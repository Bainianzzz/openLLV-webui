<script setup lang="ts">
import { cn } from "../../../lib/utils";
import { cva, type VariantProps } from "class-variance-authority";

const alertVariants = cva("relative w-full rounded-lg border p-4", {
  variants: {
    variant: {
      default: "bg-background text-foreground",
      destructive: "border-destructive/50 text-destructive",
    },
  },
  defaultVariants: { variant: "default" },
});

type AlertVariants = VariantProps<typeof alertVariants>;
const props = defineProps<{
  class?: string;
  variant?: AlertVariants["variant"];
}>();
</script>
<template>
  <div
    role="alert"
    :class="cn(alertVariants({ variant: props.variant }), props.class)"
  >
    <slot />
  </div>
</template>
