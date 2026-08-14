/** The model is told to wrap math in `$...$` / `$$...$$` (what remark-math understands), but
 * qwen2.5:3b keeps defaulting to LaTeX's other inline/block delimiters, `\(...\)` and
 * `\[...\]`, regardless. Markdown then silently eats the backslash as an escape character,
 * leaving bare unrendered `(...)` / `[...]` in the bubble. Normalizing both conventions to
 * the one remark-math actually parses is far more reliable than prompt wording alone. */
export function normalizeLatexDelimiters(content: string): string {
  return content
    .replace(/\\\[/g, () => "$$")
    .replace(/\\\]/g, () => "$$")
    .replace(/\\\(/g, () => "$")
    .replace(/\\\)/g, () => "$");
}
