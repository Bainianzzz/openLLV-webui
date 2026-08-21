import { apiClient } from "../../api/client";
import type { Page, TaskDetail, TaskKind, TaskStatus, TaskSummary } from "../../api/types";
import type { TaskListParams } from "./types";

function query(params: TaskListParams): string {
  const values = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) values.set(key, String(value));
  }
  const encoded = values.toString();
  return encoded ? `?${encoded}` : "";
}

export function listTasks(params: TaskListParams = {}, signal?: AbortSignal) {
  return apiClient.request<Page<TaskSummary>>(`/tasks${query(params)}`, { signal });
}

export function getTask(id: string, signal?: AbortSignal) {
  return apiClient.request<TaskDetail>(`/tasks/${encodeURIComponent(id)}`, { signal });
}

export function cancelTask(id: string, signal?: AbortSignal) {
  return apiClient.request<TaskSummary>(`/tasks/${encodeURIComponent(id)}/cancel`, {
    method: "POST",
    signal,
  });
}

export function artifactContentUrl(id: string): string {
  return `/api/v1/artifacts/${encodeURIComponent(id)}/content`;
}
