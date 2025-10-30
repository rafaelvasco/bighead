import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useDocuments } from "../hooks/useDocuments";
import {
  FileText,
  Trash2,
  RefreshCw,
  AlertCircle,
  Loader2,
  Plus,
} from "lucide-react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogFooter } from "./ui/dialog";
import { formatDateToLocal } from "../lib/dateUtils";

export function DocumentList() {
  const navigate = useNavigate();
  const { id: currentDocId } = useParams<{ id: string }>();
  const { documents, isLoading, error, loadDocuments, deleteDocument } =
    useDocuments();

  const [deletingDoc, setDeletingDoc] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [docToDelete, setDocToDelete] = useState<string | null>(null);

  const handleCreateNew = () => {
    navigate("/");
  };

  const handleSelectDocument = (docId: string) => {
    navigate(`/document/${docId}`);
  };

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const handleDelete = async (filename: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent selecting the document when clicking delete
    setDocToDelete(filename);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!docToDelete) return;

    try {
      setDeletingDoc(docToDelete);
      await deleteDocument(docToDelete);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete document");
    } finally {
      setDeletingDoc(null);
      setDocToDelete(null);
      setDeleteDialogOpen(false);
    }
  };

  const cancelDelete = () => {
    setDocToDelete(null);
    setDeleteDialogOpen(false);
  };

  if (isLoading && documents.length === 0) {
    return (
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Documents</h2>
          <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
        </div>
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-muted animate-pulse rounded-lg" />
          ))}
        </div>
        <p className="text-xs text-center text-muted-foreground">
          Loading documents...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Documents</h2>
          <Button onClick={loadDocuments} size="sm" variant="outline">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
        <Card className="p-4 bg-destructive/10 border-destructive/20">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-destructive shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-destructive">
                Error loading documents
              </p>
              <p className="text-xs text-destructive/80 mt-1">{error}</p>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Documents</h2>
        <div className="flex items-center gap-2">
          <Button
            onClick={handleCreateNew}
            size="sm"
            variant="default"
            title="Create new document"
            className="h-8 w-8 p-0"
          >
            <Plus className="w-4 h-4" />
          </Button>
          <Button
            onClick={loadDocuments}
            size="sm"
            variant="outline"
            title="Refresh documents"
            disabled={isLoading}
            className="h-8 w-8 p-0"
          >
            <RefreshCw
              className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`}
            />
          </Button>
        </div>
      </div>

      {documents.length === 0 ? (
        <Card className="p-6 text-center">
          <FileText className="w-12 h-12 mx-auto text-muted-foreground mb-3" />
          <p className="text-sm text-muted-foreground">
            No documents created yet
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Create a document to get started
          </p>
        </Card>
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => (
            <Card
              key={doc.filename}
              className={`p-3 cursor-pointer transition-all hover:shadow-md ${
                currentDocId === doc.id
                  ? "bg-primary/10 border-primary"
                  : "hover:bg-muted/50"
              }`}
              onClick={() => handleSelectDocument(doc.id)}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2 flex-1 min-w-0">
                  <FileText className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p
                      className="text-sm font-medium truncate"
                      title={doc.filename}
                    >
                      {doc.filename}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatDateToLocal(
                        (doc as any).created_at || doc.uploaded_at
                      )}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {doc.chunk_count} chunks
                    </p>
                  </div>
                </div>
                <Button
                  onClick={(e) => handleDelete(doc.filename, e)}
                  size="sm"
                  variant="ghost"
                  className="shrink-0 h-8 w-8 p-0 hover:bg-destructive/10 hover:text-destructive"
                  disabled={deletingDoc === doc.filename}
                  title={
                    deletingDoc === doc.filename
                      ? "Deleting..."
                      : "Delete document"
                  }
                >
                  {deletingDoc === doc.filename ? (
                    <Loader2 className="w-4 h-4 animate-spin text-destructive" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Dialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Document"
        description={`Are you sure you want to delete "${docToDelete}"? This action cannot be undone.`}
      >
        <DialogContent>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={cancelDelete}
              disabled={deletingDoc !== null}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={confirmDelete}
              disabled={deletingDoc !== null}
            >
              {deletingDoc ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
