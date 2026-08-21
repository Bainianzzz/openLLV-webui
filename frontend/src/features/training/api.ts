import { apiClient } from "../../api/client";
import type { TaskSummary } from "../../api/types";
import type { CreateTrainingRequest } from "./types";

export function createTraining(request: CreateTrainingRequest, signal?: AbortSignal) {
  return apiClient.requestJson<TaskSummary>("/trainings", request, signal);
}
