export interface Feature {
  name: string;
}

export interface Requirement {
  id: string;
  desc: string;
  priority: string;
  comp: string;
  category?: string;
  features?: Feature[];
}

export interface Module {
  title: string;
  type: string;
  desc: string;
}

export interface EstimateItem {
  item: string;
  defaultHrs: number;
}

export interface TimelineItem {
  task: string;
  length: string;
}

export interface Project {
  id: string;
  slug: string;
  name: string;
  desc: string;
  badge: string;
  statusClass: "b-active" | "b-pending" | "b-pipeline";
  progress: number;
  reqCount: number;
  requirements: Requirement[];
  modules: Module[];
  estimates: EstimateItem[];
  timeline: TimelineItem[];
  docs: string[];
}

/** Convert a project name to a URL-safe slug */
export function toSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .slice(0, 60);
}

export const REQ_TABS = [
  "Functional",
  "Non-Functional",
  "UI/UX",
  "Integrations",
  "Security & Compliance",
  "Data & Validation",
  "Workflow & Roles",
  "Infrastructure & Deployment",
  "Risks / Assumptions / Dependencies",
  "Open Questions",
  "Out of Scope",
] as const;

export type ReqTab = (typeof REQ_TABS)[number];

export const portfolioData: Project[] = [
  {
    id: "proj-bopc",
    slug: "bopc-cloud-core",
    name: "BOPC Cloud Core Refactoring Workflow",
    desc: "Migrating highly legacy system infrastructure models into high-availability multi-region cloud microservices instances with decoupled token structures.",
    badge: "Active Production", statusClass: "b-active", progress: 74, reqCount: 44,
    requirements: [
      { id: "REQ-001", desc: "Federated IAM authentication broker mapping corporate AD parameters safely.", priority: "Critical", comp: "High", category: "Functional", features: [
        { name: "Login with SSO / AD" }, { name: "Logout & session termination" }, { name: "MFA enforcement" }, { name: "Token refresh flow" }, { name: "Role assignment on login" },
      ]},
      { id: "REQ-002", desc: "Persistent multi-region storage systems executing absolute snapshots.", priority: "High", comp: "Medium", category: "Infrastructure & Deployment", features: [
        { name: "Snapshot scheduler" }, { name: "Cross-region replication" }, { name: "Snapshot restore UI" }, { name: "Storage health dashboard" },
      ]},
      { id: "REQ-003", desc: "System must maintain 99.9% uptime SLA across all regions.", priority: "High", comp: "High", category: "Non-Functional", features: [
        { name: "Health check endpoints" }, { name: "Auto-failover configuration" }, { name: "Uptime monitoring alerts" },
      ]},
      { id: "REQ-004", desc: "Admin dashboard with role-based access control for operations team.", priority: "Medium", comp: "Medium", category: "UI/UX", features: [
        { name: "Admin dashboard layout" }, { name: "User management table" }, { name: "Role assignment UI" }, { name: "Permission matrix view" }, { name: "Audit log viewer" },
      ]},
      { id: "REQ-005", desc: "Integration with existing Salesforce CRM for customer data sync.", priority: "High", comp: "High", category: "Integrations", features: [
        { name: "Salesforce OAuth connection" }, { name: "Contact sync pipeline" }, { name: "Sync conflict resolution" }, { name: "Sync status dashboard" },
      ]},
      { id: "REQ-006", desc: "All data encrypted at rest using AES-256 and in transit via TLS 1.3.", priority: "Critical", comp: "Medium", category: "Security & Compliance", features: [
        { name: "Encryption key management" }, { name: "TLS certificate setup" }, { name: "Compliance audit report" },
      ]},
      { id: "REQ-007", desc: "Input validation on all API endpoints with schema enforcement.", priority: "High", comp: "Low", category: "Data & Validation", features: [
        { name: "Request schema validation" }, { name: "Error response formatting" }, { name: "Validation unit tests" },
      ]},
      { id: "REQ-008", desc: "Multi-tier approval workflow for infrastructure provisioning requests.", priority: "Medium", comp: "Medium", category: "Workflow & Roles", features: [
        { name: "Request submission form" }, { name: "Approver notification" }, { name: "Approval / rejection flow" }, { name: "Workflow status tracker" },
      ]},
      { id: "REQ-009", desc: "Kubernetes cluster deployment on AWS EKS with auto-scaling policies.", priority: "High", comp: "High", category: "Infrastructure & Deployment", features: [
        { name: "EKS cluster setup" }, { name: "Auto-scaling policy config" }, { name: "Namespace isolation" }, { name: "Deployment pipeline (CI/CD)" },
      ]},
      { id: "REQ-010", desc: "Migration timeline assumes zero downtime — risk if legacy DB schema differs.", priority: "High", comp: "High", category: "Risks / Assumptions / Dependencies", features: [
        { name: "Schema diff analysis" }, { name: "Rollback plan documentation" }, { name: "Blue-green deployment setup" },
      ]},
      { id: "REQ-011", desc: "What is the expected peak concurrent user load for the new system?", priority: "Medium", comp: "Low", category: "Open Questions", features: [
        { name: "Load testing spike analysis" }, { name: "Capacity planning doc" },
      ]},
      { id: "REQ-012", desc: "Legacy monolith reporting module will not be migrated in this phase.", priority: "Low", comp: "Low", category: "Out of Scope", features: [
        { name: "Reporting module stub" },
      ]},
    ],
    modules: [
      { title: "Authentication Broker Layer", type: "Security System", desc: "Enterprise Single Sign-On router with security assertion token processing." },
      { title: "Data Snapshot Mesh Hub", type: "Infrastructure Core", desc: "High velocity replication cluster mapping active transactional pools." },
    ],
    estimates: [
      { item: "Core Infrastructure Architecture Integration", defaultHrs: 180 },
      { item: "Identity Propagation Blueprinting", defaultHrs: 95 },
    ],
    timeline: [
      { task: "Phase 1 Baseline Orchestration", length: "75%" },
      { task: "IAM Boundary Deployment Testing", length: "40%" },
    ],
    docs: ["BOPC_Cloud_Migration_Specs_v4.pdf", "Target_Cloud_Architecture_V2.docx"],
  },
  {
    id: "proj-nexus",
    slug: "nexus-headless-storefront",
    name: "Nexus Headless Distributed Storefront",
    desc: "Re-platforming traditional web retail structures onto edge serverless routines aiming for ultra-low latency response vectors globally.",
    badge: "In Validation", statusClass: "b-pipeline", progress: 42, reqCount: 29,
    requirements: [
      { id: "REQ-101", desc: "Real-time edge inventory reconciliation and programmatic buffer protection checks.", priority: "High", comp: "High", category: "Functional", features: [
        { name: "Inventory sync worker" }, { name: "Buffer overflow protection" }, { name: "Stock level alerts" }, { name: "Inventory audit log" },
      ]},
      { id: "REQ-102", desc: "Headless cart compilation matrices routing seamlessly via global Stripe microservices APIs.", priority: "Critical", comp: "Low", category: "Integrations", features: [
        { name: "Stripe checkout integration" }, { name: "Cart API endpoints" }, { name: "Payment webhook handler" }, { name: "Refund flow" },
      ]},
      { id: "REQ-103", desc: "Page load time must be under 100ms globally via CDN edge nodes.", priority: "Critical", comp: "High", category: "Non-Functional", features: [
        { name: "CDN configuration" }, { name: "Asset compression pipeline" }, { name: "Performance monitoring" },
      ]},
    ],
    modules: [
      { title: "Global Inventory Cache Node", type: "Edge Daemon", desc: "Low-overhead regional check worker validating inventory updates dynamically." },
      { title: "Cart Transaction Micro-Engine", type: "Serverless Router", desc: "Isolated functional task stack firing stateless settlement requests." },
    ],
    estimates: [
      { item: "Edge Cache Sync Implementation", defaultHrs: 140 },
      { item: "Stripe API Webhook Interfacing", defaultHrs: 80 },
    ],
    timeline: [
      { task: "Edge Sync Discovery Audits", length: "45%" },
      { task: "Integration Pipeline Validation", length: "60%" },
    ],
    docs: ["Nexus_Headless_Requirements_Doc.xlsx", "Global_Stripe_Integration_Flow.txt"],
  },
  {
    id: "proj-apex",
    slug: "apex-telemetry-streamer",
    name: "Apex Telemetry Operational Streamer",
    desc: "Aggregating industrial hardware analytics feeds into continuous visualization layout clusters with dynamic data pipeline validation loops.",
    badge: "Pending Audit", statusClass: "b-pending", progress: 15, reqCount: 18,
    requirements: [
      { id: "REQ-201", desc: "Ingesting raw metrics buffers with automatic dropouts for stale payload values.", priority: "Medium", comp: "Medium", category: "Functional", features: [
        { name: "Metrics ingestion API" }, { name: "Stale data cleanup job" }, { name: "Buffer overflow handler" }, { name: "Ingestion status dashboard" },
      ]},
    ],
    modules: [{ title: "Kafka Event Broker Aggregator", type: "Pipeline Block", desc: "Ingestion gateway processing payload batches per second safely." }],
    estimates: [{ item: "Broker Configuration Optimization", defaultHrs: 140 }],
    timeline: [{ task: "Ingestion Stress Verification Test", length: "20%" }],
    docs: ["Data_Ingestion_Format_Specs.csv"],
  },
  {
    id: "proj-titan",
    slug: "titan-fleet-routing",
    name: "Titan Fleet Routing Logistics Matrix",
    desc: "Geospatial telemetry pipeline updating algorithmic driver routing patterns based on immediate regional asset density fluctuations.",
    badge: "Active Production", statusClass: "b-active", progress: 61, reqCount: 52,
    requirements: [
      { id: "REQ-301", desc: "Continuous coordinate tracking via micro-location client telemetry feeds.", priority: "High", comp: "High", category: "Functional", features: [
        { name: "GPS telemetry receiver" }, { name: "Route calculation engine" }, { name: "Driver location map view" }, { name: "ETA prediction model" }, { name: "Geofence alerts" },
      ]},
    ],
    modules: [{ title: "Geospatial Route Calculation Hub", type: "Math Processing Core", desc: "Main matrix generation script calculating step distances dynamically." }],
    estimates: [{ item: "Matrix Optimization Engineering", defaultHrs: 220 }],
    timeline: [{ task: "GIS Matrix Integration Suite", length: "70%" }],
    docs: ["Fleet_Coordinate_API.pdf"],
  },
  {
    id: "proj-vanguard",
    slug: "vanguard-hipaa-records",
    name: "Vanguard Health HIPAA Records Hub",
    desc: "Upgrading operational electronic patient data ingestion systems to match modern compliance encryption standards safely.",
    badge: "Active Production", statusClass: "b-active", progress: 89, reqCount: 65,
    requirements: [
      { id: "REQ-401", desc: "Encrypting operational records both during active transit and rest environments.", priority: "Critical", comp: "High", category: "Security & Compliance", features: [
        { name: "AES-256 encryption at rest" }, { name: "TLS 1.3 in-transit setup" }, { name: "Key rotation scheduler" }, { name: "HIPAA audit trail" }, { name: "PHI access logging" },
      ]},
    ],
    modules: [{ title: "Cryptographic Envelope Controller", type: "Security Block", desc: "Hardware security module connector managing rotating system master keys." }],
    estimates: [{ item: "Cryptographic Key Integration Architecture", defaultHrs: 160 }],
    timeline: [{ task: "Security Validation Audit Execution", length: "90%" }],
    docs: ["HIPAA_Compliance_Matrix.pdf"],
  },
  {
    id: "proj-aurora",
    slug: "aurora-firmware-grid",
    name: "Aurora Hardware Ambient Firmware Grid",
    desc: "Deploying automated over-the-air safe firmware compilation patches to isolated edge hardware units seamlessly.",
    badge: "In Validation", statusClass: "b-pipeline", progress: 30, reqCount: 22,
    requirements: [
      { id: "REQ-501", desc: "Differential file transmission optimizing packet transfers safely.", priority: "Low", comp: "Medium", category: "Functional", features: [
        { name: "Binary diff generator" }, { name: "Patch upload endpoint" }, { name: "Checksum verification" }, { name: "Rollback on failure" },
      ]},
    ],
    modules: [{ title: "Binary Diff Patch Manager", type: "Hardware Utility", desc: "Client side payload extraction scripts validating file checksum hashes." }],
    estimates: [{ item: "Differential Assembly Routines", defaultHrs: 210 }],
    timeline: [{ task: "Firmware Packet Prototyping", length: "40%" }],
    docs: ["Microchip_Architecture_Limits.txt"],
  },
  {
    id: "proj-starlight",
    slug: "starlight-crm-workspace",
    name: "Starlight CRM Experience Workspace",
    desc: "Consolidating disparate organizational contact platforms into an adaptive dashboard interface optimized for agent ticketing flows.",
    badge: "Pending Audit", statusClass: "b-pending", progress: 5, reqCount: 12,
    requirements: [
      { id: "REQ-601", desc: "Unified workspace feeds consolidating system channel interactions.", priority: "Medium", comp: "Low", category: "Functional", features: [
        { name: "Unified inbox view" }, { name: "Channel filter sidebar" }, { name: "Ticket assignment flow" }, { name: "Agent status indicator" }, { name: "Conversation history" },
      ]},
    ],
    modules: [{ title: "Omnichannel Pipeline Component", type: "UI View Layout", desc: "Reactive dashboard layout syncing external support requests securely." }],
    estimates: [{ item: "UI Grid Interface Implementation", defaultHrs: 90 }],
    timeline: [{ task: "Visual Interface Iteration Loops", length: "10%" }],
    docs: ["CX_Consolidation_Scope.docx"],
  },
  {
    id: "proj-quantum",
    slug: "quantum-asset-ledger",
    name: "Quantum Distributed Asset Ledger",
    desc: "Constructing zero-trust append-only transaction ledger nodes to coordinate complex internal cross-border fiscal adjustments.",
    badge: "Active Production", statusClass: "b-active", progress: 55, reqCount: 41,
    requirements: [
      { id: "REQ-701", desc: "Cryptographic append-only chain integrity checking verification structures.", priority: "Critical", comp: "High", category: "Security & Compliance", features: [
        { name: "Block hash generator" }, { name: "Chain integrity verifier" }, { name: "Append-only write API" }, { name: "Tamper detection alerts" }, { name: "Ledger audit export" },
      ]},
    ],
    modules: [{ title: "Immutable Chain State Manager", type: "Ledger Pipeline", desc: "Block hash generator logic storing historical data sequence changes safely." }],
    estimates: [{ item: "Ledger Pipeline Development Block", defaultHrs: 310 }],
    timeline: [{ task: "Chain Mechanism Stress Checks", length: "50%" }],
    docs: ["Ledger_Accounting_Rules.xlsx"],
  },
  {
    id: "proj-horizon",
    slug: "horizon-spatial-mapping",
    name: "Horizon Spatial Mapping Layout",
    desc: "High density coordinate engine compiling layered topographic property metadata onto live interactive mapping assets.",
    badge: "In Validation", statusClass: "b-pipeline", progress: 38, reqCount: 17,
    requirements: [
      { id: "REQ-801", desc: "Dynamic interactive spatial loading rendering high density vector boundaries.", priority: "High", comp: "Medium", category: "Functional", features: [
        { name: "Map tile renderer" }, { name: "Vector polygon overlay" }, { name: "Property detail popup" }, { name: "Layer toggle controls" }, { name: "Coordinate search" },
      ]},
    ],
    modules: [{ title: "Vector Polygon Map Core", type: "GIS Client", desc: "Hardware accelerated layer mapping localized commercial region coordinates." }],
    estimates: [{ item: "Vector Render Engineering Framework", defaultHrs: 145 }],
    timeline: [{ task: "Polygon Boundary Calibration Steps", length: "30%" }],
    docs: ["Commercial_Map_Data.csv"],
  },
];
