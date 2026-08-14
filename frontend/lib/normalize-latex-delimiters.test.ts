import { describe, expect, it } from "vitest";
import { normalizeLatexDelimiters } from "./normalize-latex-delimiters";

describe("normalizeLatexDelimiters", () => {
  it("converts \\( \\) into single dollar signs", () => {
    expect(normalizeLatexDelimiters("el conjunto \\(\\mathbb{R}^n\\) con...")).toBe(
      "el conjunto $\\mathbb{R}^n$ con..."
    );
  });

  it("converts \\[ \\] into double dollar signs", () => {
    expect(normalizeLatexDelimiters("\\[u + v = a + b\\]")).toBe("$$u + v = a + b$$");
  });

  it("leaves plain text without LaTeX delimiters untouched", () => {
    expect(normalizeLatexDelimiters("hola, esto no tiene formulas")).toBe(
      "hola, esto no tiene formulas"
    );
  });

  it("leaves already-correct $...$ delimiters untouched", () => {
    expect(normalizeLatexDelimiters("el conjunto $\\mathbb{R}^n$")).toBe(
      "el conjunto $\\mathbb{R}^n$"
    );
  });
});
