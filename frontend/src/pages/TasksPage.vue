<script setup lang="ts">
import { ref } from "vue";
import { RouterLink } from "vue-router";
import PageHeader from "../components/shared/PageHeader.vue";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import type { TaskKind, TaskStatus } from "../features/tasks/types";
import { useTasks } from "../features/tasks/useTasks";

const { items, page, total, pageCount, loading, error, loadTasks, setFilters } = useTasks();
const kindFilter = ref("all");
const statusFilter = ref("all");
const dateFormatter = new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" });

function formatDate(value: string | null): string {
  return value ? dateFormatter.format(new Date(value)) : "Not started";
}

function kindLabel(kind: TaskKind): string {
  return { enhancement: "Enhancement", training: "Training", dataset_download: "Dataset download" }[kind];
}

function statusVariant(status: TaskStatus): "default" | "secondary" | "destructive" | "outline" {
  if (status === "failed") return "destructive";
  if (status === "succeeded") return "default";
  if (status === "cancelled") return "outline";
  return "secondary";
}

async function applyFilters(): Promise<void> {
  await setFilters(
    kindFilter.value === "all" ? undefined : kindFilter.value as TaskKind,
    statusFilter.value === "all" ? undefined : statusFilter.value as TaskStatus,
  );
}

async function changePage(nextPage: number): Promise<void> {
  await loadTasks(nextPage);
}

void loadTasks();
</script>

<template>
  <PageHeader eyebrow="Activity" title="Tasks" description="Every enhancement, training, and dataset download is tracked from queue to completion." />

  <Card class="overflow-hidden">
    <CardHeader class="gap-4 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
      <div>
        <CardTitle>Task history</CardTitle>
        <CardDescription class="mt-1">{{ total }} task{{ total === 1 ? '' : 's' }} · newest first</CardDescription>
      </div>
      <div class="grid gap-2 sm:grid-cols-2">
        <Select v-model="kindFilter" @update:model-value="applyFilters">
          <SelectTrigger class="w-full sm:w-48" aria-label="Filter tasks by kind"><SelectValue placeholder="All task types" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All task types</SelectItem>
            <SelectItem value="enhancement">Enhancement</SelectItem>
            <SelectItem value="training">Training</SelectItem>
            <SelectItem value="dataset_download">Dataset download</SelectItem>
          </SelectContent>
        </Select>
        <Select v-model="statusFilter" @update:model-value="applyFilters">
          <SelectTrigger class="w-full sm:w-40" aria-label="Filter tasks by status"><SelectValue placeholder="All statuses" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="queued">Queued</SelectItem>
            <SelectItem value="running">Running</SelectItem>
            <SelectItem value="cancelling">Cancelling</SelectItem>
            <SelectItem value="succeeded">Succeeded</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </CardHeader>
    <Alert v-if="error" role="alert" class="mx-6 mb-4 border-destructive/30 bg-destructive/5 text-destructive">
      <AlertTitle>Unable to load tasks</AlertTitle><AlertDescription>{{ error }}</AlertDescription>
    </Alert>
    <CardContent class="p-0">
      <div class="overflow-x-auto">
        <Table>
          <TableHeader><TableRow><TableHead>Type</TableHead><TableHead>Status</TableHead><TableHead>Message</TableHead><TableHead>Created</TableHead><TableHead>Finished</TableHead><TableHead class="text-right"> </TableHead></TableRow></TableHeader>
          <TableBody>
            <TableRow v-if="loading"><TableCell colspan="6" class="h-32 text-center text-muted-foreground">Loading tasks…</TableCell></TableRow>
            <TableRow v-else-if="!items.length"><TableCell colspan="6" class="h-32 text-center text-muted-foreground">No tasks match these filters.</TableCell></TableRow>
            <TableRow v-for="item in items" v-else :key="item.id">
              <TableCell><p class="font-medium">{{ kindLabel(item.kind) }}</p><p class="mt-1 font-mono text-xs text-muted-foreground">{{ item.id }}</p></TableCell>
              <TableCell><Badge :variant="statusVariant(item.status)" class="capitalize">{{ item.status }}</Badge></TableCell>
              <TableCell class="max-w-72 text-muted-foreground">{{ item.message || 'No message' }}</TableCell>
              <TableCell class="whitespace-nowrap text-muted-foreground">{{ formatDate(item.created_at) }}</TableCell>
              <TableCell class="whitespace-nowrap text-muted-foreground">{{ formatDate(item.finished_at) }}</TableCell>
              <TableCell class="text-right"><RouterLink :to="`/tasks/${item.id}`" class="font-medium text-primary hover:underline">Details</RouterLink></TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
      <div class="flex flex-col gap-3 border-t px-4 py-4 sm:flex-row sm:items-center sm:justify-between" aria-label="Task pagination">
        <p class="text-sm text-muted-foreground">Page {{ page }} of {{ pageCount }}</p>
        <div class="flex gap-2"><Button variant="outline" size="sm" :disabled="loading || page <= 1" @click="changePage(page - 1)">Previous</Button><Button variant="outline" size="sm" :disabled="loading || page >= pageCount" @click="changePage(page + 1)">Next</Button></div>
      </div>
    </CardContent>
  </Card>
</template>
