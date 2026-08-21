import { computed, onUnmounted, ref } from "vue";
import type {
  TaskDetail,
  TaskKind,
  TaskStatus,
  TaskSummary,
} from "@/types/tasks";
import { cancelTask, getTask, listTasks } from "@/api/tasks";

export const terminalTaskStatuses: TaskStatus[] = [
  "succeeded",
  "failed",
  "cancelled",
];

export function isTerminalTaskStatus(status: TaskStatus): boolean {
  return terminalTaskStatuses.includes(status);
}

export function useTasks() {
  const items = ref<TaskSummary[]>([]);
  const page = ref(1);
  const pageSize = ref(20);
  const total = ref(0);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const task = ref<TaskDetail | null>(null);
  const detailLoading = ref(false);
  const detailError = ref<string | null>(null);
  const kind = ref<TaskKind | undefined>();
  const status = ref<TaskStatus | undefined>();
  let listController: AbortController | null = null;
  let detailController: AbortController | null = null;
  let listPollTimer: ReturnType<typeof setTimeout> | null = null;
  let pollTimer: ReturnType<typeof setTimeout> | null = null;

  const pageCount = computed(() =>
    Math.max(1, Math.ceil(total.value / pageSize.value)),
  );

  async function loadTasks(nextPage = page.value): Promise<void> {
    if (listPollTimer !== null) clearTimeout(listPollTimer);
    listPollTimer = null;
    listController?.abort();
    const controller = new AbortController();
    listController = controller;
    loading.value = true;
    error.value = null;
    try {
      const result = await listTasks(
        {
          page: nextPage,
          page_size: pageSize.value,
          kind: kind.value,
          status: status.value,
        },
        controller.signal,
      );
      if (controller.signal.aborted) return;
      items.value = result.items;
      page.value = result.page;
      pageSize.value = result.page_size;
      total.value = result.total;
      if (items.value.some((item) => !isTerminalTaskStatus(item.status)))
        scheduleListPoll();
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") return;
      error.value =
        cause instanceof Error ? cause.message : "Unable to load tasks";
    } finally {
      if (listController === controller) loading.value = false;
    }
  }

  function scheduleListPoll(): void {
    listPollTimer = setTimeout(() => void loadTasks(page.value), 3000);
  }

  async function setFilters(
    nextKind?: TaskKind,
    nextStatus?: TaskStatus,
  ): Promise<void> {
    kind.value = nextKind;
    status.value = nextStatus;
    await loadTasks(1);
  }

  async function loadTask(id: string, poll = true): Promise<TaskDetail | null> {
    stopPolling();
    detailController?.abort();
    const controller = new AbortController();
    detailController = controller;
    detailLoading.value = true;
    detailError.value = null;
    try {
      const result = await getTask(id, controller.signal);
      if (controller.signal.aborted) return null;
      if (poll && !isTerminalTaskStatus(result.status)) schedulePoll(id);
      task.value = result;
      return result;
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError")
        return null;
      detailError.value =
        cause instanceof Error ? cause.message : "Unable to load task";
      throw cause;
    } finally {
      if (detailController === controller) detailLoading.value = false;
    }
  }

  function schedulePoll(id: string): void {
    pollTimer = setTimeout(() => void loadTask(id), 2000);
  }

  function stopPolling(): void {
    if (pollTimer !== null) clearTimeout(pollTimer);
    pollTimer = null;
  }

  async function requestCancel(id: string): Promise<TaskSummary> {
    detailController?.abort();
    stopPolling();
    const controller = new AbortController();
    detailController = controller;
    const result = await cancelTask(id, controller.signal);
    if (task.value) {
      task.value.status = result.status;
      task.value.message = result.message;
      task.value.created_at = result.created_at;
      task.value.started_at = result.started_at;
      task.value.finished_at = result.finished_at;
    }
    if (!isTerminalTaskStatus(result.status)) schedulePoll(id);
    return result;
  }

  onUnmounted(() => {
    listController?.abort();
    detailController?.abort();
    if (listPollTimer !== null) clearTimeout(listPollTimer);
    stopPolling();
  });

  return {
    items,
    page,
    total,
    pageCount,
    loading,
    error,
    kind,
    status,
    task,
    detailLoading,
    detailError,
    loadTasks,
    setFilters,
    loadTask,
    requestCancel,
  };
}
