# EstimateIQ Frontend Architecture Guide

**For Beginners: A Complete Walkthrough of How the UI Works**

---

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Core Concepts](#core-concepts)
5. [How the UI Works](#how-the-ui-works)
6. [Component Breakdown](#component-breakdown)
7. [State Management](#state-management)
8. [API Integration](#api-integration)
9. [User Workflows](#user-workflows)

---

## Overview

EstimateIQ's frontend is a **React-based web application** that allows users to:

1. **Upload** RFP documents (PDF, DOCX, XLSX)
2. **Monitor** processing progress in real-time
3. **Browse** extracted requirements by category
4. **Search** requirements using natural language
5. **View** requirement details with metadata

The frontend communicates with the backend API to fetch data and display it in an intuitive interface.

---

## Technology Stack

### Core Framework
- **React 18** — UI library for building interactive components
  - Component-based architecture
  - Hooks for state and side effects
  - Fast rendering with virtual DOM

- **TypeScript** — Typed JavaScript
  - Catches errors at compile time
  - Better IDE support and autocomplete
  - Safer refactoring

### Routing
- **React Router v6** — Client-side routing
  - Navigate between pages without full page reload
  - URL-based state (e.g., `/workspace/project-123`)
  - Nested routes for complex layouts

### State Management
- **Redux Toolkit** — Centralized state management
  - Single source of truth for app state
  - Predictable state updates
  - Time-travel debugging

- **RTK Query** — Data fetching and caching
  - Automatic API call management
  - Built-in caching and invalidation
  - Polling for real-time updates

### Styling
- **CSS-in-JS** — Inline styles (no CSS files)
  - Dynamic styling based on state
  - No CSS class naming conflicts
  - Easier component encapsulation

- **CSS Variables** — Theme colors and spacing
  - Dark mode support
  - Consistent design system
  - Easy theme switching

### Build Tools
- **Vite** — Fast build tool and dev server
  - Lightning-fast hot module replacement (HMR)
  - Optimized production builds
  - ES modules support

- **npm** — Package manager
  - Manages dependencies
  - Scripts for build, dev, test

---

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/              # Basic UI elements (buttons, inputs, etc.)
│   │   └── ...
│   │
│   ├── features/            # Feature-specific components
│   │   ├── discovery/       # Project creation/discovery
│   │   │   └── CreateProjectModal.tsx
│   │   ├── workspace/       # Main workspace
│   │   │   ├── panels/      # Workspace panels
│   │   │   │   ├── UploadPanel.tsx
│   │   │   │   ├── RequirementsPanel.tsx
│   │   │   │   ├── DocumentsPanel.tsx
│   │   │   │   └── EstimatePanel.tsx
│   │   │   └── WorkspaceLayout.tsx
│   │   └── ...
│   │
│   ├── services/            # API client code
│   │   ├── projectsApi.ts   # Project endpoints
│   │   ├── documentsApi.ts  # Document endpoints
│   │   ├── retrievalApi.ts  # Search endpoints
│   │   └── ...
│   │
│   ├── store/               # Redux state management
│   │   ├── slices/          # Redux slices (state + reducers)
│   │   │   ├── uploadSlice.ts
│   │   │   ├── workspaceSlice.ts
│   │   │   └── ...
│   │   └── index.ts         # Store configuration
│   │
│   ├── types/               # TypeScript type definitions
│   │   └── index.ts
│   │
│   ├── App.tsx              # Root component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
│
├── public/                  # Static assets
├── package.json             # Dependencies and scripts
├── tsconfig.json            # TypeScript configuration
└── vite.config.ts           # Vite configuration
```

---

## Core Concepts

### Components

A **component** is a reusable piece of UI. Think of it as a building block.

**Example:**
```typescript
// Button component
function Button({ label, onClick }) {
  return (
    <button onClick={onClick} style={{ padding: "8px 16px" }}>
      {label}
    </button>
  );
}

// Usage
<Button label="Upload" onClick={handleUpload} />
```

### Hooks

**Hooks** are functions that let you use React features in functional components.

**Common hooks:**
- `useState` — Manage component state
- `useEffect` — Run side effects (API calls, timers)
- `useParams` — Get URL parameters
- `useQuery` — Fetch data from API (RTK Query)

**Example:**
```typescript
function UploadPanel() {
  const [files, setFiles] = useState<File[]>([]);  // State
  const { slug } = useParams();  // Get URL param
  const { data } = useGetProjectStatusQuery(slug);  // Fetch data
  
  useEffect(() => {
    console.log("Component mounted");
  }, []);  // Run once on mount
  
  return <div>...</div>;
}
```

### Redux State

**Redux** is a centralized state management system. Instead of each component managing its own state, all state lives in one place.

**Example:**
```typescript
// Redux slice (state + reducers)
const uploadSlice = createSlice({
  name: "upload",
  initialState: {
    isUploading: false,
    isSuccess: false,
    uploadError: null,
  },
  reducers: {
    startUpload: (state) => {
      state.isUploading = true;
    },
    uploadSuccess: (state) => {
      state.isUploading = false;
      state.isSuccess = true;
    },
    uploadError: (state, action) => {
      state.isUploading = false;
      state.uploadError = action.payload;
    },
  },
});

// Usage in component
const dispatch = useAppDispatch();
const { isUploading } = useAppSelector((s) => s.upload);

dispatch(startUpload());
```

### RTK Query

**RTK Query** is a data fetching library that handles API calls, caching, and polling.

**Example:**
```typescript
// Define API endpoints
const projectsApi = createApi({
  reducerPath: "projectsApi",
  baseQuery: fetchBaseQuery({ baseUrl: "http://localhost:8000" }),
  endpoints: (builder) => ({
    listProjects: builder.query({
      query: () => "/projects",
    }),
    getProjectStatus: builder.query({
      query: (projectId) => `/projects/${projectId}/status`,
      pollingInterval: 2000,  // Poll every 2 seconds
    }),
  }),
});

// Usage in component
const { data, isLoading } = useGetProjectStatusQuery(projectId, {
  pollingInterval: 2000,  // Real-time updates
});
```

---

## How the UI Works

### User Flow: Upload and Monitor

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER LANDS ON HOMEPAGE                                   │
│    → Sees "Create Project" button                            │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│ 2. USER CLICKS "CREATE PROJECT"                             │
│    → Modal opens with project name input                     │
│    → User enters "My RFP" and clicks Create                  │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│ 3. FRONTEND CALLS API                                        │
│    POST /projects (name: "My RFP")                           │
│    → Backend creates project, returns project_id            │
│    → Frontend navigates to /workspace/project_id             │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│ 4. WORKSPACE LOADS                                           │
│    → UploadPanel shown                                       │
│    → User drags files or clicks to select                    │
│    → Files added to local state                              │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│ 5. USER CLICKS "UPLOAD"                                      │
│    → Frontend calls POST /upload (multipart/form-data)       │
│    → Backend receives files, creates documents              │
│    → Backend queues parsing tasks                            │
│    → Frontend receives project_id and job IDs                │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│ 6. PIPELINE VIEW SHOWN                                       │
│    → PipelineView component renders                          │
│    → Shows progress bars for each document                   │
│    → Polls GET /projects/{id}/status every 2 seconds         │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│ 7. REAL-TIME PROGRESS UPDATES                                │
│    → Backend processes documents                             │
│    → Frontend polls status endpoint                          │
│    → Progress bars update in real-time                       │
│    → Stage pills show completed/in-progress stages           │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│ 8. PROCESSING COMPLETE                                       │
│    → All documents show "embedded" status                    │
│    → "Documents Ready" message shown                         │
│    → User can now browse requirements                        │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│ 9. USER CLICKS "REQUIREMENTS" TAB                            │
│    → RequirementsPanel loads                                 │
│    → Calls GET /search/category?category=functional          │
│    → Backend returns requirements                            │
│    → Frontend displays in table format                       │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│ 10. USER SEARCHES                                            │
│     → Types "user authentication" in search box              │
│     → Clicks Search button                                   │
│     → Frontend calls POST /search (query: "...")             │
│     → Backend returns semantic search results                │
│     → Frontend displays matching requirements                │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### CreateProjectModal

**Purpose:** Allow users to create a new project.

**Location:** `frontend/src/features/discovery/CreateProjectModal.tsx`

**What it does:**
1. Shows a modal with a text input
2. User enters project name
3. On submit, calls `POST /projects`
4. Navigates to workspace on success

**Code structure:**
```typescript
export function CreateProjectModal() {
  const [projectName, setProjectName] = useState("");
  const [createProject, { isLoading }] = useCreateProjectMutation();
  
  const handleCreate = async () => {
    const result = await createProject({ name: projectName });
    navigate(`/workspace/${result.data.id}`);
  };
  
  return (
    <div className="modal">
      <input 
        value={projectName}
        onChange={(e) => setProjectName(e.target.value)}
        placeholder="Project name"
      />
      <button onClick={handleCreate} disabled={isLoading}>
        Create
      </button>
    </div>
  );
}
```

---

### UploadPanel

**Purpose:** Allow users to upload documents.

**Location:** `frontend/src/features/workspace/panels/UploadPanel.tsx`

**What it does:**
1. Shows drag-and-drop zone
2. Accepts PDF, DOCX, XLSX files
3. Displays selected files
4. On upload, calls `POST /upload`
5. Shows pipeline progress

**Key features:**
- **Drag and drop:** Users can drag files directly
- **File validation:** Only accepts .pdf, .docx, .xlsx
- **Progress tracking:** Shows real-time pipeline status
- **Error handling:** Displays upload errors

**Code structure:**
```typescript
export function UploadPanel() {
  const [localFiles, setLocalFiles] = useState<File[]>([]);
  const dispatch = useAppDispatch();
  const { isUploading, isSuccess } = useAppSelector((s) => s.upload);
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    setLocalFiles((prev) => [...prev, ...files]);
  };
  
  const handleUpload = () => {
    dispatch(uploadDocuments({ projectName: "RFP Upload", files: localFiles }));
  };
  
  if (isSuccess) {
    return <PipelineView />;
  }
  
  return (
    <div onDrop={handleDrop}>
      {/* Upload UI */}
    </div>
  );
}
```

---

### PipelineView

**Purpose:** Show real-time processing progress.

**Location:** `frontend/src/features/workspace/panels/UploadPanel.tsx` (nested component)

**What it does:**
1. Polls `GET /projects/{id}/status` every 2 seconds
2. Shows overall progress bar
3. Shows per-document cards with stage pills
4. Updates in real-time as backend processes

**Progress stages:**
- `uploaded` → 5%
- `parsed` → 30%
- `chunked` → 55%
- `classified` → 75%
- `embedded` → 100%

**Code structure:**
```typescript
function PipelineView({ projectId }: PipelineViewProps) {
  const { data, isLoading } = useGetProjectStatusQuery(projectId, {
    pollingInterval: 2000,  // Poll every 2 seconds
  });
  
  const allReady = data?.is_ready ?? false;
  const totalDocs = data?.total_documents ?? 0;
  const readyDocs = data?.ready_documents ?? 0;
  
  return (
    <div>
      <ProgressBar 
        current={readyDocs} 
        total={totalDocs}
      />
      {data?.documents.map((doc) => (
        <DocCard key={doc.document_id} doc={doc} />
      ))}
    </div>
  );
}
```

---

### RequirementsPanel

**Purpose:** Display extracted requirements with search and filtering.

**Location:** `frontend/src/features/workspace/panels/RequirementsPanel.tsx`

**What it does:**
1. Shows category tabs (Functional, Security, etc.)
2. Displays requirements in a table
3. Allows semantic search
4. Shows requirement details on click

**Key features:**
- **Category browsing:** Click tabs to filter by type
- **Semantic search:** Natural language search
- **Expandable rows:** Click to see full details
- **Metadata display:** Section, page, confidence score

**Categories:**
```
- Functional
- Non-Functional
- Security
- Integration
- UI/UX
- Workflow & Roles
- Data Validation
- Infrastructure
- Risks & Assumptions
- Open Questions
- Out of Scope
```

**Code structure:**
```typescript
export function RequirementsPanel() {
  const { slug: projectId } = useParams();
  const [activeCategory, setActiveCategory] = useState("functional");
  const [searchQuery, setSearchQuery] = useState("");
  
  // Browse by category
  const { data: categoryData } = useSearchByCategoryQuery(
    { projectId, category: activeCategory, topK: 100 },
    { skip: !!searchQuery }
  );
  
  // Semantic search
  const [triggerSearch, { data: searchData }] = useSearchMutation();
  
  const handleSearch = () => {
    triggerSearch({ projectId, query: searchQuery, topK: 50 });
  };
  
  const results = searchQuery ? searchData?.results : categoryData?.results;
  
  return (
    <div>
      {/* Category tabs */}
      {CATEGORIES.map((cat) => (
        <button onClick={() => setActiveCategory(cat.value)}>
          {cat.label}
        </button>
      ))}
      
      {/* Search bar */}
      <input 
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search requirements..."
      />
      
      {/* Results table */}
      {results?.map((item) => (
        <RequirementRow key={item.chunk_id} item={item} />
      ))}
    </div>
  );
}
```

---

### RequirementRow

**Purpose:** Display a single requirement in the table.

**Location:** `frontend/src/features/workspace/panels/RequirementsPanel.tsx` (nested component)

**What it does:**
1. Shows requirement ID, title, type, description
2. Expandable to show metadata
3. Color-coded by type

**Columns:**
- **ID:** Unique identifier (e.g., FR-001)
- **Requirement:** Section title
- **Type:** Category badge (color-coded)
- **Description:** Full requirement text

**Metadata (on expand):**
- Section name
- Page number
- Confidence score
- Similarity score

**Code structure:**
```typescript
function RequirementRow({ item, isLast }: Props) {
  const [expanded, setExpanded] = useState(false);
  
  const reqId = item.req_id || item.chunk_id.slice(0, 6);
  const title = item.title || item.section;
  const description = item.description || item.text;
  
  return (
    <div onClick={() => setExpanded(!expanded)}>
      {/* Main row */}
      <div style={{ display: "grid", gridTemplateColumns: "80px 160px 130px 1fr" }}>
        <div>{reqId}</div>
        <div>{title}</div>
        <TypeBadge label={item.type_label} />
        <div>{description}</div>
      </div>
      
      {/* Expanded metadata */}
      {expanded && (
        <div>
          <MetaTag label="Section" value={item.section} />
          <MetaTag label="Page" value={item.page_number} />
          <MetaTag label="Confidence" value={`${item.confidence_score * 100}%`} />
        </div>
      )}
    </div>
  );
}
```

---

### DocumentsPanel

**Purpose:** Show list of uploaded documents.

**Location:** `frontend/src/features/workspace/panels/DocumentsPanel.tsx`

**What it does:**
1. Lists all documents in the project
2. Shows file name, type, status
3. Allows re-processing or deletion

---

### EstimatePanel

**Purpose:** Show estimation results (future feature).

**Location:** `frontend/src/features/workspace/panels/EstimatePanel.tsx`

**What it does:**
1. Displays cost/effort estimates
2. Shows breakdown by category
3. Allows filtering and export

---

## State Management

### Redux Store Structure

```typescript
{
  upload: {
    isUploading: boolean,
    isSuccess: boolean,
    uploadError: string | null,
    currentProjectId: string | null,
    toastShown: boolean,
  },
  workspace: {
    activePanel: "upload" | "requirements" | "documents" | "estimate",
    selectedProject: string | null,
  },
}
```

### Redux Slices

**uploadSlice.ts:**
```typescript
const uploadSlice = createSlice({
  name: "upload",
  initialState: {
    isUploading: false,
    isSuccess: false,
    uploadError: null,
    currentProjectId: null,
    toastShown: false,
  },
  reducers: {
    startUpload: (state) => {
      state.isUploading = true;
      state.isSuccess = false;
      state.uploadError = null;
    },
    uploadSuccess: (state, action) => {
      state.isUploading = false;
      state.isSuccess = true;
      state.currentProjectId = action.payload;
    },
    uploadError: (state, action) => {
      state.isUploading = false;
      state.uploadError = action.payload;
    },
    resetUpload: (state) => {
      state.isUploading = false;
      state.isSuccess = false;
      state.uploadError = null;
      state.currentProjectId = null;
      state.toastShown = false;
    },
    markToastShown: (state) => {
      state.toastShown = true;
    },
  },
});
```

**workspaceSlice.ts:**
```typescript
const workspaceSlice = createSlice({
  name: "workspace",
  initialState: {
    activePanel: "upload",
    selectedProject: null,
  },
  reducers: {
    setActivePanel: (state, action) => {
      state.activePanel = action.payload;
    },
    setSelectedProject: (state, action) => {
      state.selectedProject = action.payload;
    },
  },
});
```

---

## API Integration

### RTK Query Setup

**Location:** `frontend/src/services/`

**Pattern:**
```typescript
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

export const projectsApi = createApi({
  reducerPath: "projectsApi",
  baseQuery: fetchBaseQuery({
    baseUrl: "http://localhost:8000",
  }),
  endpoints: (builder) => ({
    listProjects: builder.query({
      query: () => "/projects",
    }),
    createProject: builder.mutation({
      query: (body) => ({
        url: "/projects",
        method: "POST",
        body,
      }),
    }),
    getProjectStatus: builder.query({
      query: (projectId) => `/projects/${projectId}/status`,
      pollingInterval: 2000,
    }),
  }),
});

export const {
  useListProjectsQuery,
  useCreateProjectMutation,
  useGetProjectStatusQuery,
} = projectsApi;
```

### API Endpoints Used

**Projects:**
- `GET /projects` — List all projects
- `POST /projects` — Create new project
- `GET /projects/{id}` — Get project details
- `GET /projects/{id}/status` — Get processing status

**Upload:**
- `POST /upload` — Upload documents

**Search:**
- `POST /search` — Semantic search
- `GET /search/category` — Browse by category

**Documents:**
- `GET /documents/{id}` — Get document details
- `GET /documents/{id}/semantic-chunks` — Get chunks

---

## User Workflows

### Workflow 1: Upload and Browse

```
1. User clicks "Create Project"
2. Enters project name
3. Navigates to workspace
4. Drags files into upload zone
5. Clicks "Upload"
6. Watches progress in real-time
7. When complete, clicks "Requirements"
8. Browses requirements by category
```

### Workflow 2: Search Requirements

```
1. User is in Requirements panel
2. Types "user authentication" in search box
3. Clicks "Search"
4. Results appear instantly
5. Clicks on a requirement to expand
6. Sees full details and metadata
```

### Workflow 3: Filter by Category

```
1. User is in Requirements panel
2. Clicks "Security" tab
3. Table updates to show only security requirements
4. Can click on each requirement for details
5. Clicks "Functional" to switch categories
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `App.tsx` | Root component, routing setup |
| `main.tsx` | Entry point, renders App |
| `store/index.ts` | Redux store configuration |
| `store/slices/uploadSlice.ts` | Upload state management |
| `store/slices/workspaceSlice.ts` | Workspace state management |
| `services/projectsApi.ts` | Projects API endpoints |
| `services/documentsApi.ts` | Documents API endpoints |
| `services/retrievalApi.ts` | Search API endpoints |
| `features/discovery/CreateProjectModal.tsx` | Project creation |
| `features/workspace/panels/UploadPanel.tsx` | File upload |
| `features/workspace/panels/RequirementsPanel.tsx` | Requirements display |
| `features/workspace/panels/DocumentsPanel.tsx` | Document list |
| `features/workspace/panels/EstimatePanel.tsx` | Estimation view |

---

## Common Patterns

### Using a Query Hook

```typescript
// Fetch data
const { data, isLoading, error } = useGetProjectStatusQuery(projectId, {
  pollingInterval: 2000,  // Poll every 2 seconds
});

// Render
if (isLoading) return <div>Loading...</div>;
if (error) return <div>Error: {error.message}</div>;
return <div>{data?.total_documents} documents</div>;
```

### Using a Mutation Hook

```typescript
// Define mutation
const [createProject, { isLoading }] = useCreateProjectMutation();

// Call mutation
const handleCreate = async () => {
  const result = await createProject({ name: "My Project" });
  console.log(result.data);
};

// Render
<button onClick={handleCreate} disabled={isLoading}>
  {isLoading ? "Creating..." : "Create"}
</button>
```

### Accessing Redux State

```typescript
// Get state
const { isUploading } = useAppSelector((state) => state.upload);

// Dispatch action
const dispatch = useAppDispatch();
dispatch(startUpload());
```

### URL Parameters

```typescript
// Get URL params
const { slug: projectId } = useParams<{ slug: string }>();

// Navigate
navigate(`/workspace/${projectId}`);
```

---

## Debugging Tips

### Check Redux State
1. Install Redux DevTools browser extension
2. Open DevTools → Redux tab
3. See all state changes and actions

### Check Network Requests
1. Open browser DevTools → Network tab
2. Filter by "Fetch/XHR"
3. See all API calls and responses

### Check Component Props
1. Install React DevTools browser extension
2. Open DevTools → Components tab
3. Inspect component props and state

### Console Logging
```typescript
console.log("Debug:", { projectId, data, isLoading });
```

---

## Summary

The EstimateIQ frontend is a **React-based web application** that:

1. **Manages projects** — Create and organize RFP projects
2. **Uploads documents** — Drag-and-drop file upload
3. **Monitors progress** — Real-time pipeline status
4. **Displays requirements** — Browse and search extracted requirements
5. **Provides search** — Semantic search with natural language

**Key technologies:**
- React 18 (UI framework)
- TypeScript (type safety)
- Redux Toolkit (state management)
- RTK Query (data fetching)
- React Router (routing)
- Vite (build tool)

**Key insight:** The frontend is a thin client that communicates with the backend API. All heavy lifting (parsing, chunking, embedding) happens on the backend.

---

## Next Steps

- Read `BACKEND_ARCHITECTURE.md` to understand the API
- Explore the code in `frontend/src/features/` to see component implementations
- Check `frontend/src/services/` to see API integration patterns
- Run `npm run dev` to start the development server
