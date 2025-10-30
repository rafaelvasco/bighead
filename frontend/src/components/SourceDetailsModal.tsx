import { useState } from 'react';
import { ArrowUpRight, ChevronDown, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import type { ChatMessage } from '../types/document';

interface SourceDetailsModalProps {
  message: ChatMessage;
  onClose: () => void;
  onSourceJump: (lineStart: number, lineEnd: number) => void;
  initialSourceIndex?: number;
}

interface SourceExpandedState {
  [key: number]: boolean;
}

export function SourceDetailsModal({
  message,
  onClose,
  onSourceJump,
  initialSourceIndex = 0,
}: SourceDetailsModalProps) {
  const [expandedSources, setExpandedSources] = useState<SourceExpandedState>({
    [initialSourceIndex]: true,
  });

  if (!message.sources || message.sources.length === 0) {
    return null;
  }

  // Sort sources by relevance score (descending)
  const sortedSources = message.sources
    .map((source, idx) => ({ source, originalIdx: idx }))
    .sort((a, b) => (b.source.relevance_score ?? 0) - (a.source.relevance_score ?? 0));

  const toggleSourceExpanded = (idx: number) => {
    setExpandedSources((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const relevancePercentage = (score: number | undefined) =>
    Math.round((score ?? 0) * 100);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col bg-background">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div>
            <h2 className="text-lg font-semibold">Sources ({message.sources.length})</h2>
            <p className="text-sm text-muted-foreground">
              Most relevant sources from the document
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Sources List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {sortedSources.map(({ source, originalIdx }, displayIdx) => {
            const isExpanded = expandedSources[originalIdx];

            return (
              <Card
                key={originalIdx}
                className={`overflow-hidden bg-muted/30 border-border/50 transition-opacity ${
                  displayIdx === 0 ? 'border-primary/30 bg-primary/5' : ''
                }`}
              >
                {/* Header with reference and relevance score */}
                <div className="px-3 py-2 border-b border-border/40 bg-muted/50">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs font-mono text-muted-foreground">
                      {source.reference}
                    </p>
                    {source.relevance_score !== undefined && (
                      <span className="text-xs font-medium text-primary">
                        {relevancePercentage(source.relevance_score)}% match
                      </span>
                    )}
                  </div>
                </div>

                {/* Content preview - clickable to toggle */}
                <div
                  className="px-3 py-2 cursor-pointer hover:bg-muted/20 transition-colors"
                  onClick={() => toggleSourceExpanded(originalIdx)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      toggleSourceExpanded(originalIdx);
                    }
                  }}
                >
                  <div className={`${isExpanded ? '' : 'max-h-40'} overflow-y-auto bg-background rounded p-2 mb-2 text-xs transition-all`}>
                    <pre className="whitespace-pre-wrap break-words font-mono text-muted-foreground leading-relaxed">
                      {source.content}
                    </pre>
                  </div>
                  <div className="flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors">
                    <ChevronDown
                      className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                    />
                    <span className="text-xs ml-1">
                      {isExpanded ? 'Show less' : 'Show more'}
                    </span>
                  </div>
                </div>

                {/* Jump to source button */}
                <div className="px-3 py-2 border-t border-border/40 flex justify-end">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs gap-1 h-auto py-1 px-2"
                    onClick={() => {
                      onSourceJump(source.line_start, source.line_end);
                      onClose();
                    }}
                  >
                    Jump to Source
                    <ArrowUpRight className="h-3 w-3" />
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
