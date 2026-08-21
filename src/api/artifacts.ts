import { http } from "@/api/http";
import type {
  Artifact,
  DirectoryListing,
  UploadImagesRequest,
} from "@/types/artifacts";

export function uploadImages(
  { files }: UploadImagesRequest,
  signal?: AbortSignal,
) {
  const form = new FormData();
  for (const file of files) form.append("files", file);
  return http
    .post<Artifact>("/artifacts/images", form, { signal })
    .then(({ data }) => data);
}
export function getArtifact(id: string, signal?: AbortSignal) {
  return http
    .get<Artifact>(`/artifacts/${encodeURIComponent(id)}`, { signal })
    .then(({ data }) => data);
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
    ? http.get<DirectoryListing>(path, { signal }).then(({ data }) => data)
    : http
        .get<Blob>(path, { responseType: "blob", signal })
        .then(({ data }) => data);
}
