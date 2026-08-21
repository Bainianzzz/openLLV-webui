import { computed, onMounted, onUnmounted, reactive, ref } from "vue";
import type { TrainingTaskDetail } from "../../api/types";
import { getArtifact } from "../artifacts/api";
import { createTraining, getTrainingCatalog, getTrainingTask, listAvailableDatasets } from "./api";
import type { CreateTrainingRequest, Dataset, TrainingCatalog } from "./types";

const FINAL_STATUSES = new Set(["succeeded", "failed", "cancelled"]);

export function useTraining() {
  const catalog = ref<TrainingCatalog | null>(null);
  const datasets = ref<Dataset[]>([]);
  const task = ref<TrainingTaskDetail | null>(null);
  const checkpointUrl = ref("");
  const loadingOptions = ref(true);
  const submitting = ref(false);
  const error = ref("");
  const form = reactive({
    model: "",
    datasetId: "",
    epochs: 20,
    batchSize: 8,
    learningRate: 0.0001,
    resize: 256,
    device: "auto",
    useSwanLab: false,
    swanlabProject: "",
    swanlabExperiment: "",
  });

  let requestController: AbortController | undefined;
  let pollTimer: ReturnType<typeof setTimeout> | undefined;
  let activeTaskId = "";

  const isFinished = computed(() => task.value ? FINAL_STATUSES.has(task.value.status) : false);
  const history = computed(() => task.value?.job.history ?? []);
  const latestHistory = computed(() => history.value.at(-1));

  function stopPolling() {
    if (pollTimer) clearTimeout(pollTimer);
    pollTimer = undefined;
  }

  async function loadOptions() {
    requestController?.abort();
    requestController = new AbortController();
    loadingOptions.value = true;
    error.value = "";
    try {
      const [catalogResponse, datasetResponse] = await Promise.all([
        getTrainingCatalog(requestController.signal),
        listAvailableDatasets(requestController.signal),
      ]);
      catalog.value = catalogResponse;
      datasets.value = datasetResponse.items;
      form.model = catalogResponse.models[0]?.name ?? "";
      form.device = catalogResponse.devices[0] ?? "auto";
      form.datasetId = datasetResponse.items[0]?.id ?? "";
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") return;
      error.value = cause instanceof Error ? cause.message : "Unable to load training options.";
    } finally {
      loadingOptions.value = false;
    }
  }

  async function refreshTask(taskId: string) {
    if (document.hidden || taskId !== activeTaskId) return;
    requestController = new AbortController();
    try {
      const detail = await getTrainingTask(taskId, requestController.signal);
      task.value = detail;
      if (FINAL_STATUSES.has(detail.status)) {
        const checkpointId = detail.job.checkpoint_artifact_id;
        if (checkpointId) {
          const artifact = await getArtifact(checkpointId, requestController.signal);
          checkpointUrl.value = artifact.content_url;
        }
        return;
      }
      pollTimer = setTimeout(() => void refreshTask(taskId), 1500);
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") return;
      error.value = cause instanceof Error ? cause.message : "Unable to refresh training status.";
    }
  }

  function validate(): string | null {
    if (!form.model || !form.datasetId || !form.device) return "Choose a model, an available dataset, and a device.";
    if (!Number.isInteger(form.epochs) || form.epochs < 1) return "Epochs must be a positive integer.";
    if (!Number.isInteger(form.batchSize) || form.batchSize < 1) return "Batch size must be a positive integer.";
    if (!(form.learningRate > 0)) return "Learning rate must be greater than zero.";
    if (!Number.isInteger(form.resize) || form.resize < 1) return "Resize must be a positive integer.";
    if (form.useSwanLab && (!form.swanlabProject.trim() || !form.swanlabExperiment.trim())) {
      return "Enter both a SwanLab project and experiment name.";
    }
    return null;
  }

  async function submit() {
    const validationError = validate();
    if (validationError) {
      error.value = validationError;
      return;
    }

    stopPolling();
    requestController?.abort();
    requestController = new AbortController();
    submitting.value = true;
    error.value = "";
    task.value = null;
    checkpointUrl.value = "";
    try {
      const request: CreateTrainingRequest = {
        model: form.model,
        dataset_id: form.datasetId,
        epochs: form.epochs,
        batch_size: form.batchSize,
        lr: form.learningRate,
        resize: form.resize,
        device: form.device,
        num_workers: 0,
        ...(form.useSwanLab ? {
          swanlab: {
            project: form.swanlabProject.trim(),
            experiment: form.swanlabExperiment.trim(),
          },
        } : {}),
      };
      const created = await createTraining(request, requestController.signal);
      activeTaskId = created.id;
      await refreshTask(created.id);
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") return;
      error.value = cause instanceof Error ? cause.message : "Unable to submit the training task.";
    } finally {
      submitting.value = false;
    }
  }

  function handleVisibilityChange() {
    if (document.hidden) {
      stopPolling();
      requestController?.abort();
    } else if (activeTaskId && !isFinished.value) {
      void refreshTask(activeTaskId);
    }
  }

  onMounted(() => {
    document.addEventListener("visibilitychange", handleVisibilityChange);
    void loadOptions();
  });
  onUnmounted(() => {
    document.removeEventListener("visibilitychange", handleVisibilityChange);
    stopPolling();
    requestController?.abort();
  });

  return {
    catalog,
    datasets,
    task,
    checkpointUrl,
    loadingOptions,
    submitting,
    error,
    form,
    isFinished,
    history,
    latestHistory,
    loadOptions,
    submit,
  };
}
