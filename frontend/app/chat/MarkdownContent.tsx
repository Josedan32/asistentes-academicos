import ReactMarkdown from "react-markdown";

/** Renders the assistant's response as structured Markdown instead of raw text — the model
 * naturally answers with **bold** terms and numbered/bulleted lists, and showing that markup
 * literally (asterisks, no line breaks) reads as broken. Every element maps to the bubble's
 * own typography (15.5px/1.65, text-body) so headings/lists don't clash with the design. */
export function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="flex flex-col gap-2 text-[15.5px] leading-[1.65] text-text-body">
      <ReactMarkdown
        components={{
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
          code: ({ children }) => (
            <code className="rounded bg-[#F5F7F9] px-1 py-[1px] font-mono text-[13.5px]">
              {children}
            </code>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
