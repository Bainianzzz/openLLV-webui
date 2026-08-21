import { http } from "@/api/http";
import type { TaskSummary } from "@/types";
import type {
  CreateEnhancementRequest,
  EnhancementCatalog,
} from "@/types/enhancement";

export function getEnhancementCatalog(signal?: AbortSignal) {
  return http
    .get<EnhancementCatalog>("/catalog", { signal })
    .then(({ data }) => data);
}
export function createEnhancement(
  request: CreateEnhancementRequest,
  signal?: AbortSignal,
) {
  return http
    .post<TaskSummary>("/enhancements", request, { signal })
    .then(({ data }) => data);
}
