import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import type { DatasetDownloadTaskDetail } from "../../api/types";
import {
  createDatasetDownload,
  getDatasetCatalog,
  getDatasetDownloadTask,
  listDatasets,
} from "./api";
import type { Dataset, DatasetStatus } from "./types";

const PAGE_SIZE = 10;
const FINAL_STATUSES = new Set(["succeeded", "failed", "cancelled"]);

function isAbortError(cause: unknown): boolean {
  return cause instanceof DOMException && cause.name === "AbortError";
}

export function useDatasets() {
  const datasetKeys = ref<string[]>([]);
  const datasets = ref<Dataset[]>([]);
  const task = ref<DatasetDownloadTaskDetail | null>(null);
  const form = reactive({ datasetKey: "", overwrite: false });
  const status = ref<DatasetStatus | "all">("all");
  const page = ref(1);
  const total = ref(0);
  const loadingCatalog = ref(true);
  const loadingDatasets = ref(true);
  const submitting = ref(false);
  const error = ref("");

  let listController: AbortController | undefined;
  let actionController: AbortController | undefined;
  let pollTimer: ReturnType<typeof setTimeout> | undefined;
  let activeTaskId = "";

  const pageCount = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)));
  const isTaskFinished = computed(() => task.value ? FINAL_STATUSES.has(task.value.status) : false);

  function stopPolling() {
    if (pollTimer) clearTimeout(pollTimer);
    pollTimer = undefined;
  }

  async function loadCatalog() {
    loadingCatalog.value = true;
    try {
      const catalog = await getDatasetCatalog(actionController?.signal);
      datasetKeys.value = catalog.datasets?.map((item) => item.name) ?? [];
      if (!datasetKeys.value.includes(form.datasetKey)) {
        form.datasetKey = datasetKeys.value[0] ?? "";
      }
    } catch (cause) {
      if (isAbortError(cause)) return;
      error.value = cause instanceof Error ? cause.message : "Unable to load configured datasets.";
    } finally {
      loadingCatalog.value = false;
    }
  }

  async function loadDatasets() {
    listController?.abort();
    listController = new AbortController();
    loadingDatasets.value = true;
    try {
      const response = await listDatasets({
        page: page.value,
        page_size: PAGE_SIZE,
        ...(status.value === "all" ? {} : { status: status.value }),
      }, listController.signal);
      datasets.value = response.items;
      total.value = response.total;
      if (response.page > Math.max(1, Math.ceil(response.total / PAGE_SIZE))) {
        page.value = Math.max(1, Math.ceil(response.total / PAGE_SIZE));
      }
    } catch (cause) {
      if (isAbortError(cause)) return;
      error.value = cause instanceof Error ? cause.message : "Unable to load managed datasets.";
    } finally {
      loadingDatasets.value = false;
    }
  }

  async function refreshTask(taskId: string) {
    if (document.hidden || taskId !== activeTaskId) return;
    actionController = new AbortController();
    try {
      const detail = await getDatasetDownloadTask(taskId, actionController.signal);
      task.value = detail;
      await loadDatasets();
      if (!FINAL_STATUSES.has(detail.status)) {
        pollTimer = setTimeout(() => void refreshTask(taskId), 1500);
      }
    } catch (cause) {
      if (isAbortError(cause)) return;
      error.value = cause instanceof Error ? cause.message : "Unable to refresh download status.";
    }
  }

  async function submit() {
    if (!form.datasetKey) {
      error.value = "Choose a configured dataset to download.";
      return;
    }
    stopPolling();
    actionController?.abort();
    actionController = new AbortController();
    submitting.value = true;
    error.value = "";
    task.value = null;
    try {
      const created = await createDatasetDownload({
        dataset_key: form.datasetKey,
        overwrite: form.overwrite,
      }, actionController.signal);
      activeTaskId = created.id;
      await refreshTask(created.id);
    } catch (cause) {
      if (isAbortError(cause)) return;
      error.value = cause instanceof Error ? cause.message : "Unable to submit the dataset download.";
    } finally {
      submitting.value = false;
    }
  }

  function setPage(nextPage: number) {
    if (nextPage < 1 || nextPage > pageCount.value || nextPage === page.value) return;
    page.value = nextPage;
  }

  function handleVisibilityChange() {
    if (document.hidden) {
      stopPolling();
      actionController?.abort();
    } else if (activeTaskId && !isTaskFinished.value) {
      void refreshTask(activeTaskId);
    }
  }

  watch(status, () => {
    page.value = 1;
    void loadDatasets();
  });
  watch(page, () => void loadDatasets());

  onMounted(() => {
    actionController = new AbortController();
    document.addEventListener("visibilitychange", handleVisibilityChange);
    void Promise.all([loadCatalog(), loadDatasets()]);
  });
  onUnmounted(() => {
    document.removeEventListener("visibilitychange", handleVisibilityChange);
    stopPolling();
    listController?.abort();
    actionController?.abort();
  });

  return {
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
  };
}
