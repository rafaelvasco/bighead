import { DocumentUpload } from './DocumentUpload';
import { CreateFromSearch } from './CreateFromSearch';

export function HomeScreen() {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold mb-2">Welcome to BigHead</h2>
        <p className="text-muted-foreground">
          Choose how you want to create your document
        </p>
      </div>

      <div className="space-y-4">
        {/* Upload Document Path */}
        <DocumentUpload />

        {/* Create from Search Path */}
        <CreateFromSearch />
      </div>
    </div>
  );
}
