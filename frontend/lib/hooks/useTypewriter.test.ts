import { renderHook } from "@testing-library/react";
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useTypewriter } from "./useTypewriter";

describe("useTypewriter", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns the full text immediately when not active", () => {
    const { result } = renderHook(() => useTypewriter("Hola mundo", false));
    expect(result.current).toBe("Hola mundo");
  });

  it("reveals the text progressively while active", () => {
    const { result, rerender } = renderHook(
      ({ target, active }) => useTypewriter(target, active),
      { initialProps: { target: "Hola mundo", active: true } }
    );
    expect(result.current).toBe("");

    act(() => {
      vi.advanceTimersByTime(32);
    });
    rerender({ target: "Hola mundo", active: true });

    expect(result.current.length).toBeGreaterThan(0);
    expect(result.current.length).toBeLessThan("Hola mundo".length);
  });

  it("catches up to the full text eventually while active", () => {
    const { result, rerender } = renderHook(
      ({ target, active }) => useTypewriter(target, active),
      { initialProps: { target: "Hola", active: true } }
    );

    act(() => {
      vi.advanceTimersByTime(1000);
    });
    rerender({ target: "Hola", active: true });

    expect(result.current).toBe("Hola");
  });

  it("snaps to the full text once active turns false", () => {
    const { result, rerender } = renderHook(
      ({ target, active }) => useTypewriter(target, active),
      { initialProps: { target: "Hola mundo", active: true } }
    );
    act(() => {
      vi.advanceTimersByTime(16);
    });

    rerender({ target: "Hola mundo", active: false });

    expect(result.current).toBe("Hola mundo");
  });
});
