import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ReactNode } from 'react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h1 className="text-xl font-bold mb-3 mt-4">{children}</h1>,
          h2: ({ children }) => <h2 className="text-lg font-bold mb-2 mt-3">{children}</h2>,
          h3: ({ children }) => <h3 className="text-base font-bold mb-2 mt-2">{children}</h3>,
          h4: ({ children }) => <h4 className="font-bold mb-2">{children}</h4>,
          h5: ({ children }) => <h5 className="font-bold mb-1">{children}</h5>,
          h6: ({ children }) => <h6 className="font-bold mb-1">{children}</h6>,
          p: ({ children }) => <p className="mb-2">{children}</p>,
          strong: ({ children }) => <strong className="font-bold text-foreground">{children}</strong>,
          em: ({ children }) => <em className="italic">{children}</em>,
          code: ({ children, inline }: any) =>
            inline ? (
              <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono">{children}</code>
            ) : (
              <code className="block bg-muted p-2 rounded text-sm font-mono overflow-x-auto mb-2">{children}</code>
            ),
          pre: ({ children }) => (
            <pre className="bg-muted p-3 rounded mb-2 overflow-x-auto text-sm">{children}</pre>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-primary/30 pl-3 py-1 my-2 opacity-80">{children}</blockquote>
          ),
          ul: ({ children }) => <ul className="list-disc list-inside ml-2 mb-2 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal list-inside ml-2 mb-2 space-y-1">{children}</ol>,
          li: ({ children }) => <li className="ml-2">{children as ReactNode}</li>,
          a: ({ children, href }) => (
            <a href={href} className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          ),
          table: ({ children }) => (
            <table className="border-collapse w-full my-2">{children}</table>
          ),
          thead: ({ children }) => <thead className="bg-muted">{children}</thead>,
          tbody: ({ children }) => <tbody>{children}</tbody>,
          tr: ({ children }) => <tr className="border border-border/40">{children}</tr>,
          th: ({ children }) => <th className="border border-border/40 p-2 text-left font-semibold">{children}</th>,
          td: ({ children }) => <td className="border border-border/40 p-2">{children}</td>,
          hr: () => <hr className="my-3 border-border/40" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
