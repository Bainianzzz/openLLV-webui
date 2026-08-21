import { apiClient } from "../../api/client";
import type { Page, TaskSummary } from "../../api/types";
import type {
  CreateDatasetDownloadRequest,
  Dataset,
  DatasetCatalog,
  DatasetDownloadTaskDetailResponse,
  DatasetDownloadTaskDetailView,
  DatasetListParams,
} from "./types";

function query(params: DatasetListParams): string {
  const values = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) values.set(key, String(value));
  }
  const encoded = values.toString();
  return encoded ? `?${encoded}` : "";
}

export function listDatasets(params: DatasetListParams = {}, signal?: AbortSignal) {
  return apiClient.request<Page<Dataset>>(`/datasets${query(params)}`, { signal });
}

export function createDatasetDownload(request: CreateDatasetDownloadRequest, signal?: AbortSignal) {
  return apiClient.requestJson<TaskSummary>("/datasets/downloads", request, signal);
}

export function getDatasetCatalog(signal?: AbortSignal) {
  return apiClient.request<DatasetCatalog>("/catalog", { signal });
}

export async function getDatasetDownloadTask(
  id: string,
  signal?: AbortSignal,
): Promise<DatasetDownloadTaskDetailView> {
  const detail = await apiClient.request<DatasetDownloadTaskDetailResponse>(
    `/tasks/${encodeURIComponent(id)}`,
    { signal },
  );
  const job = detail.job ?? detail.dataset_download;
  if (detail.kind !== "dataset_download" || !job) {
    throw new Error("The submitted task is not a dataset download task.");
  }
  return { ...detail, kind: "dataset_download", job, dataset_download: job };
}
