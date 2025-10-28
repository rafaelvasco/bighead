import { useState } from "react";
import { Search, Loader2, Plus } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useDocuments } from "../hooks/useDocuments";

export function CreateFromSearch() {
  const { createFromSearch } = useDocuments();
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const generateFilenameFromQuery = (query: string): string => {
    // Convert query to a clean filename
    return (
      query
        .toLowerCase()
        .replace(/[^a-z0-9\s]/g, "")
        .trim()
        .replace(/\s+/g, "-")
        .substring(0, 50) + ".md"
    );
  };

  const handleCreate = async () => {
    if (!query.trim()) {
      setError("Please provide a search query");
      return;
    }

    // Generate filename from query
    const filename = generateFilenameFromQuery(query);

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await createFromSearch(query, filename);
      setSuccess(`Document "${filename}" created successfully!`);
      // Clear form
      setQuery("");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create document"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="h-5 w-5" />
          Create Document from Web Search
        </CardTitle>
        <CardDescription>
          Search the web and create a document from the results
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="search-query">Search Query</Label>
          <Input
            id="search-query"
            placeholder="e.g., Latest AI developments 2025"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isLoading}
          />
        </div>

        {error && (
          <div className="p-3 bg-destructive/10 border border-destructive/20 text-destructive rounded-md">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {success && (
          <div className="p-3 bg-green-500/10 border border-green-500/20 text-green-700 dark:text-green-400 rounded-md">
            <p className="text-sm">{success}</p>
          </div>
        )}

        <Button
          className="w-full"
          onClick={handleCreate}
          disabled={isLoading || !query.trim()}
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Creating Document...
            </>
          ) : (
            <>
              <Plus className="h-4 w-4 mr-2" />
              Create Document
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
