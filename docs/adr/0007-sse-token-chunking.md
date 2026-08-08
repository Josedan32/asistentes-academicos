# 7. Stream `token` events by chunking a completed response

Status: accepted (2026-08-07)

## Context
The SSE contract (spec §9.2) documents `token*` as a sequence of incremental events, but
`LLMProvider.complete()` (spec §7.2) returns one finished `LLMResponse` — there is no
streaming method on the port. Adding one would mean every adapter, and the fake used for
loop tests, would need a second code path.

## Decision
The chat endpoint chunks the finished `DoneEvent.content` into word-sized pieces and
emits them as sequential `token` events after the loop completes. The `LLMProvider` port
stays single-call.

## Consequences
- The frontend's incremental "typing" UX is satisfied without a streaming provider method.
- This is safe because latency is not the bottleneck: the spike (ADR 0006) measured the
  1.9 GB Q4_K_M model at 100% GPU utilization, well within interactive range.
- If a future adapter offers true token streaming, this decision is revisited — nothing
  here forbids it, it simply was not needed to satisfy the contract.
