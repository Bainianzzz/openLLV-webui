import type { TaskSummary } from "../../api/types";

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
  swanlab?: SwanLabOptions;
}

export type TrainingTask = Pick<TaskSummary, "id" | "kind" | "status" | "created_at"> & {
  kind: "training";
};
