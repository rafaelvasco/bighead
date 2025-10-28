import { Routes, Route, Link, useLocation } from "react-router-dom";
import { FileText, Settings } from "lucide-react";
import { DocumentProvider } from "./contexts/DocumentContext";
import { DocumentList } from "./components/DocumentList";
import { HomeScreen } from "./components/HomeScreen";
import { DocumentDashboard } from "./components/DocumentDashboard";
import { AdminPage } from "./components/AdminPage";
import { Button } from "./components/ui/button";

function AppLayout() {
  const location = useLocation();
  const isAdminPage = location.pathname === "/admin";

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="border-b shrink-0">
        <div className="px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2 hover:opacity-80">
              <FileText className="h-6 w-6" />
              <h1 className="text-2xl font-bold">BigHead</h1>
              <span className="text-sm text-muted-foreground">
                Interact with you Knowledge
              </span>
            </Link>
            <Link to="/admin">
              <Button variant={isAdminPage ? "default" : "ghost"} size="sm">
                <Settings className="h-4 w-4 mr-2" />
                Admin
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - hide on admin page */}
        {!isAdminPage && (
          <aside className="w-80 border-r bg-muted/20 overflow-y-auto shrink-0">
            <DocumentList />
          </aside>
        )}

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 py-8 max-w-7xl h-full">
            <Routes>
              <Route path="/" element={<HomeScreen />} />
              <Route path="/document/:id" element={<DocumentDashboard />} />
              <Route path="/admin" element={<AdminPage />} />
            </Routes>
          </div>
        </main>
      </div>

      <footer className="border-t shrink-0">
        <div className="px-4 py-6 text-center text-sm text-muted-foreground">
          Made by Rafael Vasco
        </div>
      </footer>
    </div>
  );
}

function App() {
  return (
    <DocumentProvider>
      <AppLayout />
    </DocumentProvider>
  );
}

export default App;
