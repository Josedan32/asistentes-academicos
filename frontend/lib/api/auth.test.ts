import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getStoredSession, login, logout, register } from "./auth";

describe("auth", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("stores the token and role on successful login", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(
        JSON.stringify({ access_token: "tok", token_type: "bearer", role: "student" }),
        { status: 200 }
      )
    );

    await login("ana@pascualbravo.edu.co", "a-strong-password");

    const session = getStoredSession();
    expect(session).toEqual({ token: "tok", role: "student" });
  });

  it("returns null when nothing is stored", () => {
    expect(getStoredSession()).toBeNull();
  });

  it("clears the session on logout", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(
        JSON.stringify({ access_token: "tok", token_type: "bearer", role: "coordination" }),
        { status: 200 }
      )
    );
    await login("coord@pascualbravo.edu.co", "a-strong-password");

    logout();

    expect(getStoredSession()).toBeNull();
  });

  it("register stores the session exactly like login", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      new Response(
        JSON.stringify({ access_token: "tok2", token_type: "bearer", role: "student" }),
        { status: 201 }
      )
    );

    await register({
      email: "ana@pascualbravo.edu.co",
      password: "a-strong-password",
      first_name: "Ana",
      last_name: "Marin",
      document: "123",
      program_id: 1,
      current_semester: 5,
    });

    expect(getStoredSession()).toEqual({ token: "tok2", role: "student" });
  });
});
