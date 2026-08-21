export interface Artifact {
  id: string;
  kind: "image" | "output" | "checkpoint" | "dataset";
  path_type: "file" | "directory";
  display_name: string;
  content_url: string;
}
export interface DirectoryItem {
  display_name: string;
}
export interface DirectoryListing {
  items: DirectoryItem[];
}
export interface UploadImagesRequest {
  files: File[];
}
