import { useState } from "react";
import { FileText, Loader2, Sparkles, RefreshCw } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useDocuments } from '../hooks/useDocuments';

export function DocumentSummary() {
  const { documentContent, selectedDocument, summary, generateSummary } = useDocuments();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateSummary = async () => {
    if (!documentContent || !selectedDocument?.id) return;

    setIsLoading(true);
    setError(null);

    try {
      await generateSummary(documentContent, selectedDocument.id);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to generate summary"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Document Summary
            </CardTitle>
            <CardDescription>{selectedDocument?.filename}</CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleGenerateSummary}
            disabled={isLoading || !documentContent}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                {summary ? 'Regenerate' : 'Generate'}
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="py-8">
            <div className="flex items-center justify-center gap-3 mb-4">
              <Sparkles className="h-6 w-6 text-primary animate-pulse" />
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-primary mb-1">
                Generating AI summary...
              </p>
              <p className="text-xs text-muted-foreground">
                Analyzing document content and extracting key insights
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 bg-destructive/10 border border-destructive/20 text-destructive rounded-md">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {summary && !isLoading ? (
          <div className="space-y-2">
            <p className="whitespace-pre-wrap text-sm">{summary}</p>
          </div>
        ) : !isLoading && !error && (
          <div className="text-center text-muted-foreground py-8">
            <Sparkles className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No summary generated yet.</p>
            <p className="text-sm mt-1">Click "Generate" to create one.</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
