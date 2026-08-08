import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useChatStream } from "./useChatStream";

function fakeStreamResponse(chunks: string[]): Response {
  const encoder = new TextEncoder();
  let index = 0;
  const body = new ReadableStream<Uint8Array>({
    pull(controller) {
      if (index < chunks.length) {
        controller.enqueue(encoder.encode(chunks[index]));
        index += 1;
      } else {
        controller.close();
      }
    },
  });
  return new Response(body, { status: 200 });
}

describe("useChatStream", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("starts idle with no messages", () => {
    const { result } = renderHook(() => useChatStream(null));
    expect(result.current.runState).toBe("idle");
    expect(result.current.messages).toEqual([]);
  });

  it("walks queued -> loading_model -> thinking -> tool_call -> token -> done", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      fakeStreamResponse([
        'event: queued\ndata: {"position":2,"estimated_wait":10}\n\n',
        "event: loading_model\ndata: {}\n\n",
        'event: thinking\ndata: {"tool":"get_prerequisites"}\n\n',
        'event: tool_call\ndata: {"name":"get_prerequisites","arguments":{},"result":[],' +
          '"duration_ms":42,"row_count":0}\n\n',
        'event: token\ndata: {"text":"Hola"}\n\n',
        'event: done\ndata: {"tool_count":1,"total_ms":100,"source_count":1,' +
          '"conversation_id":7,"message_id":55}\n\n',
      ])
    );
    const { result } = renderHook(() => useChatStream(null));

    await act(async () => {
      await result.current.send("hola");
    });

    await waitFor(() => expect(result.current.runState).toBe("idle"));
    expect(result.current.conversationId).toBe(7);
    const assistantMessage = result.current.messages.find((m) => m.role === "assistant");
    expect(assistantMessage?.id).toBe(55);
    expect(assistantMessage?.content).toBe("Hola");
    expect(assistantMessage?.toolCalls).toHaveLength(1);
    expect(assistantMessage?.toolCalls[0].name).toBe("get_prerequisites");
  });

  it("surfaces an error event without throwing", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      fakeStreamResponse([
        'event: error\ndata: {"code":"queue_timeout","message":"Timed out"}\n\n',
      ])
    );
    const { result } = renderHook(() => useChatStream(null));

    await act(async () => {
      await result.current.send("hola");
    });

    await waitFor(() => expect(result.current.runState).toBe("error"));
    expect(result.current.errorInfo).toEqual({ code: "queue_timeout", message: "Timed out" });
  });

  it("stop() aborts the in-flight stream and returns to idle", async () => {
    let releaseController: (() => void) | null = null;
    (fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (_url: string, options: RequestInit) =>
        new Promise((resolve, reject) => {
          releaseController = () => reject(new DOMException("Aborted", "AbortError"));
          options.signal?.addEventListener("abort", () => releaseController?.());
        })
    );
    const { result } = renderHook(() => useChatStream(null));

    let sendPromise: Promise<void>;
    act(() => {
      sendPromise = result.current.send("hola");
    });
    await waitFor(() => expect(result.current.runState).toBe("thinking"));

    act(() => {
      result.current.stop();
    });
    await act(async () => {
      await sendPromise;
    });

    expect(result.current.runState).toBe("idle");
  });

  it("reset() clears the conversation for a fresh start", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      fakeStreamResponse([
        'event: token\ndata: {"text":"Hola"}\n\n',
        'event: done\ndata: {"tool_count":0,"total_ms":0,"source_count":0,' +
          '"conversation_id":3,"message_id":9}\n\n',
      ])
    );
    const { result } = renderHook(() => useChatStream(null));
    await act(async () => {
      await result.current.send("hola");
    });
    await waitFor(() => expect(result.current.conversationId).toBe(3));

    act(() => {
      result.current.reset();
    });

    expect(result.current.conversationId).toBeNull();
    expect(result.current.messages).toEqual([]);
  });

  it("ignores a second send() while the first is still in flight", async () => {
    let releaseController: (() => void) | null = null;
    (fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (_url: string, options: RequestInit) =>
        new Promise((resolve, reject) => {
          releaseController = () => reject(new DOMException("Aborted", "AbortError"));
          options.signal?.addEventListener("abort", () => releaseController?.());
        })
    );
    const { result } = renderHook(() => useChatStream(null));

    let firstSend: Promise<void>;
    act(() => {
      firstSend = result.current.send("primera");
    });
    await waitFor(() => expect(result.current.runState).toBe("thinking"));

    // A second call while the first is still unresolved — e.g. the student typing again
    // before the model responds — must not create a second user/assistant message pair.
    await act(async () => {
      await result.current.send("segunda, mientras la primera sigue en curso");
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].content).toBe("primera");

    act(() => {
      result.current.stop();
    });
    await act(async () => {
      await firstSend;
    });
  });

  it("allows a new send() once the previous one has finished", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      fakeStreamResponse([
        'event: token\ndata: {"text":"ok"}\n\n',
        'event: done\ndata: {"tool_count":0,"total_ms":0,"source_count":0,' +
          '"conversation_id":1,"message_id":1}\n\n',
      ])
    );
    const { result } = renderHook(() => useChatStream(null));

    await act(async () => {
      await result.current.send("primera");
    });
    await waitFor(() => expect(result.current.runState).toBe("idle"));

    await act(async () => {
      await result.current.send("segunda");
    });

    expect(result.current.messages).toHaveLength(4);
  });

  it("clearError() returns to idle without discarding message history", async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      fakeStreamResponse(['event: error\ndata: {"code":"x","message":"boom"}\n\n'])
    );
    const { result } = renderHook(() => useChatStream(null));
    await act(async () => {
      await result.current.send("hola");
    });
    await waitFor(() => expect(result.current.runState).toBe("error"));

    act(() => {
      result.current.clearError();
    });

    expect(result.current.runState).toBe("idle");
    expect(result.current.errorInfo).toBeNull();
    expect(result.current.messages).toHaveLength(2); // the user turn + the empty assistant turn
  });
});
