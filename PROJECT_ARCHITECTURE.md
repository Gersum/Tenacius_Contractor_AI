# Project Architecture

The system is intentionally organized as a local, audit-friendly conversion engine:

```mermaid
flowchart TD
    A[Prospect Input] --> B[Enrichment Pipeline]
    B --> C[Hiring Signal Brief]
    B --> D[Competitor Gap Brief]
    C --> E[Grounding Policy]
    D --> E
    E --> F[Email Drafting]
    F --> G[Email Handler]
    G --> H[Inbound Reply]
    H --> I[Qualification]
    I --> J[Cal.com Booking]
    I --> K[SMS Scheduling Fallback]
    I --> L[HubSpot Sync]
    B --> M[Trace Logger]
    E --> M
    G --> M
    H --> M
    I --> M
    J --> M
    K --> M
    L --> M
```

The implementation keeps outbound traffic in sink mode until live providers are intentionally enabled. The runtime is designed around traceable artifacts rather than opaque side effects, so each operational step has a file-based evidence surface.
