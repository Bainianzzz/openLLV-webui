<script setup lang="ts">
import PageHeader from "../components/shared/PageHeader.vue";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Label } from "../components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { useDatasets } from "../features/datasets/useDatasets";

const {
  datasetKeys,
  datasets,
  task,
  form,
  status,
  page,
  total,
  pageCount,
  loadingCatalog,
  loadingDatasets,
  submitting,
  error,
  loadDatasets,
  submit,
  setPage,
} = useDatasets();

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});

function formatDate(value: string): string {
  return dateFormatter.format(new Date(value));
}

function formatBytes(value: number | null): string {
  if (value === null) return "Not reported";
  if (value === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const unit = Math.min(
    Math.floor(Math.log(value) / Math.log(1024)),
    units.length - 1,
  );
  return `${(value / 1024 ** unit).toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
}
</script>

<template>
  <PageHeader
    eyebrow="Library"
    title="Datasets"
    description="Download configured datasets into managed storage and track their availability for training."
  >
    <template #actions
      ><Badge variant="secondary">Dataset worker</Badge></template
    >
  </PageHeader>

  <div class="grid gap-6 xl:grid-cols-5">
    <Card class="xl:col-span-2">
      <CardHeader>
        <CardTitle>Download dataset</CardTitle>
        <CardDescription
          >Only dataset keys advertised by the server catalog can be
          submitted.</CardDescription
        >
      </CardHeader>
      <CardContent>
        <form class="space-y-5" @submit.prevent="submit">
          <div class="space-y-2">
            <Label for="dataset-key">Configured dataset</Label>
            <Select
              v-model="form.datasetKey"
              :disabled="loadingCatalog || !datasetKeys.length"
            >
              <SelectTrigger id="dataset-key" class="w-full">
                <SelectValue
                  :placeholder="
                    loadingCatalog ? 'Loading datasets…' : 'Select a dataset'
                  "
                />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="datasetKey in datasetKeys"
                  :key="datasetKey"
                  :value="datasetKey"
                >
                  {{ datasetKey }}
                </SelectItem>
              </SelectContent>
            </Select>
            <p
              v-if="!loadingCatalog && !datasetKeys.length"
              class="text-sm text-muted-foreground"
            >
              The server catalog does not currently advertise any downloadable
              datasets.
            </p>
          </div>

          <label
            class="flex cursor-pointer items-start gap-3 rounded-lg border bg-muted/20 p-4 focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-ring"
          >
            <input
              v-model="form.overwrite"
              type="checkbox"
              class="mt-0.5 size-4 rounded border-input accent-primary"
              aria-label="Overwrite existing dataset"
            />
            <span>
              <span class="block text-sm font-medium"
                >Overwrite existing dataset</span
              >
              <span class="mt-1 block text-sm text-muted-foreground"
                >Replace managed files when this dataset key already
                exists.</span
              >
            </span>
          </label>

          <Alert
            v-if="error"
            role="alert"
            class="border-destructive/30 bg-destructive/5 text-destructive"
          >
            <AlertTitle>Dataset request failed</AlertTitle>
            <AlertDescription>{{ error }}</AlertDescription>
          </Alert>

          <div class="flex gap-3">
            <Button
              type="submit"
              class="flex-1"
              :disabled="loadingCatalog || submitting || !datasetKeys.length"
              :aria-busy="submitting"
            >
              {{ submitting ? "Submitting…" : "Start download" }}
            </Button>
            <Button
              v-if="error"
              type="button"
              variant="outline"
              @click="loadDatasets"
              >Retry list</Button
            >
          </div>
        </form>
      </CardContent>
    </Card>

    <Card v-if="task" class="xl:col-span-3">
      <CardHeader class="flex-row items-start justify-between gap-4 space-y-0">
        <div class="min-w-0">
          <CardTitle>Latest download</CardTitle>
          <CardDescription class="mt-2 truncate font-mono">{{
            task.id
          }}</CardDescription>
        </div>
        <Badge
          :variant="task.status === 'failed' ? 'destructive' : 'secondary'"
          class="capitalize"
        >
          {{ task.status }}
        </Badge>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="grid gap-4 sm:grid-cols-2">
          <div class="rounded-lg border bg-muted/30 p-4">
            <p
              class="text-xs font-medium uppercase tracking-wide text-muted-foreground"
            >
              Dataset key
            </p>
            <p class="mt-2 font-semibold">{{ task.job.dataset_key }}</p>
          </div>
          <div class="rounded-lg border bg-muted/30 p-4">
            <p
              class="text-xs font-medium uppercase tracking-wide text-muted-foreground"
            >
              Overwrite
            </p>
            <p class="mt-2 font-semibold">
              {{ task.job.overwrite ? "Enabled" : "Disabled" }}
            </p>
          </div>
        </div>
        <p v-if="task.message" class="text-sm text-muted-foreground">
          {{ task.message }}
        </p>
        <p
          v-if="task.job.output_artifact_id"
          class="text-sm text-muted-foreground"
        >
          Output artifact:
          <span class="font-mono">{{ task.job.output_artifact_id }}</span>
        </p>
        <p
          v-if="task.error_detail"
          class="rounded-md bg-destructive/5 p-3 text-sm text-destructive"
        >
          {{ task.error_detail }}
        </p>
        <p
          v-if="!['succeeded', 'failed', 'cancelled'].includes(task.status)"
          class="text-sm text-muted-foreground"
        >
          Status updates automatically while this page is open.
        </p>
      </CardContent>
    </Card>

    <Card v-else class="flex min-h-64 flex-col justify-center xl:col-span-3">
      <CardContent class="pt-6 text-center">
        <p class="font-medium">No download submitted in this session</p>
        <p class="mt-2 text-sm text-muted-foreground">
          Choose a configured dataset to start an asynchronous download.
        </p>
      </CardContent>
    </Card>
  </div>

  <Card class="mt-6 overflow-hidden">
    <CardHeader
      class="gap-4 sm:flex-row sm:items-center sm:justify-between sm:space-y-0"
    >
      <div>
        <CardTitle>Managed datasets</CardTitle>
        <CardDescription class="mt-1"
          >{{ total }} dataset{{ total === 1 ? "" : "s" }} in managed
          storage</CardDescription
        >
      </div>
      <Select v-model="status">
        <SelectTrigger
          class="w-full sm:w-44"
          aria-label="Filter datasets by status"
        >
          <SelectValue placeholder="Filter by status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All statuses</SelectItem>
          <SelectItem value="downloading">Downloading</SelectItem>
          <SelectItem value="available">Available</SelectItem>
          <SelectItem value="failed">Failed</SelectItem>
        </SelectContent>
      </Select>
    </CardHeader>

    <CardContent class="p-0">
      <div class="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Dataset</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Files</TableHead>
              <TableHead>Size</TableHead>
              <TableHead>Updated</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-if="loadingDatasets">
              <TableCell
                colspan="5"
                class="h-32 text-center text-muted-foreground"
                >Loading managed datasets…</TableCell
              >
            </TableRow>
            <TableRow v-else-if="!datasets.length">
              <TableCell
                colspan="5"
                class="h-32 text-center text-muted-foreground"
                >No datasets match this filter.</TableCell
              >
            </TableRow>
            <TableRow v-for="dataset in datasets" v-else :key="dataset.id">
              <TableCell>
                <p class="font-medium">{{ dataset.display_name }}</p>
                <p class="mt-1 font-mono text-xs text-muted-foreground">
                  {{ dataset.dataset_key }}
                </p>
              </TableCell>
              <TableCell>
                <Badge
                  :variant="
                    dataset.status === 'failed' ? 'destructive' : 'secondary'
                  "
                  class="capitalize"
                >
                  {{ dataset.status }}
                </Badge>
                <p
                  v-if="dataset.error_code"
                  class="mt-1 text-xs text-destructive"
                >
                  {{ dataset.error_code }}
                </p>
              </TableCell>
              <TableCell>{{ dataset.file_count ?? "—" }}</TableCell>
              <TableCell>{{ formatBytes(dataset.total_bytes) }}</TableCell>
              <TableCell class="whitespace-nowrap text-muted-foreground">{{
                formatDate(dataset.updated_at)
              }}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>

      <div
        class="flex flex-col gap-3 border-t px-4 py-4 sm:flex-row sm:items-center sm:justify-between"
        aria-label="Dataset pagination"
      >
        <p class="text-sm text-muted-foreground">
          Page {{ page }} of {{ pageCount }}
        </p>
        <div class="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            :disabled="loadingDatasets || page <= 1"
            @click="setPage(page - 1)"
            >Previous</Button
          >
          <Button
            variant="outline"
            size="sm"
            :disabled="loadingDatasets || page >= pageCount"
            @click="setPage(page + 1)"
            >Next</Button
          >
        </div>
      </div>
    </CardContent>
  </Card>
</template>
