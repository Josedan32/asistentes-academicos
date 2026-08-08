import { describe, expect, it } from "vitest";
import { robotStateFor } from "./robot-state";

describe("robotStateFor", () => {
  it("maps every run state to a robot avatar state", () => {
    expect(robotStateFor("idle")).toBe("waiting");
    expect(robotStateFor("queued")).toBe("waiting");
    expect(robotStateFor("loading_model")).toBe("loading");
    expect(robotStateFor("thinking")).toBe("searching");
    expect(robotStateFor("streaming")).toBe("thinking");
    expect(robotStateFor("error")).toBe("error");
  });
});
