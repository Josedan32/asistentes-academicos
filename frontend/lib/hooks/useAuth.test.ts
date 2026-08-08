import { renderHook, waitFor, act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useAuth } from "./useAuth";

describe("useAuth", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("starts with no session when nothing is stored", () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.session).toBeNull();
  });

  it("exposes the session after a successful login", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(
        JSON.stringify({ access_token: "tok", token_type: "bearer", role: "student" }),
        { status: 200 }
      )
    );
    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.login("ana@pascualbravo.edu.co", "a-strong-password");
    });

    await waitFor(() => {
      expect(result.current.session).toEqual({ token: "tok", role: "student" });
    });
  });

  it("clears the session on logout", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(
        JSON.stringify({ access_token: "tok", token_type: "bearer", role: "student" }),
        { status: 200 }
      )
    );
    const { result } = renderHook(() => useAuth());
    await act(async () => {
      await result.current.login("ana@pascualbravo.edu.co", "a-strong-password");
    });

    act(() => {
      result.current.logout();
    });

    expect(result.current.session).toBeNull();
  });
});
