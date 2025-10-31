import { useEffect, useState } from "react";
import { useParams, Navigate } from "react-router-dom";
import { DocumentEditor } from "./DocumentEditor";
import { SummaryPanel } from "./SummaryPanel";
import { QueryInterface } from "./QueryInterface";
import { useDocuments } from "../hooks/useDocuments";

export function DocumentDashboard() {
  const { id } = useParams<{ id: string }>();
  const [summaryExpanded, setSummaryExpanded] = useState(true);
  const {
    documentContent,
    selectedDocument,
    selectDocument,
    documents,
    summary,
  } = useDocuments();

  // Select the document based on URL parameter
  useEffect(() => {
    if (id && (!selectedDocument || selectedDocument.id !== id)) {
      // Find document by ID
      const doc = documents.find((d) => d.id === id);
      if (doc) {
        selectDocument(doc.filename);
      }
    }
  }, [id, selectedDocument, documents, selectDocument]);

  // If no ID in URL, redirect to home
  if (!id) {
    return <Navigate to="/" replace />;
  }

  // If document not found in list, show error
  const doc = documents.find((d) => d.id === id);
  if (documents.length > 0 && !doc) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Document not found</p>
      </div>
    );
  }

  // Loading state
  if (!documentContent) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">Loading document...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Top Section - Document Editor */}
      <div className="h-[1000px]">
        <DocumentEditor />
      </div>

      {/* Summary Panel - Conditionally Rendered */}
      {summary && (
        <div
          className={`transition-all duration-300 overflow-hidden ${
            summaryExpanded ? "max-h-[700px]" : "h-[100px]"
          }`}
        >
          <SummaryPanel
            summary={summary}
            filename={selectedDocument?.filename}
            isExpanded={summaryExpanded}
            onExpandedChange={setSummaryExpanded}
          />
        </div>
      )}

      {/* Bottom Section - Chat Interface */}
      <div>
        <QueryInterface />
      </div>
    </div>
  );
}
