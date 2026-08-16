import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import { normalizeLatexDelimiters } from "@/lib/normalize-latex-delimiters";

const KATEX_OPTIONS = { throwOnError: false, errorColor: "#7D6A2E", strict: false as const };

export function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="flex flex-col gap-2 text-[15.5px] leading-[1.65] text-text-body
                    [&_.katex-display]:my-1 [&_.katex-display]:overflow-x-auto
                    [&_.katex-display]:overflow-y-hidden [&_.katex-display]:rounded-[8px]
                    [&_.katex-display]:border [&_.katex-display]:border-border-control
                    [&_.katex-display]:bg-tool-bg [&_.katex-display]:px-4
                    [&_.katex-display]:py-[10px]">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[[rehypeKatex, KATEX_OPTIONS]]}
        components={{
          h1: ({ children }) => (
            <h2 className="m-0 mt-2 text-[18px] font-semibold text-navy first:mt-0">
              {children}
            </h2>
          ),
          h2: ({ children }) => (
            <h2 className="m-0 mt-2 text-[17px] font-semibold text-navy first:mt-0">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="m-0 mt-1 text-[15.5px] font-semibold text-navy first:mt-0">
              {children}
            </h3>
          ),
          p: ({ children }) => <p className="m-0">{children}</p>,
          strong: ({ children }) => <strong className="font-semibold text-navy">{children}</strong>,
          ul: ({ children }) => (
            <ul className="m-0 flex flex-col gap-1 pl-5 [list-style-type:disc]">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="m-0 flex flex-col gap-1 pl-5 [list-style-type:decimal]">{children}</ol>
          ),
          li: ({ children }) => <li className="pl-1">{children}</li>,
          a: ({ children, href }) => (
            <a href={href} target="_blank" rel="noreferrer" className="text-accent underline">
              {children}
            </a>
          ),
          blockquote: ({ children }) => (
            <div className="rounded-[8px] border-l-[3px] border-accent bg-tool-bg py-2 pl-3 pr-2">
              {children}
            </div>
          ),
          code: ({ children }) => (
            <code className="rounded bg-[#F5F7F9] px-1 py-[1px] font-mono text-[13.5px]">
              {children}
            </code>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto">
              <table className="my-1 border-collapse text-[14px]">{children}</table>
            </div>
          ),
          th: ({ children }) => (
            <th className="border border-border px-2 py-1 text-left font-semibold text-navy">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-border px-2 py-1">{children}</td>
          ),
        }}
      >
        {normalizeLatexDelimiters(content)}
      </ReactMarkdown>
    </div>
  );
}
