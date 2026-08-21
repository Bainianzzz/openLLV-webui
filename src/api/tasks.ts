import { http } from "@/api/http";
import type { Page, TaskDetail, TaskSummary } from "@/types";
import type { TaskListParams } from "@/types/tasks";

function query(params: TaskListParams): string {
  const values = new URLSearchParams();
  for (const [key, value] of Object.entries(params))
    if (value !== undefined) values.set(key, String(value));
  const encoded = values.toString();
  return encoded ? `?${encoded}` : "";
}

export function listTasks(params: TaskListParams = {}, signal?: AbortSignal) {
  return http
    .get<Page<TaskSummary>>(`/tasks${query(params)}`, { signal })
    .then(({ data }) => data);
}
export function getTask(id: string, signal?: AbortSignal) {
  return http
    .get<TaskDetail>(`/tasks/${encodeURIComponent(id)}`, { signal })
    .then(({ data }) => data);
}
export function cancelTask(id: string, signal?: AbortSignal) {
  return http
    .post<TaskSummary>(`/tasks/${encodeURIComponent(id)}/cancel`, undefined, {
      signal,
    })
    .then(({ data }) => data);
}
export function artifactContentUrl(id: string): string {
  return `/api/v1/artifacts/${encodeURIComponent(id)}/content`;
}
