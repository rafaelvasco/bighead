# Claude Code Project Guidelines

This document contains important rules and conventions for this project that Claude Code should follow.

## TypeScript Import Rules

### Separate Type Imports (REQUIRED)
All TypeScript type imports **must** use the `import type` syntax separately from value imports.

**Correct:**
```typescript
import { api } from '../services/api';
import type { Document, QueryResponse } from '../services/api';
```

**Incorrect:**
```typescript
import { api, Document, QueryResponse } from '../services/api';
```

This rule is enforced by ESLint using `@typescript-eslint/consistent-type-imports` with the `separate-type-imports` fix style.

## Project Structure

- **Frontend**: React + TypeScript + Vite application located in `frontend/`
- **Backend**: Python Flask API (assumed based on project context)

### Frontend Architecture

#### State Management
The application uses a **centralized Context + Hooks pattern** for state management:

**DocumentContext** (`frontend/src/contexts/DocumentContext.tsx`):
- Central store for all document-related state
- Manages: documents list, selected document, document content, summary, loading states, errors
- All state updates flow through this context

**useDocuments Hook** (`frontend/src/hooks/useDocuments.ts`):
- Custom hook that abstracts ALL API calls
- Automatically updates the DocumentContext when data changes
- Components should NEVER call the API directly - always use this hook
- Provides methods: `loadDocuments`, `uploadDocument`, `deleteDocument`, `selectDocument`, `queryDocuments`, `generateSummary`, etc.

**Component Guidelines**:
- All components access document data through the `useDocuments()` hook
- No props drilling - components get data directly from the context
- When an API action occurs (upload, delete, update), the context is automatically updated
- All components react to context changes automatically

## Code Style

- ESLint configuration is located at `frontend/eslint.config.js`
- Follow the TypeScript and React best practices enforced by the ESLint configuration
