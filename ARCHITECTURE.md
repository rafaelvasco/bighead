# BigHead - Architecture and Project Analysis

## Overview

BigHead is a full-stack AI-powered document analysis application that utilizes Retrieval-Augmented Generation (RAG) to enable users to upload documents, ask questions about them, generate summaries, and integrate web search capabilities. The application provides a modern user interface built with React/TypeScript and a robust Python Flask backend powered by advanced AI technologies.

## Core Functionality

1. **Document Management**: Upload, view, edit, and delete text/markdown documents
2. **AI-Powered Q&A**: Natural language queries about document content with source attribution
3. **Document Summarization**: Automatic AI generation of document summaries and key insights
4. **Chat Interface**: Persistent conversation history with documents
5. **Web Search Integration**: Brave Search API for additional context and information retrieval
6. **Admin Interface**: Database management and vector store inspection tools

## Project Architecture

### High-Level Architecture

The application follows a clean separation between frontend and backend:

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│                  React + TypeScript + Vite                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   UI Layer  │  │ State Mgmt  │  │     API Layer       │  │
│  │             │  │             │  │                     │  │
│  │ ShadCN UI   │  │   Context   │  │   HTTP Client       │  │
│  │ Components  │  │   + Hooks   │  │   (TypeScript)      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP/REST API
                                │
┌─────────────────────────────────────────────────────────────┐
│                          Backend                             │
│                    Python Flask Application                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    Routes   │  │  Services   │  │     Data Layer      │  │
│  │             │  │             │  │                     │  │
│  │   Blueprints│  │ Business    │  │  SQLite + ChromaDB  │  │
│  │   + CORS    │  │   Logic     │  │  Vector Store       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
                       ┌─────────────────┐
                       │ External APIs   │
                       │                 │
                       │ OpenRouter LLM  │
                       │ OpenAI Embed    │
                       │ Brave Search    │
                       └─────────────────┘
```

## Frontend Architecture

### State Management Pattern

The frontend uses a **centralized Context + Hooks pattern** for state management:

#### DocumentContext (`DocumentContext.tsx`)

- **Purpose**: Central state store for all document-related data
- **State Variables**:

  - `documents`: Array of all uploaded documents
  - `selectedDocument`: Currently selected document object
  - `documentContent`: Raw text content of selected document
  - `summary`: AI-generated summary of current document
  - `chatHistory`: Array of human/AI conversation messages
  - `isLoading`, `error`: Loading and error states

- **State Management Functions**:
  - `setDocuments`, `setSelectedDocument`, `setDocumentContent`
  - `setSummary`, `setChatHistory`, `setIsLoading`, `setError`
  - `selectDocumentByFilename`: Select document by filename
  - `addDocument`, `removeDocument`, `updateDocument`: CRUD operations
  - `clearSelection`: Clear all selection state

#### useDocuments Hook (`useDocuments.ts`)

- **Purpose**: Custom hook that abstracts ALL API calls and manages state updates
- **Key Functions**:
  - `loadDocuments()`: Fetch all documents from backend
  - `uploadDocument(file)`: Handle file upload and processing
  - `deleteDocument(filename)`: Remove document from system
  - `selectDocument(filename)`: Switch active document
  - `queryDocuments(question)`: Perform RAG query against document
  - `generateSummary(content)`: Generate AI summary
  - `updateDocumentContent(filename, content)`: Edit document content
  - `createFromSearch(query, filename)`: Create document from web search

### Component Architecture

The frontend follows a component-based architecture with clear separation of concerns:

#### UI Components (`/components/`)

1. **App.tsx**: Application router and layout manager

   - Manages navigation (Home, Document Dashboard, Admin)
   - Configures routing with React Router
   - Provides consistent header/footer layout

2. **DocumentUpload.tsx**

   - Drag-and-drop file upload interface
   - File validation (.txt, .md support)
   - Upload progress and status indicators
   - Automatic navigation after successful upload

3. **DocumentList.tsx**

   - Sidebar component showing all documents
   - Document selection and deletion
   - Loading states and error handling
   - Real-time document statistics (chunk count)

4. **QueryInterface.tsx**

   - Chat-style conversation interface
   - Message history display with source attribution
   - Real-time typing indicators
   - Interactive message input with keyboard shortcuts

5. **DocumentDashboard.tsx**

   - Main document workspace
   - Integrates editor and chat interface
   - Handles document selection and loading
   - Responsive layout with split-screen view

6. **DocumentEditor.tsx**

   - Advanced markdown/text editor
   - Syntax highlighting with CodeMirror
   - Real-time preview capabilities
   - Document statistics and metadata display

7. **DocumentSummary.tsx**

   - Display AI-generated summaries
   - Key insights visualization
   - Document statistics (word count, line count)

8. **CreateFromSearch.tsx**

   - Web search integration interface
   - Brave Search API integration
   - Document creation from search results

9. **AdminPage.tsx**
   - Database management interface
   - Vector store inspection tools
   - System monitoring and debugging

#### UI Foundation (`/components/ui/`)

- ShadCN UI component library
- Consistent design system
- Reusable UI primitives (Button, Card, Input, etc.)
- Accessible and responsive components

### API Layer (`/services/api.ts`)

**Type-safe API client** with comprehensive interface definitions:

- **Document Operations**: `uploadDocument`, `listDocuments`, `getDocument`, `updateDocument`, `deleteDocument`
- **Query Operations**: `queryDocuments` for RAG functionality
- **Summarization**: `summarizeDocument` for AI summaries
- **Admin Operations**: Database and vector store management endpoints
- **Type Definitions**: Comprehensive TypeScript interfaces for all API responses

**Key Features**:

- Automatic error handling with detailed error messages
- TypeScript type safety for all API responses
- Consistent request/response patterns
- Environment-based API URL configuration

### Frontend Build System

- **Vite**: Fast development server and optimized builds
- **TypeScript**: Static type checking and modern JavaScript features
- **Tailwind CSS**: Utility-first styling framework
- **ESLint**: Code quality and consistency enforcement

## Backend Architecture

### Application Structure

The backend follows a layered architecture with clear separation of concerns:

#### Flask Application Setup (`app/__init__.py`)

- Flask application factory pattern
- CORS configuration for frontend integration
- Blueprint registration for modular routing
- Environment configuration and logging setup
- Upload directory and data directory initialization

#### Configuration Management (`app/config.py`)

- Environment-based configuration
- API key management for external services
- Database path configuration
- Configuration validation at startup

#### Routing Layer (`app/routes/`)

**Modular Blueprint Architecture**:

1. **documents.py**: Document management endpoints

   - `POST /api/documents/upload`: Upload and index documents
   - `GET /api/documents/`: List all documents
   - `GET /api/documents/<filename>`: Get document content
   - `PUT /api/documents/<filename>`: Update document content
   - `DELETE /api/documents/<filename>`: Delete document
   - `POST /api/documents/create-from-search`: Create from web search
   - `GET /api/documents/<filename>/data`: Get document with chat history

2. **query.py**: RAG query endpoint

   - `POST /api/query`: Query documents with RAG pipeline

3. **summarize.py**: Document summarization

   - `POST /api/summarize`: Generate AI summaries

4. **admin.py**: System administration

   - Database table inspection
   - Data management operations
   - Vector store exploration tools
   - System debugging utilities

5. **health.py**: Application health check
   - System status verification
   - Service availability monitoring

#### Service Layer (`app/services/`)

**Business Logic Implementation**:

1. **rag_service.py**: Core RAG pipeline

   - Haystack integration for document processing
   - ChromaDB vector store management
   - OpenRouter LLM integration
   - OpenAI embedding service
   - Document chunking and indexing
   - Query processing and source retrieval

2. **document_service.py**: Document management

   - File upload processing and validation
   - Document CRUD operations
   - Web search integration
   - Content indexing and vectorization
   - File system operations

3. **query_service.py**: Query orchestration

   - RAG pipeline execution
   - Chat history management
   - Source attribution processing
   - Error handling and validation

4. **summarizer.py**: Document summarization

   - OpenRouter LLM integration
   - Summary generation with key insights
   - Document statistics calculation
   - Result formatting and storage

5. **mcp_tools.py**: Web search integration
   - Brave Search API integration
   - Web result processing
   - MCP (Model Context Protocol) tool simulation
   - External service error handling

#### Data Layer (`app/database/`)

**SQLite Database Service** (`database_service.py`):

- **document_ingest_data table**: Document metadata and summaries
- **chat_history table**: Conversation history with source references
- **Connection management**: Context-based connection handling
- **Database migration**: Automatic schema initialization
- **Data integrity**: Transaction management and error handling

### External Service Integration

1. **OpenRouter API**: LLM generation (GPT-4o-mini)

   - Document queries and summarization
   - Configurable model selection
   - Error handling and retry logic

2. **OpenAI API**: Document embeddings

   - Text vectorization for semantic search
   - High-quality embedding model
   - Rate limiting and quota management

3. **Brave Search API**: Web search capabilities

   - External information retrieval
   - Context-aware search results
   - Integration with document analysis

4. **ChromaDB**: Vector database
   - Document embeddings storage
   - Efficient similarity search
   - Persistent data storage
   - Collection management

## Frontend-Backend Interaction Flow

### Document Upload Workflow

```
Frontend                     Backend                    External APIs
    │                           │                            │
    │ POST /api/documents/upload │                            │
    │─────────────────────────►│                            │
    │                           │ Validate file              │
    │                           │ Extract content            │
    │                           │ Document metadata          │
    │                           │ Save to database            │
    │                           │ Index in ChromaDB           │
    │                           │ Generate embeddings         │
    │                           │─────────────────────────►   │ OpenAI
    │                           │◄──────────────────────────  │ (embeddings)
    │ ◄─────────────────────────│                        │
    │ Response with success      │                            │
```

### Query Workflow

```
Frontend                     Backend                    External APIs
    │                           │                            │
    │ POST /api/query           │                            │
    │─────────────────────────►│                            │
    │                           │ Validate document ID        │
    │                           │ Create question embedding   │
    │                           │─────────────────────────►   │ OpenAI
    │                           │◄──────────────────────────  │ (embeddings)
    │                           │ Search ChromaDB for relevant│
    │                           │ document chunks             │
    │                           │ Context-based LLM query     │
    │                           │─────────────────────────►   │ OpenRouter
    │                           │◄──────────────────────────  │ (LLM)
    │                           │ Save chat history            │
    │ ◄─────────────────────────│                            │
    │ Response with answer and │                            │
    │ source references        │                            │
```

### Data Consistency Patterns

1. **Optimistic UI Updates**: Frontend updates state immediately, then syncs with backend
2. **Error Rollback**: Failed operations revert frontend state with user notifications
3. **Automatic Refresh**: Critical operations trigger data reloads for consistency
4. **Context Synchronization**: Document selection automatically loads related data

### Error Handling Strategy

**Frontend Error Handling**:

- API request errors with user-friendly messages
- Network error detection and retry mechanisms
- Form validation with real-time feedback
- Global error state management in DocumentContext

**Backend Error Handling**:

- Validation decorators for request validation
- Exception handling middleware
- Detailed error logging with context
- Graceful degradation for external API failures

## Key Technologies and Their Roles

### Frontend Technologies

1. **React 19**: Component-based UI framework with modern hooks
2. **TypeScript**: Static typing for better code quality and maintainability
3. **Vite**: Fast development server and optimized production builds
4. **React Router**: Client-side routing for single-page application
5. **Tailwind CSS**: Utility-first CSS framework for rapid UI development
6. **ShadCN UI**: Component library with consistent design system
7. **CodeMirror**: Advanced code editor with syntax highlighting
8. **React Markdown**: Markdown rendering with GFM support

### Backend Technologies

1. **Flask**: Lightweight Python web framework
2. **SQLite**: Embedded database for document metadata and chat history
3. **ChromaDB**: Vector database for semantic search capabilities
4. **Haystack**: RAG pipeline orchestration framework
5. **OpenRouter API**: LLM generation service
6. **OpenAI API**: Text embedding generation
7. **Brave Search API**: Web search integration

### Development Tools

1. **ESLint**: Code quality and consistency enforcement
2. **Python Logging**: Comprehensive application logging
3. **Environment Variables**: Secure configuration management
4. **Factory Pattern**: Service instantiation and configuration

## Security Considerations

### Frontend Security

- Input sanitization for user queries
- File type validation and size limits
- XSS prevention through React's built-in protections
- Secure API communication with CORS

### Backend Security

- File upload validation and sandboxing
- SQL injection prevention through parameterized queries
- API key protection through environment variables
- Rate limiting considerations for external API usage
- Content Security Policy for frontend resources

## Performance Optimizations

### Frontend Optimizations

- Component memoization to prevent unnecessary re-renders
- Lazy loading for document content
- Efficient state management with minimal re-renders
- Code splitting for optimal bundle sizes

### Backend Optimizations

- Database connection pooling with context management
- Vector database indexing for fast similarity search
- Efficient document chunking strategies
- Caching of frequently accessed data
- Asynchronous operations where appropriate

## Scalability Considerations

### Current Limitations

- Single-server deployment architecture
- SQLite database scaling constraints
- File-based document storage
- In-memory processing for large documents

### Future Scaling Paths

- Database migration to PostgreSQL/MySQL
- Container-based deployment with Kubernetes
- Distributed vector storage (Pinecone, Weaviate)
- Cloud storage for document files
- Microservices architecture for different functional areas

## Development Workflow

### Project Setups

**Frontend Development**:

```bash
cd frontend
npm install
npm run dev  # Development server on http://localhost:5173
```

**Backend Development**:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py  # Development server on http://localhost:5177
```

### Code Organization

- **Type-first development**: TypeScript interfaces defined before implementation
- **Component composition**: Complex UI built from reusable primitives
- **Service-oriented architecture**: Clear separation between API, business logic, and data layers
- **Configuration management**: Environment-based configuration with validation

### Testing Strategy

- **Frontend**: Component testing with React Testing Library
- **Backend**: API endpoint testing with Flask test client
- **Integration**: Full-stack testing for critical workflows
- **External services**: Mock testing for API integrations

## Future Enhancement Opportunities

### Feature Enhancements

1. **Multi-format support**: PDF, DOCX, and other document formats
2. **Real-time collaboration**: Multiple users interacting with documents
3. **Advanced search**: Semantic search across document collections
4. **Document versioning**: Track changes and maintain document history
5. **Export capabilities**: PDF generation for summaries and insights
6. **User authentication**: Multi-tenant support with user management
7. **Advanced analytics**: Document usage patterns and insights

### Technical Improvements

1. **WebSocket support**: Real-time updates and notifications
2. **Background processing**: Asynchronous document processing
3. **Enhanced error handling**: More granular error recovery
4. **Performance monitoring**: Application performance metrics
5. **Automated testing**: Comprehensive test suite with CI/CD
6. **Container deployment**: Docker-based deployment configuration

### RAG Improvement Plan:

Proposed Fixes

1.  Improve Query Processing (High Priority)
    • Add automatic query expansion to include both time-based and entity-based terms
    • Implement multiple retrieval strategies for temporal queries
    • Use hybrid search combining semantic and keyword matching

2.  Optimize Chunking Strategy (Medium Priority)
    • Adjust chunk size to ensure related context stays together
    • Implement overlapping chunks to preserve context boundaries
    • Add semantic chunking based on document structure

3.  Enhance Retrieval (High Priority)
    • Increase default top_k from 3 to 5-10 for better coverage
    • Add re-ranking based on query relevance
    • Implement query-specific boost for temporal information

4.  Improve LLM Prompting (Medium Priority)
    • Add instructions for temporal reasoning
    • Provide guidance on synthesizing information from multiple chunks
    • Include confidence scoring mechanism

5.  Add Diagnostics (Low Priority)
    • Log retrieval scores for analysis
    • Add query similarity metrics
    • Implement fallback strategies for failed retrievals

Implementation Order

1.  Fix retrieval (increase top_k, add query expansion)
2.  Optimize chunking for better context preservation
3.  Improve LLM prompting for better synthesis
4.  Add diagnostics for future improvements
