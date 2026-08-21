<script setup lang="ts">
import { onMounted, ref, watch, computed } from "vue";
import { RouterLink, useRoute } from "vue-router";
import PageHeader from "../components/shared/PageHeader.vue";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { artifactContentUrl } from "../features/tasks/api";
import { useTasks } from "../features/tasks/useTasks";
import type { TaskStatus } from "../features/tasks/types";

const route = useRoute();
const taskId = computed(() => String(route.params.id));
const { task, detailLoading, detailError, loadTask, requestCancel } = useTasks();
const cancelling = ref(false);
const dateFormatter = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });

function formatDate(value: string | null): string {
  return value ? dateFormatter.format(new Date(value)) : "Not reported";
}

function statusVariant(status: TaskStatus): "default" | "secondary" | "destructive" | "outline" {
  if (status === "failed") return "destructive";
  if (status === "succeeded") return "default";
  if (status === "cancelled") return "outline";
  return "secondary";
}

function canCancel(status: TaskStatus): boolean {
  return status === "queued" || status === "running";
}

function historyEntry(value: unknown): string {
  return typeof value === "string" ? value : JSON.stringify(value);
}

async function cancel(): Promise<void> {
  if (!task.value || !canCancel(task.value.status)) return;
  cancelling.value = true;
  try {
    await requestCancel(task.value.id);
  } catch (cause) {
    // The task remains visible; the next explicit reload can retry the request.
    if (cause instanceof Error) detailError.value = cause.message;
  } finally {
    cancelling.value = false;
  }
}

async function load(): Promise<void> {
  try {
    await loadTask(taskId.value);
  } catch {
    // The composable exposes the user-facing error.
  }
}

watch(taskId, () => void load());
onMounted(() => void load());
</script>

<template>
  <PageHeader eyebrow="Task detail" :title="task ? `${task.kind.replace('_', ' ')} task` : 'Task details'" :description="`Task ${taskId}`">
    <template #actions><RouterLink to="/tasks" class="text-sm font-medium text-muted-foreground hover:text-foreground">Back to tasks</RouterLink></template>
  </PageHeader>

  <Alert v-if="detailError" class="mb-6 border-destructive/30 bg-destructive/5 text-destructive">
    <AlertTitle>Unable to load task</AlertTitle><AlertDescription>{{ detailError }}</AlertDescription>
  </Alert>
  <div v-if="detailLoading && !task" class="rounded-xl border bg-card p-8 text-center text-muted-foreground">Loading task details…</div>
  <div v-else-if="task" class="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(280px,0.8fr)]">
    <div class="space-y-6">
      <Card>
        <CardHeader class="flex-row items-start justify-between gap-4 space-y-0"><div><CardTitle>Task status</CardTitle><CardDescription class="mt-2">{{ task.message || 'No status message reported.' }}</CardDescription></div><Badge :variant="statusVariant(task.status)" class="capitalize">{{ task.status }}</Badge></CardHeader>
        <CardContent class="grid gap-4 sm:grid-cols-3"><div><p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">Created</p><p class="mt-2 text-sm">{{ formatDate(task.created_at) }}</p></div><div><p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">Started</p><p class="mt-2 text-sm">{{ formatDate(task.started_at) }}</p></div><div><p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">Finished</p><p class="mt-2 text-sm">{{ formatDate(task.finished_at) }}</p></div></CardContent>
      </Card>

      <Card v-if="task.kind === 'enhancement'">
        <CardHeader><CardTitle>Enhancement</CardTitle><CardDescription>{{ task.job.backend }} backend · {{ task.job.method }}</CardDescription></CardHeader>
        <CardContent class="space-y-4"><div class="grid gap-4 sm:grid-cols-2"><div><p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">Device</p><p class="mt-2 text-sm">{{ task.job.device }}</p></div><div><p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">Input artifact</p><p class="mt-2 break-all font-mono text-xs">{{ task.job.input_artifact_id }}</p></div></div><div class="flex flex-wrap gap-3"><a v-if="task.job.output_artifact_id" :href="artifactContentUrl(task.job.output_artifact_id)" target="_blank" rel="noreferrer" class="inline-flex h-10 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90">Open output artifact</a><a :href="artifactContentUrl(task.job.input_artifact_id)" target="_blank" rel="noreferrer" class="inline-flex h-10 items-center rounded-md border border-input px-4 text-sm font-medium hover:bg-accent">Open input artifact</a></div></CardContent>
      </Card>

      <Card v-else-if="task.kind === 'training'">
        <CardHeader><CardTitle>Training results</CardTitle><CardDescription>{{ task.job.model }} · {{ task.job.device }}</CardDescription></CardHeader>
        <CardContent class="space-y-5"><div class="grid gap-4 sm:grid-cols-3"><div class="rounded-lg border bg-muted/30 p-4"><p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">History</p><p class="mt-2 text-2xl font-semibold">{{ task.job.history?.length ?? 0 }} <span class="text-sm font-normal text-muted-foreground">entries</span></p></div><div class="rounded-lg border bg-muted/30 p-4"><p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">Best val loss</p><p class="mt-2 text-2xl font-semibold">{{ task.job.best_val_loss ?? 'Not reported' }}</p></div><div class="rounded-lg border bg-muted/30 p-4"><p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">Dataset</p><p class="mt-2 break-all font-mono text-xs">{{ task.job.dataset_id }}</p></div></div><div v-if="task.job.history?.length" class="space-y-2"><p class="text-sm font-medium">Training history</p><div class="max-h-64 space-y-2 overflow-auto rounded-lg border bg-muted/20 p-3"><p v-for="(entry, index) in task.job.history" :key="index" class="break-words font-mono text-xs text-muted-foreground">{{ historyEntry(entry) }}</p></div></div><div class="flex flex-wrap gap-3"><a v-if="task.job.checkpoint_artifact_id" :href="artifactContentUrl(task.job.checkpoint_artifact_id)" target="_blank" rel="noreferrer" class="inline-flex h-10 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90">Open checkpoint artifact</a><a v-if="task.job.swanlab_url" :href="task.job.swanlab_url" target="_blank" rel="noreferrer" class="inline-flex h-10 items-center rounded-md border border-input px-4 text-sm font-medium hover:bg-accent">Open SwanLab run</a></div></CardContent>
      </Card>

      <Card v-else>
        <CardHeader><CardTitle>Dataset download</CardTitle><CardDescription>{{ task.job.dataset_key }}</CardDescription></CardHeader>
        <CardContent class="grid gap-4 sm:grid-cols-2"><div><p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">Overwrite</p><p class="mt-2 text-sm">{{ task.job.overwrite ? 'Enabled' : 'Disabled' }}</p></div><div><p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">Dataset ID</p><p class="mt-2 break-all font-mono text-xs">{{ task.job.dataset_id || 'Not created' }}</p></div></CardContent>
      </Card>
    </div>

    <Card class="h-fit"><CardHeader><CardTitle>Actions</CardTitle><CardDescription>Task ID and lifecycle controls</CardDescription></CardHeader><CardContent class="space-y-5"><p class="break-all rounded-lg bg-muted/40 p-3 font-mono text-xs text-muted-foreground">{{ task.id }}</p><Button v-if="canCancel(task.status)" variant="destructive" class="w-full" :disabled="cancelling" @click="cancel">{{ cancelling ? 'Requesting cancellation…' : 'Cancel task' }}</Button><p v-if="task.status === 'cancelling'" class="text-sm text-muted-foreground">Cancellation requested. This page will continue checking until the worker finishes.</p><div v-if="task.error_code || task.error_detail" class="rounded-lg bg-destructive/5 p-4 text-sm text-destructive"><p v-if="task.error_code" class="font-medium">{{ task.error_code }}</p><p v-if="task.error_detail" class="mt-1">{{ task.error_detail }}</p></div></CardContent></Card>
  </div>
</template>
