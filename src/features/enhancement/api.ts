import { apiClient } from "../../api/client";
import type { TaskSummary } from "../../api/types";
import type { CreateEnhancementRequest } from "./types";
import type { EnhancementCatalog } from "./types";

export function getEnhancementCatalog(signal?: AbortSignal) {
  return apiClient.request<EnhancementCatalog>("/catalog", { signal });
}

export function createEnhancement(request: CreateEnhancementRequest, signal?: AbortSignal) {
  return apiClient.requestJson<TaskSummary>("/enhancements", request, signal);
}
