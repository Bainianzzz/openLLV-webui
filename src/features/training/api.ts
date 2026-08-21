import { apiClient } from "../../api/client";
import type { TaskSummary, TrainingTaskDetail } from "../../api/types";
import type { CreateTrainingRequest, DatasetPage, TrainingCatalog } from "./types";

export function getTrainingCatalog(signal?: AbortSignal) {
  return apiClient.request<TrainingCatalog>("/catalog", { signal });
}

export function listAvailableDatasets(signal?: AbortSignal) {
  return apiClient.request<DatasetPage>("/datasets?page=1&page_size=100&status=available", { signal });
}

export function createTraining(request: CreateTrainingRequest, signal?: AbortSignal) {
  return apiClient.requestJson<TaskSummary>("/trainings", request, signal);
}

type TrainingJob = TrainingTaskDetail["job"];
type TrainingDetailResponse = Omit<TrainingTaskDetail, "job"> & {
  job?: TrainingJob;
  training?: TrainingJob;
};

export async function getTrainingTask(id: string, signal?: AbortSignal): Promise<TrainingTaskDetail> {
  const detail = await apiClient.request<TrainingDetailResponse>(`/tasks/${encodeURIComponent(id)}`, { signal });
  const job = detail.job ?? detail.training;
  if (detail.kind !== "training" || !job) throw new Error("The submitted task is not a training task.");
  return { ...detail, kind: "training", job };
}
