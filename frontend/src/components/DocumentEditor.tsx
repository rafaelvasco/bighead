import { useState, useEffect, useRef, useMemo } from "react";
import { FileEdit, Loader2, Save, ArrowDownToLine } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useDocuments } from '../hooks/useDocuments';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import styles from './DocumentEditor.module.css';
import CodeMirror from '@uiw/react-codemirror';
import { markdown, markdownLanguage } from '@codemirror/lang-markdown';
import { languages } from '@codemirror/language-data';
import { EditorView } from '@codemirror/view';

import type { EditorView as EditorViewType } from '@codemirror/view';
import type { Components } from 'react-markdown';

// Interface for markdown blocks
interface MarkdownBlock {
  id: string;
  startLine: number;
  endLine: number;
  type: 'header' | 'paragraph' | 'list' | 'code' | 'hr' | 'blockquote';
}

// Parse markdown content into blocks with line ranges
function parseMarkdownBlocks(content: string): { blocks: MarkdownBlock[], lineToBlockId: Map<number, string> } {
  const lines = content.split('\n');
  const blocks: MarkdownBlock[] = [];
  const lineToBlockId = new Map<number, string>();

  let blockId = 0;
  let currentBlock: MarkdownBlock | null = null;
  let inCodeBlock = false;
  let inListBlock = false;

  const finishBlock = () => {
    if (currentBlock) {
      blocks.push(currentBlock);
      // Map all lines in this block to its ID
      for (let i = currentBlock.startLine; i <= currentBlock.endLine; i++) {
        lineToBlockId.set(i, currentBlock.id);
      }
      currentBlock = null;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Code block boundaries
    if (trimmed.startsWith('```')) {
      if (!inCodeBlock) {
        finishBlock();
        currentBlock = {
          id: `block-${blockId++}`,
          startLine: i,
          endLine: i,
          type: 'code'
        };
        inCodeBlock = true;
      } else {
        if (currentBlock) {
          currentBlock.endLine = i;
        }
        finishBlock();
        inCodeBlock = false;
      }
      continue;
    }

    if (inCodeBlock) {
      if (currentBlock) {
        currentBlock.endLine = i;
      }
      continue;
    }

    // Empty lines end blocks
    if (trimmed === '') {
      finishBlock();
      inListBlock = false;
      continue;
    }

    // Horizontal rule
    if (trimmed === '---' || trimmed === '***' || trimmed === '___') {
      finishBlock();
      blocks.push({
        id: `block-${blockId++}`,
        startLine: i,
        endLine: i,
        type: 'hr'
      });
      lineToBlockId.set(i, blocks[blocks.length - 1].id);
      continue;
    }

    // Headers
    if (trimmed.startsWith('#')) {
      finishBlock();
      blocks.push({
        id: `block-${blockId++}`,
        startLine: i,
        endLine: i,
        type: 'header'
      });
      lineToBlockId.set(i, blocks[blocks.length - 1].id);
      continue;
    }

    // List items
    const isListItem = /^[-*+]\s/.test(trimmed) || /^\d+\.\s/.test(trimmed);
    if (isListItem) {
      if (!inListBlock) {
        finishBlock();
        currentBlock = {
          id: `block-${blockId++}`,
          startLine: i,
          endLine: i,
          type: 'list'
        };
        inListBlock = true;
      } else if (currentBlock) {
        currentBlock.endLine = i;
      }
      continue;
    }

    // Regular paragraph
    if (!currentBlock || currentBlock.type !== 'paragraph') {
      finishBlock();
      currentBlock = {
        id: `block-${blockId++}`,
        startLine: i,
        endLine: i,
        type: 'paragraph'
      };
    } else {
      currentBlock.endLine = i;
    }
  }

  finishBlock();

  return { blocks, lineToBlockId };
}

export function DocumentEditor() {
  const { documentContent, selectedDocument, updateDocumentContent } = useDocuments();
  const [content, setContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  const editorViewRef = useRef<EditorViewType | null>(null);
  const previewRef = useRef<HTMLDivElement | null>(null);

  // Parse markdown into blocks
  const { blocks, lineToBlockId } = useMemo(() => parseMarkdownBlocks(content), [content]);

  // Track which block we're currently rendering
  const renderIndexRef = useRef(0);

  // Reset render index before each render
  useEffect(() => {
    renderIndexRef.current = 0;
  });

  // Create custom components that use block IDs
  const components: Components = useMemo(() => {
    return {
      h1: ({ children, ...props }) => {
        const block = blocks[renderIndexRef.current++];
        return <h1 id={block?.id} data-block-id={block?.id} {...props}>{children}</h1>;
      },
      h2: ({ children, ...props }) => {
        const block = blocks[renderIndexRef.current++];
        return <h2 id={block?.id} data-block-id={block?.id} {...props}>{children}</h2>;
      },
      h3: ({ children, ...props }) => {
        const block = blocks[renderIndexRef.current++];
        return <h3 id={block?.id} data-block-id={block?.id} {...props}>{children}</h3>;
      },
      h4: ({ children, ...props }) => {
        const block = blocks[renderIndexRef.current++];
        return <h4 id={block?.id} data-block-id={block?.id} {...props}>{children}</h4>;
      },
      h5: ({ children, ...props }) => {
        const block = blocks[renderIndexRef.current++];
        return <h5 id={block?.id} data-block-id={block?.id} {...props}>{children}</h5>;
      },
      h6: ({ children, ...props }) => {
        const block = blocks[renderIndexRef.current++];
        return <h6 id={block?.id} data-block-id={block?.id} {...props}>{children}</h6>;
      },
      p: ({ children, ...props }) => {
        const block = blocks[renderIndexRef.current++];
        return <p id={block?.id} data-block-id={block?.id} {...props}>{children}</p>;
      },
      ul: ({ children, ...props }) => {
        const block = blocks[renderIndexRef.current++];
        return <ul id={block?.id} data-block-id={block?.id} {...props}>{children}</ul>;
      },
      ol: ({ children, ...props }) => {
        const block = blocks[renderIndexRef.current++];
        return <ol id={block?.id} data-block-id={block?.id} {...props}>{children}</ol>;
      },
      pre: ({ children, ...props }) => {
        const block = blocks[renderIndexRef.current++];
        return <pre id={block?.id} data-block-id={block?.id} {...props}>{children}</pre>;
      },
      blockquote: ({ children, ...props }) => {
        const block = blocks[renderIndexRef.current++];
        return <blockquote id={block?.id} data-block-id={block?.id} {...props}>{children}</blockquote>;
      },
    };
  }, [blocks]);

  // Simplified scroll to line functionality
  const handleScrollToLine = () => {
    if (!editorViewRef.current || !previewRef.current) {
      return;
    }

    const editorView = editorViewRef.current;
    const cursorPos = editorView.state.selection.main.head;
    const line = editorView.state.doc.lineAt(cursorPos);
    const cursorLine = line.number - 1; // 0-indexed
    const lineText = line.text;

    console.log('=== Scroll to Line ===');
    console.log('Cursor line number:', cursorLine);
    console.log('Line text:', lineText);

    // Get the block ID for this line
    const blockId = lineToBlockId.get(cursorLine);

    if (!blockId) {
      console.log('❌ No block found for line', cursorLine);
      return;
    }

    // Find the corresponding block info
    const block = blocks.find(b => b.id === blockId);
    console.log('✓ Block ID:', blockId);
    console.log('✓ Block type:', block?.type);
    console.log('✓ Block line range:', `${block?.startLine} - ${block?.endLine}`);

    // Find the element with this ID
    const targetElement = document.getElementById(blockId);

    if (targetElement) {
      console.log('✓ Found element:', targetElement.tagName);
      console.log('✓ Element text preview:', targetElement.textContent?.substring(0, 60) + '...');
      targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
      targetElement.classList.add('highlight-flash');
      setTimeout(() => targetElement.classList.remove('highlight-flash'), 2000);
      console.log('✓ Scrolled to block successfully');
    } else {
      console.log('❌ Element not found for block ID:', blockId);
    }
  };

  // Update local content when document changes
  useEffect(() => {
    setContent(documentContent || '');
    setHasChanges(false);
  }, [documentContent, selectedDocument?.filename]);

  const handleContentChange = (value: string) => {
    setContent(value);
    setHasChanges(value !== documentContent);
  };

  const handleSave = async () => {
    if (!selectedDocument?.filename || !hasChanges) return;

    setIsSaving(true);
    setError(null);

    try {
      await updateDocumentContent(selectedDocument.filename, content);
      setHasChanges(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save document');
    } finally {
      setIsSaving(false);
    }
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

        {/* Split Pane: Editor on Left, Preview on Right */}
        <div className="flex-1 grid grid-cols-2 gap-4 overflow-hidden">
          {/* Left: Markdown Editor */}
          <div className="flex flex-col overflow-hidden">
            <CodeMirror
              value={content}
              height="100%"
              extensions={[
                markdown({ base: markdownLanguage, codeLanguages: languages }),
                EditorView.lineWrapping,
              ]}
              onChange={(value) => handleContentChange(value)}
              onCreateEditor={(view) => {
                editorViewRef.current = view;
              }}
              className="flex-1 overflow-auto text-sm"
              basicSetup={{
                lineNumbers: true,
                highlightActiveLineGutter: true,
                highlightActiveLine: true,
                foldGutter: true,
              }}
            />
          </div>

          {/* Right: Live Preview */}
          <div className="flex flex-col overflow-hidden">
            <div className="mb-2 flex justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={handleScrollToLine}
                disabled={!content}
              >
                <ArrowDownToLine className="h-4 w-4 mr-2" />
                Scroll to Line
              </Button>
            </div>
            <div className={styles.markdownPreview} ref={previewRef}>
              {content ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={components}
                >
                  {content}
                </ReactMarkdown>
              ) : (
                <p className="text-muted-foreground italic">
                  Preview will appear here...
                </p>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
