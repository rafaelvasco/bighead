# BigHead - AI-Powered Document Analyst

A full-stack application that uses RAG (Retrieval-Augmented Generation) to analyze documents, answer questions, generate summaries, and provide web search integration capabilities.

## Features

- **Document Upload**: Upload text and markdown files for analysis
- **RAG-Powered Q&A**: Ask questions about your documents with source references showing `[filename]:[line-start]-[line-end]`
- **AI Summarization**: Automatic document summarization with key insights
- **Document Editor**: Advanced markdown editor with live preview
- **Web Search Integration**: Perplexity API integration for comprehensive web search with AI-generated answers
- **Document Creation from Search**: Create documents directly from web search results
- **Admin Interface**: Database management and vector store inspection tools
- **Modern UI**: Clean, responsive interface built with React and ShadCN UI

## Tech Stack

### Frontend

- **Vite** + **React 19** + **TypeScript**
- **Tailwind CSS** for styling
- **ShadCN UI** for component library
- **React Router** for navigation
- **@uiw/react-md-editor** for markdown editing and preview
- **React Markdown** for markdown rendering

### Backend

- **Flask** - Python web framework
- **Haystack** - LLM orchestration and RAG pipeline
- **ChromaDB** - Embedded vector database
- **SQLite** - Document metadata and chat history
- **OpenRouter** - LLM generation (GPT-4o-mini)
- **OpenAI API** - Text embeddings
- **Perplexity API** - Web search with AI-generated comprehensive answers

## Project Structure

```
bighead/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/      # UI components
│   │   │   ├── ui/         # ShadCN UI components
│   │   │   ├── App.tsx     # Main application with routing
│   │   │   ├── HomeScreen.tsx
│   │   │   ├── DocumentList.tsx
│   │   │   ├── DocumentDashboard.tsx
│   │   │   ├── DocumentEditor.tsx
│   │   │   ├── QueryInterface.tsx
│   │   │   ├── DocumentSummary.tsx
│   │   │   ├── CreateFromSearch.tsx
│   │   │   └── AdminPage.tsx
│   │   ├── contexts/        # React Context
│   │   │   └── DocumentContext.tsx
│   │   ├── hooks/          # Custom hooks
│   │   │   └── useDocuments.ts
│   │   ├── services/        # API client
│   │   │   └── api.ts
│   │   ├── types/          # TypeScript type definitions
│   │   └── lib/            # Utilities
│   └── package.json
│
└── backend/                  # Flask backend
    ├── app/
    │   ├── routes/          # API endpoints
    │   │   ├── documents.py    # Document management
    │   │   ├── query.py        # RAG queries
    │   │   ├── summarize.py    # Document summarization
    │   │   ├── health.py       # Health checks
    │   │   └── admin.py        # Admin tools
    │   ├── services/        # Business logic
    │   │   ├── document_service.py     # Document management
    │   │   ├── query_service.py        # Query orchestration
    │   │   ├── summarizer.py           # Document summarization
    │   │   ├── search/                 # Search services
    │   │   │   ├── base.py
    │   │   │   ├── perplexity.py
    │   │   │   └── search_services_manager.py
    │   │   ├── retrieval/              # RAG pipeline
    │   │   │   ├── __init__.py
    │   │   │   ├── chromadb_manager.py
    │   │   │   ├── embeddings_manager.py
    │   │   │   ├── text_chunker.py
    │   │   │   └── query_expander.py
    │   │   └── utils.py
    │   ├── database/        # Database layer
    │   │   └── database_service.py
    │   ├── models/          # Data models
    │   └── utils/           # Utilities
    │   ├── __init__.py      # Flask app factory
    │   └── config.py        # Configuration
    ├── uploads/             # Uploaded documents
    ├── data/                # Database and ChromaDB persistence
    └── requirements.txt
```

## Setup Instructions

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+
- **OpenRouter API Key** (for LLM generation)
- **OpenAI API Key** (for text embeddings)
- **Perplexity API Key** (for web search)

### Backend Setup

1. **Navigate to backend directory**:

   ```bash
   cd backend
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:

   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   PERPLEXITY_API_KEY=your_perplexity_api_key_here
   FLASK_ENV=development
   FLASK_DEBUG=True
   FLASK_PORT=5177
   UPLOAD_FOLDER=uploads
   CHROMA_DB_PATH=./data/chroma_db
   ```

5. **Run the Flask server**:

   ```bash
   python run.py
   ```

   The backend will be available at `http://localhost:5177`

### Frontend Setup

1. **Navigate to frontend directory**:

   ```bash
   cd frontend
   ```

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Configure environment** (optional):

   ```bash
   cp .env.example .env
   ```

   The default API URL is `http://localhost:5177/api`

4. **Run the development server**:

   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

## Usage

1. **Upload a Document**:

   - Drag and drop a `.txt` or `.md` file, or click to browse
   - The document will be automatically indexed into the vector database
   - Navigate to the document dashboard to view content

2. **Document Editor**:

   - Edit documents with the advanced markdown editor with live preview
   - Changes are automatically saved and re-indexed

3. **View Summary**:

   - AI-generated summaries appear automatically for each document
   - Shows document statistics (word count, line count, chunk count)

4. **Ask Questions**:

   - Type questions about your document in the chat interface
   - Get AI-powered answers with source references in the format `[filename]:[line-start]-[line-end]`
   - Chat history is preserved for each document

5. **Create from Search**:

   - Use web search to create new documents
   - Enter a search query and let Perplexity AI generate comprehensive content
   - Save the search results as a new document for further analysis

6. **Admin Interface**:
   - Access database management tools
   - Inspect vector store data and embeddings
   - Monitor system health and performance

## API Endpoints

### Documents

- `POST /api/documents/upload` - Upload and index a document
- `POST /api/documents/create-from-search` - Create a document from web search results
- `GET /api/documents/` - List all indexed documents
- `GET /api/documents/<filename>` - Get document content and metadata
- `PUT /api/documents/<filename>` - Update document content
- `DELETE /api/documents/<filename>` - Delete a document
- `GET /api/documents/<filename>/data` - Get document with chat history

### Query

- `POST /api/query` - Query documents with RAG
  ```json
  {
    "question": "What is the main topic?",
    "document_id": "document_uuid",
    "top_k": 5
  }
  ```

### Summarization

- `POST /api/summarize` - Generate document summary
  ```json
  {
    "content": "document content here",
    "document_id": "document_uuid"
  }
  ```

### Health

- `GET /api/health` - System health check

### Admin

- `GET /api/admin/documents` - List all documents with full metadata
- `GET /api/admin/embeddings` - View vector embeddings
- `GET /api/admin/chat-history` - View chat history
- `DELETE /api/admin/clear-all` - Clear all data (admin only)

## Key Features Explained

### RAG with Line References

The system chunks documents while tracking line numbers, so every answer includes precise source references:

```
Answer: The document discusses machine learning applications.
Sources:
  - introduction.txt:1-15
  - introduction.txt:45-60
```

### Document Context Management

The application uses a centralized Context + Hooks pattern for state management:

- **DocumentContext**: Central state store for all document-related data
- **useDocuments Hook**: Custom hook that abstracts all API calls and manages state updates
- **Real-time synchronization**: Automatic updates across all components when data changes

### Perplexity Web Search Integration

- Comprehensive web search with AI-generated answers
- Citation sources are included for transparency
- Create documents directly from search results
- Context-aware search capabilities

## Development Notes

### Frontend Architecture

The frontend follows a component-based architecture with:

- **Type-first development**: TypeScript interfaces defined before implementation
- **Context + Hooks pattern**: Centralized state management with DocumentContext
- **Component composition**: Complex UI built from reusable primitives
- **Enforced coding standards**: ESLint with consistent-type-imports rule

### Backend Architecture

The backend uses a layered service architecture:

- **Flask Blueprints**: Modular routing organization
- **Service Layer**: Business logic separation
- **Database Service**: SQLite for metadata, ChromaDB for vectors
- **Search Service Manager**: Pluggable search service architecture

### Customizing the RAG Pipeline

Modify `backend/app/services/retrieval/` to:

- Change chunking strategies in `text_chunker.py`
- Adjust retrieval parameters in `__init__.py`
- Modify prompts in the query pipeline
- Add new embedding models in `embeddings_manager.py`

### Adding New Search Services

To add new search services:

1. Create a new class extending `SearchService` in `backend/app/services/search/`
2. Register it in `search_services_manager.py`
3. Configure API keys in `.env`

### Styling

The frontend uses Tailwind CSS with ShadCN UI components. Customize colors and themes in:

- `tailwind.config.js`
- `src/index.css`

## Troubleshooting

### Backend Issues

**Error: "OPENROUTER_API_KEY not set"**

- Make sure you've created a `.env` file in the `backend/` directory
- Add your OpenRouter API key for LLM generation

**Error: "OPENAI_API_KEY not set"**

- Add your OpenAI API key for text embeddings
- This is required for document indexing and queries

**Error: "PERPLEXITY_API_KEY not set"**

- Add your Perplexity API key for web search functionality
- Without this, search features will return empty results

**ChromaDB Permission Errors**

- Ensure the `backend/data/` directory is writable
- Try deleting `backend/data/chroma_db` and restarting
- Check filesystem permissions

**Database Connection Issues**

- Ensure SQLite can create files in `backend/data/`
- Check that the directory exists and is writable
- Look for detailed error messages in the server logs

### Frontend Issues

**API Connection Failed**

- Make sure the backend is running on port 5177
- Check CORS settings in `backend/app/__init__.py`
- Verify the API URL in frontend `.env` file

**TypeScript Errors**

- Run `npm install` to ensure all dependencies are installed
- Check that `@types/node` is installed for path resolution
- Ensure all imports use proper type imports (separate type imports enforced)

**Document Upload Fails**

- Check file size (max 16MB)
- Verify file extension is .txt or .md
- Check backend logs for detailed error messages

**Query Not Returning Results**

- Verify the document was properly indexed
- Check ChromaDB status in the admin interface
- Try increasing the `top_k` parameter in queries

## Next Enhancements

- [ ] Enhanced search with multiple providers
- [ ] Clicking on response sources show their position in the document
- [ ] Enhance RAG retrieval accuracy even more.
- [ ] Scale:
  - Scale DB (Postgres/Supabase?)
  - Scale Embedding Storage
  - Scale Backend (Flask Scaling Strategies/Find Scaling bottlenecks)
  - Scalable Deploy Strategy: (K8s/AWS)
  - Add Caching (Redis?)
  - Add Event/Message Queue (AWS/Other Provider)
- [ ] Abstract away LLM usage (MCP for LLM) for seamlessly supporting other models
- [] ?

## License

MIT License - feel free to use this project for learning and portfolio purposes.

## Credits

Built with:

- [Haystack](https://haystack.deepset.ai/) for RAG orchestration
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [OpenRouter](https://openrouter.ai/) for LLM generation
- [OpenAI](https://openai.com/) for text embeddings
- [Perplexity AI](https://www.perplexity.ai/) for web search
- [ShadCN UI](https://ui.shadcn.com/) for components
- [React](https://react.dev/) for the frontend framework
- [Flask](https://flask.palletsprojects.com/) for the backend framework
