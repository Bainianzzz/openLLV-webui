import type { Page, TaskSummary } from "../../api/types";

export interface CatalogOption {
  name: string;
  aliases: string[];
}

export interface TrainingCatalog {
  models: CatalogOption[];
  devices: string[];
}

export interface Dataset {
  id: string;
  dataset_key: string;
  display_name: string;
  status: "downloading" | "available" | "failed";
  file_count: number | null;
  total_bytes: number | null;
  error_code: string | null;
  created_at: string;
  updated_at: string;
}

export type DatasetPage = Page<Dataset>;

export interface SwanLabOptions {
  project: string;
  experiment: string;
}

export interface CreateTrainingRequest {
  model: string;
  dataset_id: string;
  epochs: number;
  batch_size: number;
  lr: number;
  resize: number | number[];
  device?: string;
  num_workers?: 0;
  swanlab?: SwanLabOptions;
}

export type TrainingTask = Pick<TaskSummary, "id" | "kind" | "status" | "created_at"> & {
  kind: "training";
};
