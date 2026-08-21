<script setup lang="ts">import { SelectLabel } from "reka-ui"; import { cn } from "../../../lib/utils"; const props = defineProps<{ class?: string }>();</script>
<template><SelectLabel :class="cn('py-1.5 pl-8 pr-2 text-sm font-semibold', props.class)"><slot /></SelectLabel></template>
