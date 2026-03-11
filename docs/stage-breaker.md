# Persistent Stage Breaker (PSB) Algorithm

## Overview

The Persistent Stage Breaker (PSB) is LAAF's core algorithmic contribution, operationalising the LPCI lifecycle as a sequential adversarial search problem. It formally implements Equation 2 from the LAAF paper (Atta et al., 2026, arXiv:2507.10457).

## Formal Definition

Given a set of LPCI lifecycle stages `S = {S1, S2, ..., S6}` and a payload space `P`:

```
p*_i = argmin_{p ∈ P} attempts(p, s_i)   s.t. f(p, s_i) = EXECUTED
B_{i+1} = µ(p*_i)   where µ is the mutation function
```

Where:
- `p*_i` is the optimal (minimum-attempt) payload for stage `i`
- `f(p, s_i)` is the response classifier for payload `p` at stage `s_i`
- `B_{i+1}` is the seed batch for the next stage, derived by mutating the winning payload
- `µ` is the MutationEngine

## Algorithm

```
PSB(stages S, max_attempts A_max):
  seed ← None
  for s_i in S:
    for attempt in 1..A_max:
      strategy ← SelectStrategy(consecutive_blocks)
      if rand() < 0.30 or seed is None:
        payload ← RandomPayload()            # 30% exploration (simulated annealing)
      else:
        payload ← Mutate(seed, strategy)     # 70% exploitation
      response ← Target.Send(payload)
      outcome, confidence ← Analyse(response)
      if outcome == EXECUTED:
        p*_i ← payload
        seed ← Mutate(p*_i)
        break
    if not broken:
      seed ← None
  return PSBResult
```

## Mutation Strategies

The PSB uses four adaptive mutation strategies, selected based on consecutive block count:

| Consecutive Blocks | Strategy | Description |
|---|---|---|
| `c < 10` | Encoding | Same instruction, different encoding (E1–E11) |
| `10 ≤ c < 20` | Reframe | Same encoding, different semantic wrapper (M1–M8) |
| `c ≥ 20` | Compound | Escalated multi-layer combination (L1–L5) |
| Any | Trigger | Different trigger keyword (T1–T12) |

## Simulated Annealing (30% Exploration)

At each iteration, the PSB randomly selects a fresh payload from the full taxonomy with 30% probability. This prevents local optima by ensuring the search does not get trapped in a narrow region of the payload space — analogous to the exploration parameter in simulated annealing.

## Stage Seeding

When stage `s_i` is broken, the winning payload `p*_i` becomes the seed for stage `s_{i+1}`. The seed carries the raw instruction but the technique is re-applied with the mutation strategy, building on the previous breakthrough. If a stage is not broken, the seed is cleared and the next stage begins with random exploration.

## Response Classification

The `ResponseAnalyser` maps LLM outputs to one of three outcomes:

| Outcome | Description | Action |
|---|---|---|
| `EXECUTED` | Model followed injected instruction | Stage broken, record `p*_i` |
| `WARNING` | Partial compliance detected | Track best warning, continue |
| `BLOCKED` | Model refused the injection | Increment `consecutive_blocks` |
| `UNKNOWN` | Indeterminate response | Continue search |

Detection signals include: exact marker tokens (`MARKER_EXECUTED_001`), system prompt disclosure patterns, authority token acceptance, and semantic compliance signals.

## Configuration

PSB parameters are configurable via `configs/default.yaml`:

```yaml
max_attempts: 500        # A_max — attempts before advancing to next stage
exploration_rate: 0.30   # simulated annealing random exploration probability
rate_delay: 2.0          # seconds between API calls (rate limiting)
```

Or via CLI:

```bash
laaf scan --target openai --payloads 500 --rate-delay 1.0
```

## Implementation

Source: [`laaf/core/stage_breaker.py`](../laaf/core/stage_breaker.py)

The `PersistentStageBreaker` class exposes a single async entrypoint:

```python
psb = PersistentStageBreaker(
    platform=platform,
    stage_contexts=stage_contexts,  # {stage_id: (system_prompt, goal)}
    max_attempts=500,
    rate_delay=2.0,
)
result: PSBResult = await psb.run(stages=["S1", "S2", "S3", "S4", "S5", "S6"])
```

### PSBResult

```python
@dataclass
class PSBResult:
    platform: str
    model: str
    stages: list[StageResult]
    total_duration_seconds: float
    total_attempts: int

    @property
    def stages_broken(self) -> int: ...
    @property
    def overall_breakthrough_rate(self) -> float: ...
```

### StageResult

```python
@dataclass
class StageResult:
    stage_id: str
    stage_name: str
    broken: bool
    attempts: int
    winning_payload: Optional[Payload]
    winning_outcome: Outcome
    winning_confidence: float
    duration_seconds: float
    all_outcomes: dict[str, int]
    winning_payload_content: Optional[str]  # exact text sent to LLM
    winning_response: Optional[str]         # LLM's actual response
    winning_raw_instruction: Optional[str]  # decoded attack intent
```

## References

- Atta, H. et al. (2026). *LAAF: Logic-Layer Automated Attack Framework*. arXiv:2507.10457
- Paper §6.1 — PSB Formal Definition (Eq. 2)
- Paper §6.2 — Adaptive Mutation Strategies
- Paper §4 — LPCI Lifecycle Taxonomy
