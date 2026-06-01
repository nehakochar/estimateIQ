# EstimateIQ Documentation Index

**Complete Guide to Understanding the System**

---

## 📚 Documentation Files

### 1. **ARCHITECTURE_SUMMARY.md** ⭐ START HERE
**Quick reference guide for the entire system**

- What is EstimateIQ?
- Complete data flow diagram
- Key technologies overview
- Processing stages
- Common tasks
- Troubleshooting tips

**Best for:** Getting a quick overview, understanding the big picture

**Read time:** 10-15 minutes

---

### 2. **BACKEND_ARCHITECTURE.md** 🔧 DETAILED BACKEND
**Complete guide to how the backend works**

**Sections:**
- Overview and big picture
- Technology stack (FastAPI, PostgreSQL, Qdrant, Celery, etc.)
- Detailed pipeline phases:
  - Phase 1: Parsing (PDF, DOCX, XLSX)
  - Phase 2: Chunking (split into sections)
  - Phase 3: Semantic Chunking (AI-powered splitting)
  - Phase 4: Classification (label by type)
  - Phase 5: Embedding (convert to vectors)
  - Phase 6: Storage (save to databases)
- Database schema
- API endpoints
- Complete data flow example
- Key concepts explained

**Best for:** Understanding how documents are processed, learning the backend architecture

**Read time:** 30-40 minutes

---

### 3. **FRONTEND_ARCHITECTURE.md** 🎨 DETAILED FRONTEND
**Complete guide to how the frontend works**

**Sections:**
- Overview and user interface
- Technology stack (React, TypeScript, Redux, RTK Query, etc.)
- Project structure
- Core concepts:
  - Components
  - Hooks
  - Redux state
  - RTK Query
- How the UI works (complete user flow)
- Component breakdown:
  - CreateProjectModal
  - UploadPanel
  - PipelineView
  - RequirementsPanel
  - RequirementRow
  - DocumentsPanel
  - EstimatePanel
- State management
- API integration
- User workflows
- Debugging tips

**Best for:** Understanding the user interface, learning React patterns, debugging frontend issues

**Read time:** 30-40 minutes

---

## 🎯 Reading Paths

### Path 1: I'm New to the Project
1. Read **ARCHITECTURE_SUMMARY.md** (10 min)
2. Read **BACKEND_ARCHITECTURE.md** (30 min)
3. Read **FRONTEND_ARCHITECTURE.md** (30 min)
4. Explore code in `backend/app/` and `frontend/src/`

**Total time:** ~2 hours

---

### Path 2: I'm a Backend Developer
1. Read **ARCHITECTURE_SUMMARY.md** (10 min)
2. Read **BACKEND_ARCHITECTURE.md** (30 min)
3. Explore `backend/app/services/`
4. Check API endpoints in `backend/app/api/routes/`

**Total time:** ~1 hour

---

### Path 3: I'm a Frontend Developer
1. Read **ARCHITECTURE_SUMMARY.md** (10 min)
2. Read **FRONTEND_ARCHITECTURE.md** (30 min)
3. Explore `frontend/src/features/`
4. Check API integration in `frontend/src/services/`

**Total time:** ~1 hour

---

### Path 4: I Need to Fix a Bug
1. Read **ARCHITECTURE_SUMMARY.md** (10 min)
2. Identify if it's backend or frontend
3. Read relevant detailed guide (30 min)
4. Check troubleshooting section
5. Explore relevant code

**Total time:** ~1 hour

---

### Path 5: I Need to Add a Feature
1. Read **ARCHITECTURE_SUMMARY.md** (10 min)
2. Read both detailed guides (60 min)
3. Understand the complete flow
4. Plan where to add the feature
5. Implement and test

**Total time:** ~2 hours

---

## 🔍 Quick Lookup

### I want to understand...

**How documents are processed:**
→ Read BACKEND_ARCHITECTURE.md → "Detailed Pipeline Phases"

**How the UI displays requirements:**
→ Read FRONTEND_ARCHITECTURE.md → "RequirementsPanel"

**How real-time progress works:**
→ Read FRONTEND_ARCHITECTURE.md → "PipelineView"

**How semantic search works:**
→ Read BACKEND_ARCHITECTURE.md → "Key Concepts Explained" → "What is Semantic Search?"

**How embeddings are generated:**
→ Read BACKEND_ARCHITECTURE.md → "Phase 5: Embedding"

**How Redux state works:**
→ Read FRONTEND_ARCHITECTURE.md → "State Management"

**How API calls are made:**
→ Read FRONTEND_ARCHITECTURE.md → "API Integration"

**How files are parsed:**
→ Read BACKEND_ARCHITECTURE.md → "Phase 1: Parsing"

**How chunks are created:**
→ Read BACKEND_ARCHITECTURE.md → "Phase 2: Chunking"

**How requirements are classified:**
→ Read BACKEND_ARCHITECTURE.md → "Phase 4: Classification"

**How the database is structured:**
→ Read BACKEND_ARCHITECTURE.md → "Database Schema"

---

## 📊 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER UPLOADS FILE                         │
│                   (PDF, DOCX, XLSX)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
   ┌─────────────┐              ┌──────────────────┐
   │   FRONTEND  │              │     BACKEND      │
   │   (React)   │◄────────────►│   (FastAPI)      │
   └─────────────┘              └──────────────────┘
        │                                 │
        │                    ┌────────────┼────────────┐
        │                    │            │            │
        │                    ▼            ▼            ▼
        │              ┌────────┐  ┌────────┐  ┌────────┐
        │              │Parsing │  │Chunking│  │Classify│
        │              └────────┘  └────────┘  └────────┘
        │                    │            │            │
        │                    └────────────┼────────────┘
        │                                 │
        │                    ┌────────────┼────────────┐
        │                    │            │            │
        │                    ▼            ▼            ▼
        │              ┌────────┐  ┌────────┐  ┌────────┐
        │              │Semantic│  │Embedding│ │Storage │
        │              │Chunking│  │         │  │        │
        │              └────────┘  └────────┘  └────────┘
        │                                 │
        │                    ┌────────────┴────────────┐
        │                    │                         │
        │                    ▼                         ▼
        │              ┌──────────────┐        ┌──────────────┐
        │              │ PostgreSQL   │        │   Qdrant     │
        │              │ (Relational) │        │   (Vector)   │
        │              └──────────────┘        └──────────────┘
        │                    │                         │
        └────────────────────┼─────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
              ┌──────────┐      ┌──────────┐
              │  Browse  │      │  Search  │
              │Requirements│    │Requirements│
              └──────────┘      └──────────┘
```

---

## 🛠️ Technology Stack at a Glance

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Web Framework | FastAPI | REST API |
| Database | PostgreSQL | Structured data |
| Vector DB | Qdrant | Embeddings |
| Task Queue | Celery | Async processing |
| Message Broker | Redis | Task queue |
| PDF Parsing | PyMuPDF | Extract from PDFs |
| DOCX Parsing | python-docx | Extract from Word |
| XLSX Parsing | openpyxl | Extract from Excel |
| Text Processing | LlamaIndex | Chunking & splitting |
| Embeddings | Sentence Transformers | AI vectors |
| ORM | SQLAlchemy | Database mapping |

### Frontend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| UI Framework | React 18 | User interface |
| Language | TypeScript | Type safety |
| Routing | React Router | Page navigation |
| State | Redux Toolkit | Global state |
| Data Fetching | RTK Query | API calls |
| Build Tool | Vite | Fast builds |
| Package Manager | npm | Dependencies |

---

## 📁 Key Directories

### Backend
```
backend/
├── app/
│   ├── main.py                    # FastAPI app
│   ├── core/                      # Configuration
│   ├── api/routes/                # API endpoints
│   ├── services/                  # Business logic
│   │   ├── parsers/               # File parsing
│   │   ├── chunking/              # Document chunking
│   │   ├── semantic_chunking/     # AI-powered splitting
│   │   ├── classification/        # Requirement classification
│   │   ├── embeddings/            # AI embeddings
│   │   └── retrieval/             # Search
│   ├── models/                    # Database models
│   └── schemas/                   # API schemas
├── tasks/                         # Celery tasks
└── requirements.txt               # Dependencies
```

### Frontend
```
frontend/
├── src/
│   ├── App.tsx                    # Root component
│   ├── main.tsx                   # Entry point
│   ├── features/                  # Feature components
│   │   ├── discovery/             # Project creation
│   │   └── workspace/             # Main workspace
│   │       └── panels/            # Workspace panels
│   ├── services/                  # API clients
│   ├── store/                     # Redux state
│   │   └── slices/                # Redux slices
│   └── types/                     # TypeScript types
├── package.json                   # Dependencies
└── vite.config.ts                 # Build config
```

---

## 🚀 Getting Started

### 1. Read the Documentation
- Start with **ARCHITECTURE_SUMMARY.md**
- Then read the detailed guide for your area

### 2. Set Up Locally
```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### 3. Explore the Code
- Backend: `backend/app/services/`
- Frontend: `frontend/src/features/`

### 4. Test the System
- Upload a test PDF
- Monitor processing
- Search requirements
- View results

---

## 📖 Document Descriptions

### ARCHITECTURE_SUMMARY.md
**Length:** ~5 pages  
**Difficulty:** Beginner  
**Content:** High-level overview, quick reference  
**Best for:** Getting oriented, quick lookups

### BACKEND_ARCHITECTURE.md
**Length:** ~15 pages  
**Difficulty:** Intermediate  
**Content:** Detailed backend explanation, code examples  
**Best for:** Backend developers, understanding processing pipeline

### FRONTEND_ARCHITECTURE.md
**Length:** ~15 pages  
**Difficulty:** Intermediate  
**Content:** Detailed frontend explanation, component breakdown  
**Best for:** Frontend developers, understanding UI architecture

---

## ❓ FAQ

**Q: Where do I start?**  
A: Read ARCHITECTURE_SUMMARY.md first, then choose your path based on your role.

**Q: How long does it take to understand the system?**  
A: 1-2 hours for a complete overview, depending on your background.

**Q: Can I understand just the frontend or just the backend?**  
A: Yes, but understanding both helps. Start with ARCHITECTURE_SUMMARY.md, then read your specific guide.

**Q: Where's the code?**  
A: Backend code is in `backend/app/`, frontend code is in `frontend/src/`.

**Q: How do I debug issues?**  
A: Check the troubleshooting section in ARCHITECTURE_SUMMARY.md, then read the relevant detailed guide.

**Q: How do I add a new feature?**  
A: Read both detailed guides to understand the complete flow, then plan where to add it.

---

## 🔗 Related Resources

- **API Documentation:** `http://localhost:8000/docs` (when backend is running)
- **Code:** `backend/app/` and `frontend/src/`
- **Configuration:** `.env` file
- **Database:** PostgreSQL on `localhost:5432`
- **Vector DB:** Qdrant on `localhost:6333`

---

## 📝 Notes

- All documentation is written for beginners
- Code examples are included throughout
- Diagrams help visualize complex concepts
- Each document can be read independently
- Cross-references link related topics

---

## 🎓 Learning Outcomes

After reading these documents, you will understand:

✅ What EstimateIQ does and why  
✅ How documents flow through the system  
✅ How the backend processes files  
✅ How the frontend displays results  
✅ How the databases store data  
✅ How the API connects frontend and backend  
✅ How to add new features  
✅ How to debug issues  
✅ The technology stack and why each tool is used  
✅ The complete architecture and data flow  

---

## 📞 Support

If you have questions:
1. Check the relevant documentation file
2. Search for your topic in the index
3. Look at the code examples
4. Check the troubleshooting section

---

**Last Updated:** June 1, 2026  
**Version:** 1.0  
**Audience:** EstimateIQ Development Team  
**Status:** Complete and Ready to Use
