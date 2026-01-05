# Notera AI Agent Architecture

## LangGraph Workflow

```mermaid
graph TD
    START([User Message]) --> AGENT[Agent Node]
    AGENT --> EXTRACTOR[Extractor Node]
    EXTRACTOR --> END{Form Complete?}
    
    AGENT --> |Generate Response|
    EXTRACTOR --> |trustcall Extraction|
    |Generate Response| --> END
    
    style START fill:#e1f5fe
    style AGENT fill:#4ade80
    style EXTRACTOR fill:#457b9d
    style END fill:#ef4444
    
    subgraph Agent_Node
        A[System Prompt]
        B[Chat History]
        C[LLM GPT-4o]
        A --> B --> C
        D[Response Text]
        C --> D
    end
    
    subgraph Extractor_Node
        E[Conversation History]
        F[Existing Payload]
        G[trustcall Extractor]
        H[Dynamic Pydantic Schema]
        I[RFC-6902 JSON Patches]
        E --> F --> G --> H --> I
    end
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      User Input                          │
│                  (Text or Voice)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Dynamic Agent                            │
│  ┌────────────────────────────────────────────────────┐     │
│  │   System Prompt (Dynamic)                │     │
│  │   └─ Generated from FormConfig          │     │
│  └───────────────────────────────────────────────┘     │
│                  │                                    │
│  ┌───────────────────────────────────────────────┐    │
│  │   Chat History                         │    │
│  │   └─ Messages from conversation          │    │
│  └───────────────────────────────────────────────┘    │
│                  │                                    │
│  ┌───────────────────────────────────────────────┐    │
│  │   LLM (GPT-4o)                       │    │
│  │   └─ Converses naturally                 │    │
│  └───────────────────────────────────────────────┘    │
│                  │                                    │
└─────────────────────┼───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│              trustcall Extractor                          │
│  ┌──────────────────────────────────────────────────────┐     │
│  │   Conversation Context                 │     │
│  │   └─ Recent messages for extraction      │     │
│  └───────────────────────────────────────────────┘     │
│                  │                                    │
│  ┌───────────────────────────────────────────────┐    │
│  │   Existing Payload                   │    │
│  │   └─ Data collected so far            │    │
│  └───────────────────────────────────────────────┘     │
│                  │                                    │
│  ┌───────────────────────────────────────────────┐    │
│  │   Dynamic Schema                      │    │
│  │   └─ FormConfig → Pydantic Model       │    │
│  └───────────────────────────────────────────────┘     │
│                  │                                    │
│  ┌───────────────────────────────────────────────┐    │
│  │   trustcall                         │    │
│  │   └─ RFC-6902 JSON Patches          │    │
│  │     (Incremental updates)              │    │
│  └───────────────────────────────────────────────┘     │
└─────────────────────┼───────────────────────────────────────┘
                      │
                      ▼
              Updated Payload
```

## Components

| Component | Description | File |
|-----------|-------------|-------|
| **FormConfig** | Defines what data to collect, agent personality | `app/models/form_config.py` |
| **PromptGenerator** | Creates dynamic system prompts from FormConfig | `app/agents/prompt_generator.py` |
| **SchemaGenerator** | Generates Pydantic models for trustcall | `app/agents/schema_generator.py` |
| **DynamicAgent** | Main orchestration with LangGraph | `app/agents/dynamic_agent.py` |
| **trustcall** | Efficient JSON patch extraction | `trustcall` package |

## Key Features

- **Config-Driven**: Agent adapts to any FormConfig (7 industry templates)
- **Dynamic Prompts**: System prompts generated per form configuration
- **Dynamic Schemas**: Pydantic models created at runtime
- **Efficient Extraction**: trustcall uses RFC-6902 JSON patches
- **Real-Time Updates**: Payload updated incrementally during conversation
- **Form Completion**: Tracks required fields collected
