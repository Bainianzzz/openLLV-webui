import { apiClient } from "../../api/client";
import type { Artifact, DirectoryListing, UploadImagesRequest } from "./types";

export function uploadImages({ files }: UploadImagesRequest, signal?: AbortSignal) {
  const form = new FormData();
  for (const file of files) form.append("files", file);
  return apiClient.request<Artifact>("/artifacts/images", { method: "POST", body: form, signal });
}

export function getArtifact(id: string, signal?: AbortSignal) {
  return apiClient.request<Artifact>(`/artifacts/${encodeURIComponent(id)}`, { signal });
}

export function getArtifactContent(
  id: string,
  pathType: "directory",
  signal?: AbortSignal,
): Promise<DirectoryListing>;
export function getArtifactContent(
  id: string,
  pathType: "file",
  signal?: AbortSignal,
): Promise<Blob>;
export function getArtifactContent(
  id: string,
  pathType: Artifact["path_type"],
  signal?: AbortSignal,
): Promise<Blob | DirectoryListing> {
  const path = `/artifacts/${encodeURIComponent(id)}/content`;
  return pathType === "directory"
    ? apiClient.request<DirectoryListing>(path, { signal })
    : apiClient.requestBlob(path, signal);
}
