import { useState, useEffect } from "react";
import { api } from "../../services/api";
import type { ChromaCollection, ChromaDocuments } from "../../types/admin";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { ChevronLeft, ChevronRight, Trash2, ChevronDown, ChevronUp } from "lucide-react";

export function ChromaViewer() {
  const [collection, setCollection] = useState<ChromaCollection | null>(null);
  const [documents, setDocuments] = useState<ChromaDocuments | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedDocuments, setExpandedDocuments] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadCollection();
  }, []);

  useEffect(() => {
    loadDocuments(currentPage);
  }, [currentPage]);

  const loadCollection = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getChromaCollections();
      setCollection(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load collection info"
      );
    } finally {
      setLoading(false);
    }
  };

  const loadDocuments = async (page: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getChromaDocuments(page, 20);
      setDocuments(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    } finally {
      setLoading(false);
    }
  };

  const deleteDocumentEmbeddings = async (filename: string) => {
    if (!confirm(`Are you sure you want to delete all embeddings for"${filename}"?`)) {
      return;
    }

    try {
      await api.deleteDocumentEmbeddings(filename);
      loadDocuments(currentPage);
      if (collection) {
        loadCollection(); // Refresh count
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete document embeddings");
    }
  };

  const toggleDocumentExpansion = (filename: string) => {
    setExpandedDocuments((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(filename)) {
        newSet.delete(filename);
      } else {
        newSet.add(filename);
      }
      return newSet;
    });
  };

  const formatContent = (content: string): string => {
    return content.length > 200 ? content.slice(0, 200) + "..." : content;
  };

  if (loading && !collection) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Loading ChromaDB collection...
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      {collection && (
        <Card>
          <CardHeader>
            <CardTitle>Collection: {collection.collection_name}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-muted-foreground">
              <p>Total Embeddings: {collection.total_embeddings}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {documents && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Documents</CardTitle>
              <div className="text-sm text-muted-foreground">
                Showing {documents.total} documents
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {documents.documents.map((document) => (
                <div
                  key={document.filename}
                  className="border rounded-lg overflow-hidden hover:bg-muted/50"
                >
                  <div className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => toggleDocumentExpansion(document.filename)}
                          className="p-1 h-8 w-8"
                        >
                          {expandedDocuments.has(document.filename) ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </Button>
                        <div>
                          <div className="font-medium">{document.filename}</div>
                          <div className="text-sm text-muted-foreground">
                            {document.chunk_count} embeddings
                            {document.uploaded_at && (
                              <>
                                {" "}• Uploaded {new Date(document.uploaded_at).toLocaleDateString()}
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => deleteDocumentEmbeddings(document.filename)}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>

                    {expandedDocuments.has(document.filename) && (
                      <div className="mt-4 space-y-2">
                        <div className="text-sm font-medium text-muted-foreground">
                          Embeddings ({document.embeddings.length}):
                        </div>
                        {document.embeddings.map((embedding, index) => (
                          <div
                            key={embedding.id}
                            className="border rounded-md p-3 bg-muted/30"
                          >
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-xs font-mono bg-muted px-2 py-1 rounded">
                                {index + 1}. ID: {embedding.id}
                              </span>
                            </div>
                            <div className="text-sm font-mono bg-white/50 p-2 rounded mb-2 whitespace-pre-wrap break-words border">
                              {formatContent(embedding.content)}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              <div className="grid grid-cols-2 gap-2">
                                {Object.entries(embedding.metadata).map(([key, value]) => (
                                  <div key={key} className="flex gap-1">
                                    <span className="font-semibold">{key}:</span>
                                    <span className="font-mono truncate">
                                      {typeof value === "object"
                                        ? JSON.stringify(value)
                                        : String(value)}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {documents.total_pages > 1 && (
              <div className="flex items-center justify-between mt-4">
                <Button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  variant="outline"
                  size="sm"
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {currentPage} of {documents.total_pages}
                </span>
                <Button
                  onClick={() =>
                    setCurrentPage((p) =>
                      Math.min(documents.total_pages, p + 1)
                    )
                  }
                  disabled={currentPage === documents.total_pages}
                  variant="outline"
                  size="sm"
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
