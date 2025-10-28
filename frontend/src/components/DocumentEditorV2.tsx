import { useState, useEffect } from "react";
import { FileEdit, Loader2, Save } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useDocuments } from "../hooks/useDocuments";
import MDEditor from "@uiw/react-md-editor";
import "@uiw/react-md-editor/markdown-editor.css";
import "@uiw/react-markdown-preview/markdown.css";

export function DocumentEditorV2() {
  const { documentContent, selectedDocument, updateDocumentContent } =
    useDocuments();
  const [content, setContent] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

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

        {/* MDEditor with full height */}
        <div className="flex-1 overflow-hidden">
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
                fontSize: "0.875rem",
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
