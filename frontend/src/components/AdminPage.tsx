import { useState } from "react";
import { Database, Table, Trash2, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { SQLiteViewer } from "./admin/SQLiteViewer";
import { ChromaViewer } from "./admin/ChromaViewer";
import { api } from "../services/api";

type ViewMode = "sqlite" | "chroma";

export function AdminPage() {
  const [viewMode, setViewMode] = useState<ViewMode>("sqlite");
  const [isClearing, setIsClearing] = useState(false);
  const [clearStatus, setClearStatus] = useState<{
    type: "success" | "error" | null;
    message: string;
  }>({ type: null, message: "" });

  const clearSqliteDatabase = async () => {
    if (!confirm("Are you sure you want to clear all data from the SQLite database? This will delete all documents and chat history.")) {
      return;
    }

    setIsClearing(true);
    setClearStatus({ type: null, message: "" });

    try {
      const result = await api.clearSqliteDatabase();
      setClearStatus({
        type: "success",
        message: result.message
      });
      // Refresh the current view
      if (viewMode === "sqlite") {
        // Force component refresh by toggling view mode
        setViewMode("chroma");
        setTimeout(() => setViewMode("sqlite"), 100);
      }
    } catch (error) {
      setClearStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Failed to clear SQLite database"
      });
    } finally {
      setIsClearing(false);
    }
  };

  const clearChromaDatabase = async () => {
    if (!confirm("Are you sure you want to clear all embeddings from ChromaDB? This will delete all document embeddings.")) {
      return;
    }

    setIsClearing(true);
    setClearStatus({ type: null, message: "" });

    try {
      const result = await api.clearChromaDatabase();
      setClearStatus({
        type: "success",
        message: result.message
      });
      // Refresh the current view
      if (viewMode === "chroma") {
        setViewMode("sqlite");
        setTimeout(() => setViewMode("chroma"), 100);
      }
    } catch (error) {
      setClearStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Failed to clear ChromaDB"
      });
    } finally {
      setIsClearing(false);
    }
  };

  const clearAllDatabases = async () => {
    if (!confirm("Are you sure you want to clear all data from both SQLite database and ChromaDB? This will delete all documents, chat history, and embeddings. This action cannot be undone!")) {
      return;
    }

    setIsClearing(true);
    setClearStatus({ type: null, message: "" });

    try {
      const result = await api.clearAllDatabases();
      setClearStatus({
        type: "success",
        message: result.message
      });
      // Refresh the current view
      const currentView = viewMode;
      setViewMode(currentView === "sqlite" ? "chroma" : "sqlite");
      setTimeout(() => setViewMode(currentView), 100);
    } catch (error) {
      setClearStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Failed to clear all databases"
      });
    } finally {
      setIsClearing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Database Administration</h1>
        <p className="text-muted-foreground">
          View and manage your SQLite and ChromaDB databases
        </p>
      </div>

      {clearStatus.type && (
        <div className={`p-4 rounded-md ${
          clearStatus.type === "success" 
            ? "bg-green-50 text-green-800 border border-green-200" 
            : "bg-red-50 text-red-800 border border-red-200"
        }`}>
          <div className="flex items-center gap-2">
            {clearStatus.type === "success" ? (
              <Database className="h-4 w-4" />
            ) : (
              <AlertTriangle className="h-4 w-4" />
            )}
            <span>{clearStatus.message}</span>
          </div>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Select Database</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Button
              onClick={() => setViewMode("sqlite")}
              variant={viewMode === "sqlite" ? "default" : "outline"}
              className="flex items-center gap-2"
              disabled={isClearing}
            >
              <Table className="h-4 w-4" />
              SQLite Database
            </Button>
            <Button
              onClick={() => setViewMode("chroma")}
              variant={viewMode === "chroma" ? "default" : "outline"}
              className="flex items-center gap-2"
              disabled={isClearing}
            >
              <Database className="h-4 w-4" />
              ChromaDB Embeddings
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            Danger Zone
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              The following actions are irreversible. Please be careful before proceeding.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button
                onClick={clearSqliteDatabase}
                variant="destructive"
                disabled={isClearing}
                className="flex items-center gap-2"
              >
                <Trash2 className="h-4 w-4" />
                {isClearing ? "Clearing..." : "Clear SQLite"}
              </Button>
              <Button
                onClick={clearChromaDatabase}
                variant="destructive"
                disabled={isClearing}
                className="flex items-center gap-2"
              >
                <Trash2 className="h-4 w-4" />
                {isClearing ? "Clearing..." : "Clear ChromaDB"}
              </Button>
              <Button
                onClick={clearAllDatabases}
                variant="destructive"
                disabled={isClearing}
                className="flex items-center gap-2"
              >
                <Trash2 className="h-4 w-4" />
                {isClearing ? "Clearing..." : "Clear All"}
              </Button>
            </div>
            <div className="text-xs text-muted-foreground">
              <p>• <strong>Clear SQLite:</strong> Deletes all documents and chat history</p>
              <p>• <strong>Clear ChromaDB:</strong> Deletes all document embeddings</p>
              <p>• <strong>Clear All:</strong> Deletes everything from both databases</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {viewMode === "sqlite" && <SQLiteViewer />}
      {viewMode === "chroma" && <ChromaViewer />}
    </div>
  );
}
