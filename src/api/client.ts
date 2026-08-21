import type { ApiErrorBody } from "./types";

const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;
  readonly requestId: string | null;

  constructor(status: number, body: ApiErrorBody | null, fallbackMessage: string) {
    const error = body?.error;
    super(error?.message ?? fallbackMessage);
    this.name = "ApiError";
    this.status = status;
    this.code = error?.code ?? "http_error";
    this.details = error?.details ?? null;
    this.requestId = error?.request_id ?? null;
  }
}

export interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: BodyInit | null;
}

async function readError(response: Response): Promise<ApiErrorBody | null> {
  try {
    const body: unknown = await response.json();
    if (
      typeof body === "object" &&
      body !== null &&
      "error" in body &&
      typeof body.error === "object" &&
      body.error !== null
    ) {
      return body as ApiErrorBody;
    }
  } catch {
    // The status code still provides a useful error when the body is not JSON.
  }
  return null;
}

export class ApiClient {
  constructor(private readonly baseUrl = API_PREFIX) {}

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const headers = new Headers(options.headers);
    const body = options.body;
    if (body !== undefined && body !== null && !(body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      body,
      headers,
    });
    if (!response.ok) {
      throw new ApiError(
        response.status,
        await readError(response),
        `Request failed with status ${response.status}`,
      );
    }
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }

  requestJson<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
    return this.request<T>(path, {
      method: "POST",
      body: JSON.stringify(body),
      signal,
    });
  }

  async requestBlob(path: string, signal?: AbortSignal): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}${path}`, { signal });
    if (!response.ok) {
      throw new ApiError(
        response.status,
        await readError(response),
        `Request failed with status ${response.status}`,
      );
    }
    return response.blob();
  }
}

export const apiClient = new ApiClient();
