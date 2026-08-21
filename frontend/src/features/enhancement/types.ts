import type { TaskSummary } from "../../api/types";

export interface CreateEnhancementRequest {
  backend: "traditional" | "deep";
  method: string;
  input_artifact_id: string;
  checkpoint_artifact_id?: string | null;
  params?: Record<string, unknown>;
  device?: string;
}

export type EnhancementTask = Pick<TaskSummary, "id" | "kind" | "status" | "created_at"> & {
  kind: "enhancement";
};
