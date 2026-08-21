<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";
import PageHeader from "../components/shared/PageHeader.vue";
import { getArtifact, getArtifactContent, uploadImages } from "../features/artifacts/api";
import type { Artifact, DirectoryListing } from "../features/artifacts/types";
import { createEnhancement, getEnhancementCatalog } from "../features/enhancement/api";
import type { EnhancementCatalog } from "../features/enhancement/types";
import { getTask } from "../features/tasks/api";
import type { EnhancementTaskDetail } from "../api/types";

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

const methods = computed(() => backend.value === "traditional"
  ? catalog.value?.algorithms ?? []
  : catalog.value?.models ?? []);
const isFinished = computed(() => task.value && ["succeeded", "failed", "cancelled"].includes(task.value.status));
const resultUrl = computed(() => {
  return resultArtifact.value?.path_type === "file" ? resultArtifact.value.content_url : null;
});

async function loadResultArtifact(id: string) {
  loadingResult.value = true;
  resultArtifact.value = null;
  resultDirectory.value = null;
  try {
    const artifact = await getArtifact(id);
    resultArtifact.value = artifact;
    if (artifact.path_type === "directory") {
      resultDirectory.value = await getArtifactContent(id, artifact.path_type);
    }
  } finally {
    loadingResult.value = false;
  }
}

watch(backend, () => {
  method.value = methods.value[0]?.name ?? "";
});

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
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error("Parameters must be a JSON object.");
  }
  return parsed as Record<string, unknown>;
}

async function refreshTask(taskId: string) {
  try {
    const detail = await getTask(taskId);
    if (detail.kind !== "enhancement") throw new Error("The submitted task is not an enhancement task.");
    task.value = detail;
    if (isFinished.value && detail.job.output_artifact_id) {
      await loadResultArtifact(detail.job.output_artifact_id);
    }
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
onUnmounted(() => {
  if (pollTimer) clearTimeout(pollTimer);
});
</script>

<template>
  <PageHeader eyebrow="Workspace" title="Enhance images" description="Upload images, choose a catalog method, and send an enhancement task to the local worker.">
    <template #actions><span class="rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700">Enhancement worker</span></template>
  </PageHeader>

  <form class="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]" @submit.prevent="submit">
    <section class="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8">
      <div class="flex items-start justify-between gap-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Input images</p>
          <h2 class="mt-2 text-xl font-semibold text-slate-950">Upload one or more images</h2>
          <p class="mt-2 text-sm leading-6 text-slate-500">A single image becomes a file artifact. Multiple images are kept as one managed directory artifact.</p>
        </div>
        <span class="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">{{ files.length }} selected</span>
      </div>
      <label class="mt-8 flex min-h-56 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-slate-50 px-6 text-center transition hover:border-indigo-400 hover:bg-indigo-50/40 focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-indigo-600">
        <span class="flex size-12 items-center justify-center rounded-2xl bg-indigo-100 text-2xl font-light text-indigo-600">+</span>
        <span class="mt-4 text-sm font-medium text-slate-800">Choose image files</span>
        <span class="mt-1 text-xs text-slate-500">PNG, JPEG, or other supported image formats</span>
        <input id="enhancement-images" class="sr-only" type="file" accept="image/*" multiple aria-label="Choose image files" @change="selectFiles">
      </label>
      <ul v-if="files.length" class="mt-4 space-y-2 text-sm text-slate-600">
        <li v-for="file in files" :key="`${file.name}-${file.size}-${file.lastModified}`" class="flex justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2"><span class="truncate">{{ file.name }}</span><span class="shrink-0 text-xs text-slate-400">{{ Math.ceil(file.size / 1024) }} KB</span></li>
      </ul>
    </section>

    <section class="rounded-2xl border border-slate-200 bg-white p-6">
      <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Enhancement setup</p>
      <div class="mt-6 space-y-5">
        <div class="grid grid-cols-2 gap-2 rounded-lg bg-slate-100 p-1 text-sm">
          <button type="button" :aria-pressed="backend === 'traditional'" :class="backend === 'traditional' ? 'bg-white text-slate-950 shadow-xs' : 'text-slate-500'" class="rounded-md px-3 py-2 font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600" @click="backend = 'traditional'">Traditional</button>
          <button type="button" :aria-pressed="backend === 'deep'" :class="backend === 'deep' ? 'bg-white text-slate-950 shadow-xs' : 'text-slate-500'" class="rounded-md px-3 py-2 font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600" @click="backend = 'deep'">Deep model</button>
        </div>
        <label class="block text-sm font-medium text-slate-700">Method<select v-model="method" class="mt-2 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-hidden focus:border-indigo-500" :disabled="loadingCatalog"><option v-for="item in methods" :key="item.name" :value="item.name">{{ item.name }}</option></select></label>
        <label class="block text-sm font-medium text-slate-700">Device<select v-model="device" class="mt-2 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-hidden focus:border-indigo-500"><option v-for="item in catalog?.devices ?? []" :key="item" :value="item">{{ item }}</option></select></label>
        <label v-if="backend === 'traditional'" class="block text-sm font-medium text-slate-700">Gamma<input v-model.number="gamma" type="number" min="0" step="0.1" class="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-hidden focus:border-indigo-500"></label>
        <label v-else class="block text-sm font-medium text-slate-700">Parameters (JSON)<textarea v-model="paramsText" rows="4" class="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2.5 font-mono text-sm outline-hidden focus:border-indigo-500" spellcheck="false"></textarea></label>
        <label class="block text-sm font-medium text-slate-700">Checkpoint artifact ID <span class="font-normal text-slate-400">(optional)</span><input v-model="checkpointArtifactId" type="text" placeholder="For deep models only" class="mt-2 block w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-hidden focus:border-indigo-500"></label>
        <p v-if="error" role="alert" class="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{{ error }}</p>
        <button type="submit" :disabled="loading || loadingCatalog" :aria-busy="loading" class="w-full rounded-lg bg-slate-950 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:opacity-50">{{ loading ? 'Uploading and submitting…' : 'Submit enhancement task' }}</button>
      </div>
    </section>
  </form>

  <section v-if="task" class="mt-6 rounded-2xl border border-slate-200 bg-white p-6">
    <div class="flex flex-wrap items-center justify-between gap-3"><div><p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Task status</p><p class="mt-2 font-mono text-sm text-slate-700">{{ task.id }}</p></div><span class="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium capitalize text-slate-700">{{ task.status }}</span></div>
    <p v-if="task.message" class="mt-4 text-sm text-slate-600" aria-live="polite">{{ task.message }}</p>
     <div v-if="loadingResult" class="mt-4 text-sm text-slate-500" role="status" aria-live="polite">Loading result artifact…</div>
     <div v-else-if="resultDirectory" class="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4" aria-labelledby="result-directory-heading">
       <p id="result-directory-heading" class="text-sm font-medium text-slate-800">Result artifact directory</p>
       <ul v-if="resultDirectory.items.length" class="mt-3 divide-y divide-slate-200 rounded-md border border-slate-200 bg-white text-sm text-slate-600">
         <li v-for="item in resultDirectory.items" :key="item.display_name" class="wrap-break-word px-3 py-2 font-mono">{{ item.display_name }}</li>
       </ul>
       <p v-else class="mt-2 text-sm text-slate-500">The directory is empty.</p>
     </div>
     <div class="mt-4 flex flex-wrap items-center gap-3">
       <a v-if="resultUrl" :href="resultUrl" target="_blank" rel="noreferrer" class="inline-flex rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">Open result artifact</a>
      <RouterLink to="/tasks" class="inline-flex text-sm font-medium text-slate-500 hover:text-slate-950 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">View all tasks</RouterLink>
    </div>
  </section>
</template>
