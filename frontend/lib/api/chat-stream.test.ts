import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { parseSSEChunk, streamChat } from "./chat-stream";

function fakeStreamResponse(chunk: string): Response {
  const encoder = new TextEncoder();
  let sent = false;
  const body = new ReadableStream<Uint8Array>({
    pull(controller) {
      if (!sent) {
        controller.enqueue(encoder.encode(chunk));
        sent = true;
      } else {
        controller.close();
      }
    },
  });
  return new Response(body, { status: 200 });
}

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

describe("streamChat", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("yields to the browser between events instead of firing them all synchronously", async () => {
    const chunk =
      'event: token\ndata: {"text":"a"}\n\n' +
      'event: token\ndata: {"text":"b"}\n\n' +
      'event: token\ndata: {"text":"c"}\n\n';
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(fakeStreamResponse(chunk));

    const received: string[] = [];
    const streamPromise = streamChat(
      { conversation_id: null, course_id: null, message: "hola", mode: "consulta" },
      (event) => received.push(event.data.text),
      new AbortController().signal
    );

    await vi.advanceTimersByTimeAsync(0);
    expect(received.length).toBeGreaterThan(0);
    expect(received.length).toBeLessThan(3);

    await vi.runAllTimersAsync();
    await streamPromise;
    expect(received).toEqual(["a", "b", "c"]);
  });
});
