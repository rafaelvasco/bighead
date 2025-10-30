import { useState } from "react";
import type { ChatMessage } from "../types/document";
import { SourceDetailsModal } from "./SourceDetailsModal";

interface SourceHighlightProps {
  message: ChatMessage;
  onSourceClick: (lineStart: number, lineEnd: number) => void;
}

export function SourceHighlight({
  message,
  onSourceClick,
}: SourceHighlightProps) {
  const [showModal, setShowModal] = useState(false);
  const [selectedSourceIndex, setSelectedSourceIndex] = useState(0);

  if (!message.sources || message.sources.length === 0) {
    return null;
  }

  const handleSourceItemClick = (index: number) => {
    setSelectedSourceIndex(index);
    setShowModal(true);
  };

  const formatLineRange = (lineStart: number, lineEnd: number) => {
    if (lineStart === lineEnd) {
      return `Line ${lineStart}`;
    }
    return `Lines ${lineStart}-${lineEnd}`;
  };

  return (
    <>
      <div className="mt-2 pt-2 border-t border-border/40 space-y-1">
        <p className="text-xs font-semibold opacity-70">
          Sources ({message.sources.length})
        </p>
        <div className="space-y-1">
          {message.sources.map((source, idx) => (
            <button
              key={idx}
              onClick={() => handleSourceItemClick(idx)}
              className="cursor-pointer block w-full text-left px-2 py-1 text-xs rounded hover:bg-muted/50 transition-colors text-muted-foreground hover:text-foreground"
            >
              <span className="font-medium">{source.filename}</span>
              <span className="text-muted-foreground ml-2">
                ({formatLineRange(source.line_start, source.line_end)})
              </span>
            </button>
          ))}
        </div>
      </div>

      {showModal && (
        <SourceDetailsModal
          message={message}
          onClose={() => setShowModal(false)}
          onSourceJump={onSourceClick}
          initialSourceIndex={selectedSourceIndex}
        />
      )}
    </>
  );
}
