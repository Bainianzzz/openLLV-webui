import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiClient, ApiError } from "./client";

afterEach(() => vi.unstubAllGlobals());

describe("ApiClient", () => {
  it("preserves structured API errors and falls back for non-JSON errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn()
        .mockResolvedValueOnce(
          new Response(
            JSON.stringify({
              error: { code: "bad_input", message: "Invalid input", details: { field: "name" }, request_id: "req-1" },
            }),
            { status: 400, headers: { "Content-Type": "application/json" } },
          ),
        )
        .mockResolvedValueOnce(new Response("not JSON", { status: 502 })),
    );
    const client = new ApiClient("/api");

    await expect(client.request("/one")).rejects.toMatchObject({
      name: "ApiError",
      status: 400,
      code: "bad_input",
      message: "Invalid input",
      details: { field: "name" },
      requestId: "req-1",
    });
    await expect(client.request("/two")).rejects.toMatchObject({
      status: 502,
      code: "http_error",
      message: "Request failed with status 502",
    });
  });

  it("sends JSON requests and returns JSON or undefined for 204 responses", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ ok: true }), { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);
    const client = new ApiClient();

    await expect(client.requestJson("/tasks", { name: "demo" })).resolves.toEqual({ ok: true });
    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/tasks");
    expect(fetchMock.mock.calls[0]?.[1]).toMatchObject({ method: "POST", body: JSON.stringify({ name: "demo" }) });
    expect((fetchMock.mock.calls[0]?.[1] as RequestInit).headers).toBeInstanceOf(Headers);
    await expect(client.request("/tasks/1", { method: "DELETE" })).resolves.toBeUndefined();
  });
});
