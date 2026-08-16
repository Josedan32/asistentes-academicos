import { createElement } from "react";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useAuth } from "./useAuth";

function renderAuthHook(queryClient: QueryClient) {
  return renderHook(() => useAuth(), {
    wrapper: ({ children }) =>
      createElement(QueryClientProvider, { client: queryClient }, children),
  });
}

function mockLoginResponse() {
  (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
    new Response(
      JSON.stringify({ access_token: "tok", token_type: "bearer", role: "student" }),
      { status: 200 }
    )
  );
}

describe("useAuth", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("starts with no session when nothing is stored", () => {
    const { result } = renderAuthHook(new QueryClient());
    expect(result.current.session).toBeNull();
  });

  it("exposes the session after a successful login", async () => {
    mockLoginResponse();
    const { result } = renderAuthHook(new QueryClient());

    await act(async () => {
      await result.current.login("ana@pascualbravo.edu.co", "a-strong-password");
    });

    await waitFor(() => {
      expect(result.current.session).toEqual({ token: "tok", role: "student" });
    });
  });

  it("clears the session on logout", async () => {
    mockLoginResponse();
    const { result } = renderAuthHook(new QueryClient());
    await act(async () => {
      await result.current.login("ana@pascualbravo.edu.co", "a-strong-password");
    });

    act(() => {
      result.current.logout();
    });

    expect(result.current.session).toBeNull();
  });

  it("clears cached query data on logout, so the next login can't see it", async () => {
    mockLoginResponse();
    const queryClient = new QueryClient();
    queryClient.setQueryData(["conversations"], [{ id: 1, title: "chat de otro estudiante" }]);
    queryClient.setQueryData(["me"], { first_name: "Otro" });

    const { result } = renderAuthHook(queryClient);
    await act(async () => {
      await result.current.login("ana@pascualbravo.edu.co", "a-strong-password");
    });
    act(() => {
      result.current.logout();
    });

    expect(queryClient.getQueryData(["conversations"])).toBeUndefined();
    expect(queryClient.getQueryData(["me"])).toBeUndefined();
  });

  it("clears leftover cached query data on login too, in case a prior session never logged out", async () => {
    mockLoginResponse();
    const queryClient = new QueryClient();
    queryClient.setQueryData(["conversations"], [{ id: 1, title: "chat de otro estudiante" }]);

    const { result } = renderAuthHook(queryClient);
    await act(async () => {
      await result.current.login("ana@pascualbravo.edu.co", "a-strong-password");
    });

    expect(queryClient.getQueryData(["conversations"])).toBeUndefined();
  });
});
