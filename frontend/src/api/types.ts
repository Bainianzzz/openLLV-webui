export type JsonObject = Record<string, unknown>;

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: unknown;
    request_id: string | null;
  };
}

export interface Page<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export type TaskKind = "enhancement" | "training" | "dataset_download";
export type TaskStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelling"
  | "cancelled";

export interface TaskSummary {
  id: string;
  kind: TaskKind;
  status: TaskStatus;
  message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface EnhancementTaskDetail extends TaskSummary {
  kind: "enhancement";
  job: {
    backend: "traditional" | "deep";
    method: string;
    input_artifact_id: string;
    checkpoint_artifact_id: string | null;
    params: JsonObject;
    device: string;
    output_artifact_id: string | null;
  };
  error_code: string | null;
  error_detail: string | null;
}

export interface TrainingTaskDetail extends TaskSummary {
  kind: "training";
  job: {
    model: string;
    dataset_id: string;
    hyperparameters: JsonObject;
    device: string;
    checkpoint_artifact_id: string | null;
    history: unknown[] | null;
    best_val_loss: number | null;
    swanlab_url: string | null;
  };
  error_code: string | null;
  error_detail: string | null;
}

export interface DatasetDownloadTaskDetail extends TaskSummary {
  kind: "dataset_download";
  job: {
    dataset_id: string | null;
    dataset_key: string;
    overwrite: boolean;
  };
  error_code: string | null;
  error_detail: string | null;
}

export type TaskDetail =
  | EnhancementTaskDetail
  | TrainingTaskDetail
  | DatasetDownloadTaskDetail;
