'use client';

import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FileTextIcon } from 'lucide-react';

interface MarkdownRendererProps {
  content: string;
  characterCount: number;
  isUpdating: boolean;
  lastUpdate: string;
}

export function MarkdownRenderer({ 
  content, 
  characterCount, 
  isUpdating, 
  lastUpdate 
}: MarkdownRendererProps) {
  const [highlightedContent, setHighlightedContent] = useState(content);
  const [previousContent, setPreviousContent] = useState('');

  useEffect(() => {
    if (content !== previousContent) {
      // Simple diff highlighting - in a real app, you'd use a proper diff library
      const newParts = content.split('\n').slice(previousContent.split('\n').length);
      if (newParts.length > 0) {
        // Temporarily highlight new content
        const highlighted = content.replace(
          newParts.join('\n'),
          `<div class="bg-green-100 border-l-4 border-green-500 pl-4 animate-pulse">${newParts.join('\n')}</div>`
        );
        setHighlightedContent(highlighted);
        
        // Remove highlight after 3 seconds
        setTimeout(() => {
          setHighlightedContent(content);
        }, 3000);
      }
      setPreviousContent(content);
    }
  }, [content, previousContent]);

  if (!content) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center h-32 text-muted-foreground">
          <div className="text-center">
            <FileTextIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>Your travel plan will appear here...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <FileTextIcon className="h-5 w-5" />
            Travel Plan
            {isUpdating && (
              <Badge variant="outline" className="animate-pulse">
                Updating...
              </Badge>
            )}
          </CardTitle>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Badge variant="secondary">
              {characterCount.toLocaleString()} chars
            </Badge>
            <span>Updated: {lastUpdate}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="max-w-none text-sm leading-relaxed">
          <ReactMarkdown
            components={{
              h1: ({ children }) => (
                <h1 className="text-xl font-bold mb-4 text-foreground border-b border-border pb-2">
                  {children}
                </h1>
              ),
              h2: ({ children }) => (
                <h2 className="text-lg font-semibold mb-3 mt-6 text-foreground">
                  {children}
                </h2>
              ),
              h3: ({ children }) => (
                <h3 className="text-base font-medium mb-2 mt-4 text-foreground">
                  {children}
                </h3>
              ),
              h4: ({ children }) => (
                <h4 className="text-sm font-medium mb-2 mt-3 text-muted-foreground uppercase tracking-wide">
                  {children}
                </h4>
              ),
              p: ({ children }) => (
                <p className="mb-3 text-foreground leading-relaxed">
                  {children}
                </p>
              ),
              ul: ({ children }) => (
                <ul className="mb-4 ml-4 space-y-1 list-disc marker:text-muted-foreground">
                  {children}
                </ul>
              ),
              ol: ({ children }) => (
                <ol className="mb-4 ml-4 space-y-1 list-decimal marker:text-muted-foreground">
                  {children}
                </ol>
              ),
              li: ({ children }) => (
                <li className="text-foreground leading-relaxed pl-1">
                  {children}
                </li>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 border-blue-200 pl-4 py-2 mb-4 bg-blue-50/50 italic text-muted-foreground">
                  {children}
                </blockquote>
              ),
              code: ({ children, className }) => {
                const isInline = !className;
                if (isInline) {
                  return (
                    <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono text-foreground">
                      {children}
                    </code>
                  );
                }
                return (
                  <code className="block bg-muted p-3 rounded-md text-xs font-mono overflow-x-auto">
                    {children}
                  </code>
                );
              },
              pre: ({ children }) => (
                <pre className="mb-4 overflow-x-auto">
                  {children}
                </pre>
              ),
              table: ({ children }) => (
                <div className="overflow-x-auto mb-4">
                  <table className="min-w-full border-collapse border border-border text-xs">
                    {children}
                  </table>
                </div>
              ),
              thead: ({ children }) => (
                <thead className="bg-muted">
                  {children}
                </thead>
              ),
              tbody: ({ children }) => (
                <tbody>
                  {children}
                </tbody>
              ),
              tr: ({ children }) => (
                <tr className="border-b border-border">
                  {children}
                </tr>
              ),
              th: ({ children }) => (
                <th className="border border-border px-3 py-2 text-left font-medium">
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className="border border-border px-3 py-2">
                  {children}
                </td>
              ),
              hr: () => (
                <hr className="my-6 border-border" />
              ),
              strong: ({ children }) => (
                <strong className="font-semibold text-foreground">
                  {children}
                </strong>
              ),
              em: ({ children }) => (
                <em className="italic text-foreground">
                  {children}
                </em>
              ),
              a: ({ children, href }) => (
                <a 
                  href={href} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline decoration-blue-300 underline-offset-2 transition-colors font-medium"
                >
                  {children}
                </a>
              ),
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  );
}