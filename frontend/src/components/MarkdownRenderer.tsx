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
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown
            components={{
              h1: ({ children }) => <h1 className="text-2xl font-bold mb-4 text-foreground">{children}</h1>,
              h2: ({ children }) => <h2 className="text-xl font-semibold mb-3 text-foreground">{children}</h2>,
              h3: ({ children }) => <h3 className="text-lg font-medium mb-2 text-foreground">{children}</h3>,
              p: ({ children }) => <p className="mb-3 text-foreground">{children}</p>,
              ul: ({ children }) => <ul className="mb-3 ml-4 list-disc">{children}</ul>,
              ol: ({ children }) => <ol className="mb-3 ml-4 list-decimal">{children}</ol>,
              li: ({ children }) => <li className="mb-1">{children}</li>,
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              em: ({ children }) => <em className="italic">{children}</em>,
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  );
}