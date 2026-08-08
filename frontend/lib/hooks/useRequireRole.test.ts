import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useRequireRole } from "./useRequireRole";
import * as auth from "../api/auth";

const replace = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace }) }));

describe("useRequireRole", () => {
  beforeEach(() => {
    replace.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("redirects to /login when there is no session", () => {
    vi.spyOn(auth, "getStoredSession").mockReturnValue(null);
    renderHook(() => useRequireRole("student"));
    expect(replace).toHaveBeenCalledWith("/login");
  });

  it("redirects to /login when the role does not match", () => {
    vi.spyOn(auth, "getStoredSession").mockReturnValue({ token: "t", role: "coordination" });
    renderHook(() => useRequireRole("student"));
    expect(replace).toHaveBeenCalledWith("/login");
  });

  it("does not redirect when the role matches", () => {
    vi.spyOn(auth, "getStoredSession").mockReturnValue({ token: "t", role: "student" });
    renderHook(() => useRequireRole("student"));
    expect(replace).not.toHaveBeenCalled();
  });
});
