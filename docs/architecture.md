# LAAF Architecture

## Overview

LAAF (Logic-layer Automated Attack Framework) is structured in six horizontal layers that mirror the LPCI lifecycle.

```
┌─────────────────────────────────────────────────────────┐
│                    CLI / REST API                        │
│            laaf/cli/main.py  |  laaf/api/               │
├─────────────────────────────────────────────────────────┤
│                  Stage Engine (PSB)                      │
│      laaf/core/engine.py  |  laaf/core/stage_breaker.py │
├───────────────────────┬─────────────────────────────────┤
│   Payload Generator   │       Mutation Engine            │
│  laaf/generators/     │     laaf/core/mutator.py         │
├───────────────────────┴─────────────────────────────────┤
│                 Taxonomy (49 techniques)                 │
│  encoding  structural  semantic  layered  triggers  exfiltration │
├─────────────────────────────────────────────────────────┤
│              Platform Adapters                           │
│  OpenAI  Anthropic  Google  HF  OpenRouter  Mock        │
├─────────────────────────────────────────────────────────┤
│              Reporting                                   │
│         CSV  JSON  HTML  PDF                             │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### Persistent Stage Breaker (PSB)
`laaf/core/stage_breaker.py` — implements Eq. 2 from the paper:

```
p*_i = argmin_{p ∈ P} attempts(p, s_i)  s.t. f(p, s_i) = EXECUTED
B_{i+1} = µ(p*_i)
```

Runs each LPCI stage sequentially, seeding the next stage with mutated versions of the winning payload.

### Response Analyser
`laaf/core/analyser.py` — classifies each LLM response as:
- `EXECUTED` — payload instruction was followed (breakthrough)
- `WARNING` — partial compliance detected
- `BLOCKED` — model refused
- `UNKNOWN` — indeterminate

### Mutation Engine
`laaf/core/mutator.py` — 4 adaptive strategies triggered by consecutive block counts:
1. **Seed Variation** (0–9 consecutive blocks)
2. **Encoding Mutation** (10–19)
3. **Compound Mutation** (20+)
4. **Random Exploration** (30% of all attempts, simulated annealing)

## Data Flow

```
POST /scans
    │
    ▼
BackgroundTask: _run_scan_bg()
    │
    ├─ get_platform("openrouter", model="...")
    │
    ├─ StageEngine.get_context(stage_id) ──► configs/stages/sN_*.yaml
    │
    └─ PersistentStageBreaker.run(stages=[...])
            │
            ├── for each stage:
            │     ├── PayloadGenerator.generate(count=1)
            │     ├── Platform.send(system_prompt, payload)
            │     ├── ResponseAnalyser.analyse(response)
            │     └── if EXECUTED: seed next stage
            │
            └── PSBResult ──► JSONReporter / CSVReporter
```
