import { apiClient } from "../../api/client";
import type { Artifact, UploadImagesRequest } from "./types";

export function uploadImages({ files }: UploadImagesRequest, signal?: AbortSignal) {
  const form = new FormData();
  for (const file of files) form.append("files", file);
  return apiClient.request<Artifact>("/artifacts/images", { method: "POST", body: form, signal });
}

export function getArtifact(id: string, signal?: AbortSignal) {
  return apiClient.request<Artifact>(`/artifacts/${encodeURIComponent(id)}`, { signal });
}

export function getArtifactContent(id: string, signal?: AbortSignal) {
  return apiClient.requestBlob(`/artifacts/${encodeURIComponent(id)}/content`, signal);
}
