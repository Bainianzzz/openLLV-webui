import { http } from "@/api/http";
import type { Page, TaskSummary } from "@/types";
import type {
  CreateDatasetDownloadRequest,
  Dataset,
  DatasetCatalog,
  DatasetDownloadTaskDetailResponse,
  DatasetDownloadTaskDetailView,
  DatasetListParams,
} from "@/types/datasets";

function query(params: DatasetListParams): string {
  const values = new URLSearchParams();
  for (const [key, value] of Object.entries(params))
    if (value !== undefined) values.set(key, String(value));
  const encoded = values.toString();
  return encoded ? `?${encoded}` : "";
}
export function listDatasets(
  params: DatasetListParams = {},
  signal?: AbortSignal,
) {
  return http
    .get<Page<Dataset>>(`/datasets${query(params)}`, { signal })
    .then(({ data }) => data);
}
export function createDatasetDownload(
  request: CreateDatasetDownloadRequest,
  signal?: AbortSignal,
) {
  return http
    .post<TaskSummary>("/datasets/downloads", request, { signal })
    .then(({ data }) => data);
}
export function getDatasetCatalog(signal?: AbortSignal) {
  return http
    .get<DatasetCatalog>("/catalog", { signal })
    .then(({ data }) => data);
}
export async function getDatasetDownloadTask(
  id: string,
  signal?: AbortSignal,
): Promise<DatasetDownloadTaskDetailView> {
  const { data: detail } = await http.get<DatasetDownloadTaskDetailResponse>(
    `/tasks/${encodeURIComponent(id)}`,
    { signal },
  );
  const job = detail.job ?? detail.dataset_download;
  if (detail.kind !== "dataset_download" || !job)
    throw new Error("The submitted task is not a dataset download task.");
  return { ...detail, kind: "dataset_download", job, dataset_download: job };
}
