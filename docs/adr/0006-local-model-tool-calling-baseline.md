# 6. Local model tool-calling baseline

Status: accepted (2026-08-07)

## Context
`backend/scripts/spike_tool_calling.py` probes whether the local model can be
trusted to pick the right tool for a student's question, before Plan 2 builds the
agent loop on top of it. The spec itself warns that small models degrade as the
number of available tools grows.

The probe ran on the development machine: a GTX 1650 Ti with 4 GB of VRAM, with
`qwen2.5:3b` served by Ollama at 100% GPU utilization. It defines two tools
(`list_semester_courses`, `get_prerequisites`) and 5 questions, each sent 3 times
(15 invocations total). The design ships four tools
(`list_semester_courses`, `get_prerequisites`, `get_course_detail`,
`find_course_in_programs`). The probe is therefore a two-tool measurement, not a
like-for-like baseline of the shipped configuration.

## Decision
47% (7/15) stands as the recorded tool-selection accuracy baseline for the
two-tool probe. It was measured twice independently, with identical
case-by-case results both times. The figure must not be re-tuned or averaged
away; if the tool set or prompting changes, that is measured as a separate,
distinctly recorded figure rather than folded into this one.

## Consequences
- The failure mode observed is abstention (the model answers without calling a
  tool), never wrong-tool selection: 0 wrong tool selections across 30
  invocations spanning both runs.
- Precision on the calls the model did make is 100%; coverage is 47%.
- 47% is an upper bound for the four-tool configuration the design ships, not an
  estimate of it. Small models are expected to do no better as tool count grows,
  per the spec's own warning.
- Ollama returns tool call arguments as a JSON object, not a string, unlike the
  OpenAI wire format. Plan 2's adapter must not `json.loads` the result.
