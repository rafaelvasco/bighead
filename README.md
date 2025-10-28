# BigHead - AI-Powered Document Analyst

A full-stack application that uses RAG (Retrieval-Augmented Generation) to analyze documents, answer questions, generate summaries, and provide autonomous agent suggestions with web search integration.

## Features

- **Document Upload**: Upload text and markdown files for analysis
- **RAG-Powered Q&A**: Ask questions about your documents with source references showing `[filename]:[line-range]`
- **AI Summarization**: Automatic document summarization with key insights
- **Autonomous Agent**: AI agent that suggests follow-up actions and research queries
- **Web Search Integration**: Perplexity API integration for comprehensive web search with AI-generated answers
- **Modern UI**: Clean, responsive interface built with React and ShadCN UI

## Tech Stack

### Frontend
- **Vite** + **React** + **TypeScript**
- **Tailwind CSS** for styling
- **ShadCN UI** for component library
- **Lucide React** for icons

### Backend
- **Flask** - Python web framework
- **Haystack** - LLM orchestration and RAG pipeline
- **ChromaDB** - Embedded vector database
- **OpenRouter** - OpenAI API access
- **Perplexity API** - Web search with AI-generated comprehensive answers

## Project Structure

```
big-head/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/      # UI components
│   │   │   ├── ui/         # ShadCN UI components
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── QueryInterface.tsx
│   │   │   ├── DocumentSummary.tsx
│   │   │   └── AgentSuggestions.tsx
│   │   ├── services/        # API client
│   │   └── App.tsx          # Main application
│   └── package.json
│
└── backend/                  # Flask backend
    ├── app/
    │   ├── routes/          # API endpoints
    │   │   ├── documents.py
    │   │   ├── query.py
    │   │   ├── summarize.py
    │   │   └── agent.py
    │   ├── services/        # Business logic
    │   │   ├── rag_service.py      # RAG with Haystack + ChromaDB
    │   │   ├── summarizer.py       # Document summarization
    │   │   ├── agent.py            # Autonomous agent
    │   │   └── mcp_tools.py        # Web search tools
    │   └── __init__.py
    ├── uploads/             # Uploaded documents
    ├── data/                # ChromaDB persistence
    └── requirements.txt
```

## Setup Instructions

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+
- **OpenRouter API Key** (for OpenAI models)
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

2. **View Summary**:
   - After upload, an AI-generated summary appears automatically
   - Shows word count and line count

3. **Ask Questions**:
   - Type questions about your document in the query interface
   - Get AI-powered answers with source references in the format `[filename]:[line-start]-[line-end]`

4. **Explore Agent Suggestions**:
   - The autonomous agent analyzes your document and suggests follow-up actions
   - Click web search buttons to find additional context using Brave Search
   - View search results inline

## API Endpoints

### Documents
- `POST /api/documents/upload` - Upload and index a document
- `GET /api/documents/` - List all indexed documents

### Query
- `POST /api/query` - Query documents with RAG
  ```json
  {
    "question": "What is the main topic?",
    "top_k": 3
  }
  ```

### Summarization
- `POST /api/summarize` - Generate document summary
  ```json
  {
    "content": "document content here"
  }
  ```

### Agent
- `POST /api/agent/suggest` - Get action suggestions
- `POST /api/agent/search-suggestions` - Get web search query suggestions
- `POST /api/agent/web-search` - Perform web search via Brave API

## Key Features Explained

### RAG with Line References
The system chunks documents while tracking line numbers, so every answer includes precise source references:
```
Answer: The document discusses machine learning applications.
Sources:
  - introduction.txt:1-15
  - introduction.txt:45-60
```

### Autonomous Agent
The AI agent analyzes documents and suggests:
- Relevant follow-up research topics
- Web searches for additional context
- Actions to take based on document content

### MCP-Style Web Search
While using direct Brave Search API integration currently, the architecture supports future integration with proper MCP (Model Context Protocol) servers for enhanced tool capabilities.

## Development Notes

### Adding New MCP Tools
To add more MCP-style tools, edit `backend/app/services/mcp_tools.py` and register new tools in the `MCP_TOOLS` dictionary.

### Customizing the RAG Pipeline
Modify `backend/app/services/rag_service.py` to:
- Change chunk sizes
- Adjust retrieval parameters
- Modify prompts
- Use different embedding models

### Styling
The frontend uses Tailwind CSS with ShadCN UI components. Customize colors and themes in:
- `frontend/tailwind.config.js`
- `frontend/src/index.css`

## Troubleshooting

### Backend Issues

**Error: "PERPLEXITY_API_KEY not set"**
- Make sure you've created a `.env` file in the `backend/` directory
- Add your OpenRouter API key

**ChromaDB Permission Errors**
- Ensure the `backend/data/` directory is writable
- Try deleting `backend/data/chroma_db` and restarting

### Frontend Issues

**API Connection Failed**
- Make sure the backend is running on port 5177
- Check CORS settings in `backend/app/__init__.py`

**TypeScript Errors**
- Run `npm install` to ensure all dependencies are installed
- Check that `@types/node` is installed for path resolution

## Future Enhancements

- [ ] Support for PDF and DOCX files
- [ ] Multi-user support with authentication
- [ ] Document versioning and comparison
- [ ] Export summaries and insights to PDF
- [ ] Proper MCP server implementation
- [ ] Chat history persistence
- [ ] Real-time collaboration features

## License

MIT License - feel free to use this project for learning and portfolio purposes.

## Credits

Built with:
- [Haystack](https://haystack.deepset.ai/) for RAG orchestration
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [OpenRouter](https://openrouter.ai/) for LLM access
- [Brave Search](https://brave.com/search/api/) for web search
- [ShadCN UI](https://ui.shadcn.com/) for components
