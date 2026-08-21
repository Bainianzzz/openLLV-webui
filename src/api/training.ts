import { http } from "@/api/http";
import type { TaskSummary, TrainingTaskDetail } from "@/types";
import type {
  CreateTrainingRequest,
  DatasetPage,
  TrainingCatalog,
} from "@/types/training";

export function getTrainingCatalog(signal?: AbortSignal) {
  return http
    .get<TrainingCatalog>("/catalog", { signal })
    .then(({ data }) => data);
}
export function listAvailableDatasets(signal?: AbortSignal) {
  return http
    .get<DatasetPage>("/datasets?page=1&page_size=100&status=available", {
      signal,
    })
    .then(({ data }) => data);
}
export function createTraining(
  request: CreateTrainingRequest,
  signal?: AbortSignal,
) {
  return http
    .post<TaskSummary>("/trainings", request, { signal })
    .then(({ data }) => data);
}
type TrainingJob = TrainingTaskDetail["job"];
type TrainingDetailResponse = Omit<TrainingTaskDetail, "job"> & {
  job?: TrainingJob;
  training?: TrainingJob;
};
export async function getTrainingTask(
  id: string,
  signal?: AbortSignal,
): Promise<TrainingTaskDetail> {
  const { data: detail } = await http.get<TrainingDetailResponse>(
    `/tasks/${encodeURIComponent(id)}`,
    { signal },
  );
  const job = detail.job ?? detail.training;
  if (detail.kind !== "training" || !job)
    throw new Error("The submitted task is not a training task.");
  return { ...detail, kind: "training", job };
}
