import { describe, expect, it } from "vitest";
import { relativeDate } from "./relative-date";

describe("relativeDate", () => {
  const now = new Date("2026-08-08T12:00:00Z");

  it("says hoy for the same calendar day", () => {
    expect(relativeDate("2026-08-08T09:00:00Z", now)).toBe("hoy");
  });

  it("says ayer for the previous calendar day", () => {
    expect(relativeDate("2026-08-07T23:00:00Z", now)).toBe("ayer");
  });

  it("says N días for anything older", () => {
    expect(relativeDate("2026-08-03T09:00:00Z", now)).toBe("5 días");
  });
});
