import { apiClient } from "../../api/client";
import type { TaskSummary } from "../../api/types";
import type { CreateEnhancementRequest } from "./types";

export function createEnhancement(request: CreateEnhancementRequest, signal?: AbortSignal) {
  return apiClient.requestJson<TaskSummary>("/enhancements", request, signal);
}
