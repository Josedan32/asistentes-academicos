import { describe, expect, it } from "vitest";
import { computeDragMove } from "./compute-drag-move";
import type { DragEndEvent } from "@dnd-kit/core";

function fakeEvent(activeId: number | string, overId: string | null): DragEndEvent {
  return {
    active: { id: activeId, data: { current: undefined }, rect: { current: { initial: null, translated: null } } },
    over: overId ? { id: overId, rect: {} as DOMRect, data: { current: undefined }, disabled: false } : null,
    collisions: null, delta: { x: 0, y: 0 }, activatorEvent: new Event("pointerdown"),
  } as unknown as DragEndEvent;
}

describe("computeDragMove", () => {
  it("extracts the course id and target semester from a valid drop", () => {
    expect(computeDragMove(fakeEvent(42, "semester-6"))).toEqual({ courseId: 42, newSemester: 6 });
  });

  it("returns null when dropped outside any droppable", () => {
    expect(computeDragMove(fakeEvent(42, null))).toBeNull();
  });

  it("returns null when the drop target id doesn't parse as a semester", () => {
    expect(computeDragMove(fakeEvent(42, "something-else"))).toBeNull();
  });
});
