<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";
import { getArtifact, getArtifactContent, uploadImages } from "@/api/artifacts";
import { createEnhancement, getEnhancementCatalog } from "@/api/enhancement";
import { getTask } from "@/api/tasks";
import type { Artifact, DirectoryListing } from "@/types/artifacts";
import type { EnhancementCatalog } from "@/types/enhancement";
import type { EnhancementTaskDetail } from "@/types";
import PageHeader from "@/components/shared/PageHeader.vue";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

const catalog = ref<EnhancementCatalog | null>(null);
const backend = ref<"traditional" | "deep">("traditional");
const method = ref("");
const device = ref("auto");
const gamma = ref(0.6);
const paramsText = ref("{}");
const checkpointArtifactId = ref("");
const files = ref<File[]>([]);
const task = ref<EnhancementTaskDetail | null>(null);
const resultArtifact = ref<Artifact | null>(null);
const resultDirectory = ref<DirectoryListing | null>(null);
const loadingResult = ref(false);
const loading = ref(false);
const loadingCatalog = ref(true);
const error = ref("");
let pollTimer: ReturnType<typeof setTimeout> | undefined;

const methods = computed(() => backend.value === "traditional" ? (catalog.value?.algorithms ?? []) : (catalog.value?.models ?? []));
const isFinished = computed(() => task.value && ["succeeded", "failed", "cancelled"].includes(task.value.status));
const resultUrl = computed(() => resultArtifact.value?.path_type === "file" ? resultArtifact.value.content_url : null);

async function loadResultArtifact(id: string) {
  loadingResult.value = true;
  resultArtifact.value = null;
  resultDirectory.value = null;
  try {
    const artifact = await getArtifact(id);
    resultArtifact.value = artifact;
    if (artifact.path_type === "directory") resultDirectory.value = await getArtifactContent(id, artifact.path_type);
  } finally {
    loadingResult.value = false;
  }
}

watch(backend, () => { method.value = methods.value[0]?.name ?? ""; });

async function loadCatalog() {
  loadingCatalog.value = true;
  try {
    catalog.value = await getEnhancementCatalog();
    method.value = methods.value[0]?.name ?? "";
    device.value = catalog.value.devices[0] ?? "auto";
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : "Unable to load the enhancement catalog.";
  } finally {
    loadingCatalog.value = false;
  }
}

function selectFiles(event: Event) {
  const input = event.target as HTMLInputElement;
  files.value = input.files ? Array.from(input.files) : [];
}

function parseParams(): Record<string, unknown> | undefined {
  if (backend.value === "traditional") return { gamma: gamma.value };
  const parsed: unknown = JSON.parse(paramsText.value);
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) throw new Error("Parameters must be a JSON object.");
  return parsed as Record<string, unknown>;
}

async function refreshTask(taskId: string) {
  try {
    const detail = await getTask(taskId);
    if (detail.kind !== "enhancement") throw new Error("The submitted task is not an enhancement task.");
    task.value = detail;
    if (isFinished.value && detail.job.output_artifact_id) await loadResultArtifact(detail.job.output_artifact_id);
    if (!isFinished.value) pollTimer = setTimeout(() => void refreshTask(taskId), 1500);
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : "Unable to refresh task status.";
  }
}

async function submit() {
  if (!files.value.length || !method.value) {
    error.value = "Choose at least one image and an available method.";
    return;
  }
  loading.value = true;
  error.value = "";
  task.value = null;
  resultArtifact.value = null;
  resultDirectory.value = null;
  try {
    const inputArtifact = await uploadImages({ files: files.value });
    const created = await createEnhancement({
      backend: backend.value,
      method: method.value,
      input_artifact_id: inputArtifact.id,
      checkpoint_artifact_id: backend.value === "deep" ? checkpointArtifactId.value.trim() || null : null,
      params: parseParams(),
      device: device.value,
    });
    await refreshTask(created.id);
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : "Unable to submit enhancement task.";
  } finally {
    loading.value = false;
  }
}

onMounted(() => void loadCatalog());
onUnmounted(() => { if (pollTimer) clearTimeout(pollTimer); });
</script>

<template>
  <PageHeader eyebrow="Workspace" title="Enhance images" description="Upload images, choose a catalog method, and send an enhancement task to the local worker.">
    <template #actions><Badge variant="secondary">Enhancement worker</Badge></template>
  </PageHeader>

  <form class="grid gap-6 xl:grid-cols-5" @submit.prevent="submit">
    <Card class="xl:col-span-3">
      <CardHeader class="flex-row items-start justify-between gap-4 space-y-0">
        <div>
          <CardTitle>Upload one or more images</CardTitle>
          <CardDescription class="mt-2">A single image becomes a file artifact. Multiple images are kept as one managed directory artifact.</CardDescription>
        </div>
        <Badge variant="secondary">{{ files.length }} selected</Badge>
      </CardHeader>
      <CardContent>
        <label class="flex min-h-56 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-input bg-muted/30 px-6 text-center transition hover:border-ring hover:bg-accent focus-within:outline-hidden focus-within:ring-2 focus-within:ring-ring">
          <span class="flex size-12 items-center justify-center rounded-2xl bg-primary text-2xl font-light text-primary-foreground">+</span>
          <span class="mt-4 text-sm font-medium">Choose image files</span>
          <span class="mt-1 text-xs text-muted-foreground">PNG, JPEG, or other supported image formats</span>
          <input id="enhancement-images" class="sr-only" type="file" accept="image/*" multiple aria-label="Choose image files" @change="selectFiles" />
        </label>
        <ul v-if="files.length" class="mt-4 flex flex-col gap-2 text-sm text-muted-foreground">
          <li v-for="file in files" :key="`${file.name}-${file.size}-${file.lastModified}`" class="flex justify-between gap-3 rounded-lg bg-muted/40 px-3 py-2">
            <span class="truncate">{{ file.name }}</span>
            <span class="shrink-0 text-xs">{{ Math.ceil(file.size / 1024) }} KB</span>
          </li>
        </ul>
      </CardContent>
    </Card>

    <Card class="xl:col-span-2">
      <CardHeader>
        <CardTitle>Enhancement setup</CardTitle>
        <CardDescription>Choose the processing backend and worker options.</CardDescription>
      </CardHeader>
      <CardContent class="flex flex-col gap-5">
        <ToggleGroup v-model="backend" type="single" class="grid grid-cols-2 rounded-lg bg-muted p-1">
          <ToggleGroupItem value="traditional" class="w-full">Traditional</ToggleGroupItem>
          <ToggleGroupItem value="deep" class="w-full">Deep model</ToggleGroupItem>
        </ToggleGroup>
        <div class="flex flex-col gap-2"><Label for="enhancement-method">Method</Label><Select v-model="method" :disabled="loadingCatalog"><SelectTrigger id="enhancement-method" class="w-full"><SelectValue placeholder="Select a method" /></SelectTrigger><SelectContent><SelectItem v-for="item in methods" :key="item.name" :value="item.name">{{ item.name }}</SelectItem></SelectContent></Select></div>
        <div class="flex flex-col gap-2"><Label for="enhancement-device">Device</Label><Select v-model="device"><SelectTrigger id="enhancement-device" class="w-full"><SelectValue placeholder="Select a device" /></SelectTrigger><SelectContent><SelectItem v-for="item in catalog?.devices ?? []" :key="item" :value="item">{{ item }}</SelectItem></SelectContent></Select></div>
        <div v-if="backend === 'traditional'" class="flex flex-col gap-2"><Label for="enhancement-gamma">Gamma</Label><Input id="enhancement-gamma" v-model.number="gamma" type="number" min="0" step="0.1" /></div>
        <div v-else class="flex flex-col gap-2"><Label for="enhancement-params">Parameters (JSON)</Label><Textarea id="enhancement-params" v-model="paramsText" rows="4" class="font-mono" spellcheck="false" /></div>
        <div class="flex flex-col gap-2"><Label for="checkpoint-artifact">Checkpoint artifact ID <span class="font-normal text-muted-foreground">(optional)</span></Label><Input id="checkpoint-artifact" v-model="checkpointArtifactId" placeholder="For deep models only" /></div>
        <Alert v-if="error" variant="destructive" role="alert"><AlertTitle>Enhancement request failed</AlertTitle><AlertDescription>{{ error }}</AlertDescription></Alert>
        <Button type="submit" class="w-full" :disabled="loading || loadingCatalog" :aria-busy="loading">{{ loading ? "Uploading and submitting…" : "Submit enhancement task" }}</Button>
      </CardContent>
    </Card>
  </form>

  <Card v-if="task" class="mt-6">
    <CardHeader class="flex-row items-start justify-between gap-3 space-y-0"><div class="min-w-0"><CardTitle>Task status</CardTitle><CardDescription class="mt-2 break-all font-mono">{{ task.id }}</CardDescription></div><Badge variant="secondary" class="capitalize">{{ task.status }}</Badge></CardHeader>
    <CardContent class="flex flex-col gap-4">
      <p v-if="task.message" class="text-sm text-muted-foreground" aria-live="polite">{{ task.message }}</p>
      <p v-if="loadingResult" class="text-sm text-muted-foreground" role="status" aria-live="polite">Loading result artifact…</p>
      <Card v-else-if="resultDirectory" class="bg-muted/30"><CardHeader><CardTitle class="text-base">Result artifact directory</CardTitle></CardHeader><CardContent><ScrollArea class="max-h-48"><ul v-if="resultDirectory.items.length" class="divide-y rounded-md border bg-background text-sm text-muted-foreground"><li v-for="item in resultDirectory.items" :key="item.display_name" class="wrap-break-word px-3 py-2 font-mono">{{ item.display_name }}</li></ul><Empty v-else class="min-h-24"><EmptyHeader><EmptyTitle class="text-sm">The directory is empty</EmptyTitle><EmptyDescription>No output files were reported.</EmptyDescription></EmptyHeader></Empty></ScrollArea></CardContent></Card>
      <div class="flex flex-wrap items-center gap-3"><a v-if="resultUrl" :href="resultUrl" target="_blank" rel="noreferrer" class="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">Open result artifact</a><RouterLink to="/tasks" class="text-sm font-medium text-muted-foreground hover:text-foreground">View all tasks</RouterLink></div>
    </CardContent>
  </Card>
</template>
