import type { TaskSummary } from "../../api/types";

export interface CatalogOption {
  name: string;
  aliases: string[];
}

export interface EnhancementCatalog {
  algorithms: CatalogOption[];
  models: CatalogOption[];
  devices: string[];
  forms?: {
    enhancement?: {
      traditional_params?: Record<string, { type: string; minimum?: number; default?: number }>;
    };
  };
}

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
