"""
Classification rules for the EstimateIQ requirement classifier.

Defines:
- CATEGORY_RULES: keyword lists per category used for scoring
- CATEGORY_PRIORITY: tie-break order (lower index = higher priority)
"""

CATEGORY_RULES: dict[str, list[str]] = {
    "integrations": [
        "api", "webhook", "oauth", "rest", "soap", "endpoint",
        "third-party", "integration", "connector", "sync",
    ],
    "non_functional": [
        "performance", "scalability", "availability", "latency", "throughput",
        "sla", "uptime", "response time", "load", "capacity",
    ],
    "workflow_roles": [
        "role", "approval", "access", "permission", "workflow", "escalation",
        "reviewer", "assignee", "stakeholder", "sign-off",
    ],
    "security_compliance": [
        "encryption", "authentication", "authorization", "compliance", "audit",
        "gdpr", "hipaa", "soc2", "pii", "certificate", "tls", "mfa",
    ],
    "ui_ux": [
        "ui", "ux", "screen", "dashboard", "form", "button", "layout",
        "page", "modal", "navigation", "frontend", "display", "view",
    ],
    "data_validation": [
        "validation", "format", "schema", "constraint", "required field",
        "data type", "input rule", "sanitize", "normalize",
    ],
    "infrastructure_deployment": [
        "docker", "kubernetes", "deployment", "ci/cd", "pipeline", "server",
        "cloud", "aws", "azure", "gcp", "infrastructure", "container", "environment",
    ],
    "risks_assumptions_dependencies": [
        "risk", "assumption", "dependency", "constraint", "blocker",
        "prerequisite", "caveat", "limitation",
    ],
    "open_questions": [
        "open question", "tbd", "to be determined", "unclear", "pending",
        "unknown", "to be confirmed", "tbc",
    ],
    "out_of_scope": [
        "out of scope", "not in scope", "excluded", "future phase",
        "not included", "descoped",
    ],
    "functional": [],  # default — no keywords needed
}

# Tie-break order: earlier position = higher priority
CATEGORY_PRIORITY: list[str] = [
    "security_compliance",
    "integrations",
    "non_functional",
    "workflow_roles",
    "ui_ux",
    "data_validation",
    "infrastructure_deployment",
    "risks_assumptions_dependencies",
    "open_questions",
    "out_of_scope",
    "functional",
]
