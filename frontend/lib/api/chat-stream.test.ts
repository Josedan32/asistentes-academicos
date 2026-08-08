import { describe, expect, it } from "vitest";
import { parseSSEChunk } from "./chat-stream";

describe("parseSSEChunk", () => {
  it("parses a single complete event", () => {
    const { events, remainder } = parseSSEChunk('event: thinking\ndata: {"tool":"x"}\n\n');
    expect(events).toEqual([{ event: "thinking", data: { tool: "x" } }]);
    expect(remainder).toBe("");
  });

  it("parses multiple events delivered in one chunk", () => {
    const buffer =
      'event: token\ndata: {"text":"Hola"}\n\n' + 'event: token\ndata: {"text":" mundo"}\n\n';
    const { events, remainder } = parseSSEChunk(buffer);
    expect(events.map((e) => e.data.text)).toEqual(["Hola", " mundo"]);
    expect(remainder).toBe("");
  });

  it("carries an incomplete trailing event in the remainder", () => {
    const buffer = 'event: token\ndata: {"text":"Hola"}\n\n' + 'event: token\ndata: {"tex';
    const { events, remainder } = parseSSEChunk(buffer);
    expect(events).toHaveLength(1);
    expect(remainder).toBe('event: token\ndata: {"tex');
  });

  it("returns no events and the whole buffer as remainder when nothing is complete yet", () => {
    const { events, remainder } = parseSSEChunk('event: token\ndata: {"te');
    expect(events).toEqual([]);
    expect(remainder).toBe('event: token\ndata: {"te');
  });

  it("ignores blank segments", () => {
    const { events } = parseSSEChunk("\n\n" + 'event: done\ndata: {"tool_count":0}\n\n');
    expect(events).toHaveLength(1);
  });
});
