import type { DatasetDownloadTaskDetail, Page, TaskSummary } from "../../api/types";

export type DatasetStatus = "downloading" | "available" | "failed";

export interface Dataset {
  id: string;
  dataset_key: string;
  display_name: string;
  status: DatasetStatus;
  file_count: number | null;
  total_bytes: number | null;
  error_code: string | null;
  created_at: string;
  updated_at: string;
}

export type DatasetPage = Page<Dataset>;

export interface DatasetListParams {
  page?: number;
  page_size?: number;
  status?: DatasetStatus;
}

export interface CreateDatasetDownloadRequest {
  dataset_key: string;
  overwrite?: boolean;
}

export interface DatasetCatalogOption {
  name: string;
  aliases: string[];
}

export interface DatasetCatalog {
  datasets: DatasetCatalogOption[];
}

export type DatasetDownloadTask = Pick<TaskSummary, "id" | "kind" | "status" | "created_at"> & {
  kind: "dataset_download";
};

type DatasetDownloadJob = DatasetDownloadTaskDetail["job"] & {
  output_artifact_id: string | null;
};

export type DatasetDownloadTaskDetailResponse = Omit<DatasetDownloadTaskDetail, "job" | "dataset_download"> & {
  job?: DatasetDownloadJob;
  dataset_download?: DatasetDownloadJob;
};

export type DatasetDownloadTaskDetailView = Omit<DatasetDownloadTaskDetail, "job" | "dataset_download"> & {
  job: DatasetDownloadJob;
  dataset_download: DatasetDownloadJob;
};
