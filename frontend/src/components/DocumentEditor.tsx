import { useState, useEffect, useRef } from "react";
import { FileEdit, Loader2, Save, Sparkles, Plus, Minus } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useDocuments } from "../hooks/useDocuments";
import { useDocumentContext } from "../contexts/DocumentContext";
import MDEditor from "@uiw/react-md-editor";
import "@uiw/react-md-editor/markdown-editor.css";
import "@uiw/react-markdown-preview/markdown.css";

export function DocumentEditor() {
  const { documentContent, selectedDocument, updateDocumentContent, generateSummary } =
    useDocuments();
  const { highlightedLineRange, setHighlightedLineRange } =
    useDocumentContext();
  const [content, setContent] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [fontSize, setFontSize] = useState(14);
  const editorContainerRef = useRef<HTMLDivElement | null>(null);
  const highlightTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Update local content when document changes
  useEffect(() => {
    setContent(documentContent || "");
    setHasChanges(false);
  }, [documentContent, selectedDocument?.filename]);

  const handleContentChange = (value: string | undefined) => {
    const newContent = value || "";
    setContent(newContent);
    setHasChanges(newContent !== documentContent);
  };

  const getLinePositions = (
    text: string,
    lineStart: number,
    lineEnd: number
  ) => {
    const lines = text.split("\n");
    let startPos = 0;
    let endPos = 0;

    // Convert 1-indexed line numbers to 0-indexed array indices
    const startIdx = Math.max(0, lineStart - 1);
    const endIdx = Math.min(lines.length - 1, lineEnd - 1);

    // Calculate start position (position at the beginning of the start line)
    for (let i = 0; i < startIdx; i++) {
      startPos += lines[i].length + 1;
    }

    // Calculate end position (position at the end of the end line)
    for (let i = 0; i <= endIdx; i++) {
      endPos += lines[i].length + 1;
    }

    return { startPos, endPos };
  };

  const scrollToAndHighlightLine = (lineStart: number, lineEnd: number) => {
    // Find textarea within MDEditor
    const editorElement = editorContainerRef.current;
    if (!editorElement) {
      console.error("Editor container not found");
      return;
    }

    const textarea = editorElement.querySelector(
      "textarea"
    ) as HTMLTextAreaElement;
    if (!textarea) {
      console.error("Textarea not found in editor");
      return;
    }

    // Find the scrollable container (MDEditor wraps textarea in a scrollable div)
    let scrollableContainer = textarea.parentElement;
    while (scrollableContainer && scrollableContainer !== editorElement) {
      const style = window.getComputedStyle(scrollableContainer);
      if (style.overflowY === "auto" || style.overflowY === "scroll") {
        break;
      }
      scrollableContainer = scrollableContainer.parentElement;
    }

    const { startPos, endPos } = getLinePositions(content, lineStart, lineEnd);

    // Focus and select the range
    textarea.focus();
    textarea.setSelectionRange(startPos, endPos);

    // Scroll to the target line position using content-ratio calculation
    requestAnimationFrame(() => {
      // Get the textarea wrapper and preview pane
      const textareaWrapper = editorElement.querySelector(
        ".w-md-editor-input"
      ) as HTMLDivElement;
      const previewPane = editorElement.querySelector(
        ".w-md-editor-preview"
      ) as HTMLDivElement;

      if (textareaWrapper && content) {
        // Calculate scroll position based on character position ratio
        // This accounts for actual rendered heights and padding
        const contentRatio = startPos / content.length;
        const maxScrollHeight =
          textareaWrapper.scrollHeight - textareaWrapper.clientHeight;
        const calculatedScrollTop = contentRatio * maxScrollHeight;

        // Set scroll position on the wrapper
        textareaWrapper.scrollTop = Math.max(0, calculatedScrollTop);

        // Sync preview pane using scale factor
        if (previewPane && maxScrollHeight > 0) {
          const scale =
            maxScrollHeight /
            (previewPane.scrollHeight - previewPane.clientHeight);
          const previewScrollTop = calculatedScrollTop / scale;
          previewPane.scrollTop = previewScrollTop;
        }
      }
    });

    // Add highlight styling
    textarea.classList.add("highlight-selection");

    // Clear previous timeout
    if (highlightTimeoutRef.current) {
      clearTimeout(highlightTimeoutRef.current);
    }

    // Remove highlight after 4 seconds
    highlightTimeoutRef.current = setTimeout(() => {
      textarea.classList.remove("highlight-selection");
      textarea.setSelectionRange(startPos, startPos);
      setHighlightedLineRange(null);
    }, 4000);
  };

  useEffect(() => {
    if (highlightedLineRange) {
      scrollToAndHighlightLine(
        highlightedLineRange.start,
        highlightedLineRange.end
      );
    }
  }, [highlightedLineRange, content]);

  useEffect(() => {
    let styleEl = document.getElementById("md-editor-font-size");
    if (!styleEl) {
      styleEl = document.createElement("style");
      styleEl.id = "md-editor-font-size";
      document.head.appendChild(styleEl);
    }

    const lineHeight = fontSize + 4;
    styleEl.textContent = `
      body .w-md-editor-text-pre > code,
      body .w-md-editor-text-input {
        font-size: ${fontSize}px !important;
        line-height: ${lineHeight}px !important;
      }
    `;
  }, [fontSize]);

  const handleSave = async () => {
    if (!selectedDocument?.filename || !hasChanges) return;

    setIsSaving(true);
    setError(null);

    try {
      await updateDocumentContent(selectedDocument.filename, content);
      setHasChanges(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save document");
    } finally {
      setIsSaving(false);
    }
  };

  const handleGenerateSummary = async () => {
    if (!selectedDocument?.id || !content) return;

    setIsGeneratingSummary(true);
    setError(null);

    try {
      await generateSummary(content, selectedDocument.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate summary");
    } finally {
      setIsGeneratingSummary(false);
    }
  };

  const increaseFontSize = () => {
    setFontSize((prev) => Math.min(prev + 1, 24));
  };

  const decreaseFontSize = () => {
    setFontSize((prev) => Math.max(prev - 1, 12));
  };

  return (
    <Card className="flex flex-col h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileEdit className="h-5 w-5" />
              Document Editor
            </CardTitle>
            <CardDescription>{selectedDocument?.filename}</CardDescription>
          </div>
          <div className="flex gap-2 items-center">
            {hasChanges && (
              <span className="text-xs text-muted-foreground">
                * Unsaved changes
              </span>
            )}
            <div className="flex items-center gap-1 border border-input rounded-md px-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={decreaseFontSize}
                disabled={fontSize <= 12}
                className="h-8 w-8 p-0"
              >
                <Minus className="h-4 w-4" />
              </Button>
              <span className="text-xs font-medium w-8 text-center">{fontSize}px</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={increaseFontSize}
                disabled={fontSize >= 24}
                className="h-8 w-8 p-0"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleGenerateSummary}
              disabled={isGeneratingSummary || !content}
            >
              {isGeneratingSummary ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Generate Summary
                </>
              )}
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={handleSave}
              disabled={isSaving || !hasChanges}
            >
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save
                </>
              )}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col overflow-hidden">
        {error && (
          <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 text-destructive rounded-md">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* MDEditor with full height */}
        <div className="flex-1 overflow-hidden" ref={editorContainerRef}>
          <MDEditor
            value={content}
            height="100%"
            preview="live"
            hideToolbar={false}
            visibleDragbar={true}
            onChange={handleContentChange}
            data-color-mode="light"
            textareaProps={{
              style: {
                fontFamily:
                  "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
              },
            }}
          />
        </div>
      </CardContent>
    </Card>
  );
}
