<script setup lang="ts">
import { RouterLink } from "vue-router";
import PageHeader from "../components/shared/PageHeader.vue";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { useTraining } from "../features/training/useTraining";

const {
  catalog,
  datasets,
  task,
  checkpointUrl,
  loadingOptions,
  submitting,
  error,
  form,
  history,
  latestHistory,
  loadOptions,
  submit,
} = useTraining();
</script>

<template>
  <PageHeader eyebrow="Workspace" title="Train a model" description="Configure a training run from a managed dataset and follow it through completion.">
    <template #actions><Badge variant="secondary">Training worker</Badge></template>
  </PageHeader>

  <form class="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]" @submit.prevent="submit">
    <Card>
      <CardHeader>
        <CardTitle>Training configuration</CardTitle>
        <CardDescription>Models and devices come from the server catalog. Only available managed datasets can be selected.</CardDescription>
      </CardHeader>
      <CardContent class="grid gap-5 sm:grid-cols-2">
        <div class="space-y-2 sm:col-span-2">
          <Label for="training-model">Model</Label>
          <Select v-model="form.model" :disabled="loadingOptions">
            <SelectTrigger id="training-model" class="w-full"><SelectValue placeholder="Select a model" /></SelectTrigger>
            <SelectContent><SelectItem v-for="item in catalog?.models ?? []" :key="item.name" :value="item.name">{{ item.name }}</SelectItem></SelectContent>
          </Select>
        </div>

        <div class="space-y-2 sm:col-span-2">
          <Label for="training-dataset">Available dataset</Label>
          <Select v-model="form.datasetId" :disabled="loadingOptions || !datasets.length">
            <SelectTrigger id="training-dataset" class="w-full"><SelectValue placeholder="Select an available dataset" /></SelectTrigger>
            <SelectContent><SelectItem v-for="dataset in datasets" :key="dataset.id" :value="dataset.id">{{ dataset.display_name }}</SelectItem></SelectContent>
          </Select>
          <p v-if="!loadingOptions && !datasets.length" class="text-sm text-muted-foreground">No available datasets. Add or finish downloading one before training.</p>
        </div>

        <div class="space-y-2"><Label for="training-epochs">Epochs</Label><Input id="training-epochs" v-model.number="form.epochs" type="number" min="1" step="1" required /></div>
        <div class="space-y-2"><Label for="training-batch-size">Batch size</Label><Input id="training-batch-size" v-model.number="form.batchSize" type="number" min="1" step="1" required /></div>
        <div class="space-y-2"><Label for="training-learning-rate">Learning rate</Label><Input id="training-learning-rate" v-model.number="form.learningRate" type="number" min="0" step="any" required /></div>
        <div class="space-y-2"><Label for="training-resize">Resize</Label><Input id="training-resize" v-model.number="form.resize" type="number" min="1" step="1" required /></div>

        <div class="space-y-2 sm:col-span-2">
          <Label for="training-device">Device</Label>
          <Select v-model="form.device" :disabled="loadingOptions">
            <SelectTrigger id="training-device" class="w-full"><SelectValue placeholder="Select a device" /></SelectTrigger>
            <SelectContent><SelectItem v-for="device in catalog?.devices ?? []" :key="device" :value="device">{{ device }}</SelectItem></SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>

    <div class="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>SwanLab monitoring</CardTitle>
          <CardDescription>Optional experiment tracking. Credentials remain on the server.</CardDescription>
        </CardHeader>
        <CardContent class="space-y-5">
          <label class="flex cursor-pointer items-center gap-3 text-sm font-medium focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-ring">
            <input v-model="form.useSwanLab" type="checkbox" class="size-4 rounded border-input accent-primary" aria-label="Enable SwanLab for this run">
            Enable SwanLab for this run
          </label>
          <template v-if="form.useSwanLab">
            <div class="space-y-2"><Label for="swanlab-project">Project</Label><Input id="swanlab-project" v-model="form.swanlabProject" placeholder="openLLV" required /></div>
            <div class="space-y-2"><Label for="swanlab-experiment">Experiment</Label><Input id="swanlab-experiment" v-model="form.swanlabExperiment" placeholder="zero-dce-demo" required /></div>
          </template>

          <Alert v-if="error" role="alert" class="border-destructive/30 bg-destructive/5 text-destructive">
            <AlertTitle>Training request failed</AlertTitle><AlertDescription>{{ error }}</AlertDescription>
          </Alert>

          <div class="flex gap-3">
            <Button type="submit" class="flex-1" :disabled="loadingOptions || submitting || !datasets.length" :aria-busy="submitting">{{ submitting ? 'Submitting…' : 'Start training' }}</Button>
            <Button v-if="error && !task" type="button" variant="outline" @click="loadOptions">Retry</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  </form>

  <Card v-if="task" class="mt-6">
    <CardHeader class="flex-row items-start justify-between gap-4 space-y-0">
      <div class="min-w-0"><CardTitle>Training run</CardTitle><CardDescription class="mt-2 break-all font-mono">{{ task.id }}</CardDescription></div>
      <Badge variant="secondary" class="capitalize">{{ task.status }}</Badge>
    </CardHeader>
    <CardContent class="space-y-5">
      <p v-if="task.message" class="text-sm text-muted-foreground">{{ task.message }}</p>
      <p v-if="task.error_detail" class="rounded-md bg-destructive/5 p-3 text-sm text-destructive">{{ task.error_detail }}</p>

      <div v-if="task.status === 'succeeded'" class="grid gap-4 sm:grid-cols-3">
        <div class="rounded-lg border bg-muted/30 p-4"><p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">History</p><p class="mt-2 text-2xl font-semibold">{{ history.length }} <span class="text-sm font-normal text-muted-foreground">entries</span></p></div>
        <div class="rounded-lg border bg-muted/30 p-4"><p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">Best val loss</p><p class="mt-2 text-2xl font-semibold">{{ task.job.best_val_loss ?? 'Not reported' }}</p></div>
        <div class="rounded-lg border bg-muted/30 p-4"><p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">Latest history</p><p class="mt-2 break-words font-mono text-xs text-muted-foreground">{{ latestHistory ? JSON.stringify(latestHistory) : 'No history reported' }}</p></div>
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <a v-if="checkpointUrl" :href="checkpointUrl" target="_blank" rel="noreferrer" class="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90">Open checkpoint artifact</a>
        <a v-if="task.job.swanlab_url" :href="task.job.swanlab_url" target="_blank" rel="noreferrer" class="inline-flex h-10 items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground">Open SwanLab run</a>
        <RouterLink to="/tasks" class="inline-flex h-10 items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground">View all tasks</RouterLink>
      </div>
    </CardContent>
  </Card>
</template>
