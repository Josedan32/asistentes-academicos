import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, ApiError } from "./client";

describe("apiFetch", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("attaches the stored bearer token", async () => {
    localStorage.setItem("pb_token", "abc123");
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200 })
    );

    await apiFetch("/api/v1/me");

    const [, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect((options.headers as Headers).get("Authorization")).toBe("Bearer abc123");
  });

  it("omits Authorization when no token is stored", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({}), { status: 200 })
    );

    await apiFetch("/api/v1/programs");

    const [, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect((options.headers as Headers).has("Authorization")).toBe(false);
  });

  it("throws ApiError carrying the backend's detail message", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({ detail: "Invalid credentials" }), { status: 401 })
    );

    await expect(apiFetch("/api/v1/auth/login")).rejects.toMatchObject({
      status: 401,
      detail: "Invalid credentials",
    });
    await expect(apiFetch("/api/v1/auth/login")).rejects.toBeInstanceOf(ApiError);
  });

  it("resolves with the parsed JSON body on success", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(JSON.stringify({ id: 1 }), { status: 200 })
    );

    const result = await apiFetch<{ id: number }>("/api/v1/me");

    expect(result.id).toBe(1);
  });
});
