"""
Persistent Stage Breaker (PSB)
================================
Core algorithmic contribution of LAAF. Operationalises the LPCI lifecycle as a
sequential adversarial search problem: find the minimum payload that breaks each
stage, then use that payload as the starting config for the next stage.

Formal definition (paper §6.1, Eq. 2):
    p*_i = argmin_{p ∈ P} attempts(p, s_i)  s.t. f(p, s_i) = EXECUTED
    B_{i+1} = µ(p*_i)   where µ is the mutation function

Paper §6 — LAAF (Atta et al., 2026)
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

import structlog

from laaf.core.analyser import ResponseAnalyser
from laaf.core.mutator import MutationEngine
from laaf.generators.payload_generator import Payload, PayloadGenerator
from laaf.platforms.base import AbstractPlatform
from laaf.taxonomy.base import Outcome

log = structlog.get_logger()


@dataclass
class StageResult:
    """Result of running the PSB on a single lifecycle stage."""
    stage_id: str
    stage_name: str
    broken: bool
    attempts: int
    winning_payload: Optional[Payload]
    winning_outcome: Outcome
    winning_confidence: float
    duration_seconds: float
    all_outcomes: dict[str, int] = field(default_factory=lambda: {
        "EXECUTED": 0, "BLOCKED": 0, "WARNING": 0, "UNKNOWN": 0
    })
    # Artifact fields — populated on breakthrough
    winning_payload_content: Optional[str] = None   # exact text sent to LLM
    winning_response: Optional[str] = None           # LLM's actual response
    winning_raw_instruction: Optional[str] = None    # decoded attack intent


@dataclass
class PSBResult:
    """Complete result of a full PSB run across all 6 stages."""
    platform: str
    model: str
    stages: list[StageResult] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    total_attempts: int = 0

    @property
    def stages_broken(self) -> int:
        return sum(1 for s in self.stages if s.broken)

    @property
    def overall_breakthrough_rate(self) -> float:
        if not self.stages:
            return 0.0
        return self.stages_broken / len(self.stages)


class PersistentStageBreaker:
    """
    Implements the PSB loop:
    1. For each stage s_i, generate payloads from the technique taxonomy.
    2. Send each payload to the target LLM.
    3. If EXECUTED: record winning payload p*_i, mutate into seed batch for s_{i+1}.
    4. If not broken within A_max attempts: advance without seed.
    5. Adaptively switch mutation strategy based on consecutive blocks.
    6. Intersperse 30% random payloads to prevent local optima (simulated annealing).
    """

    def __init__(
        self,
        platform: AbstractPlatform,
        stage_contexts: dict[str, tuple[str, str]],  # stage_id → (system_prompt, goal)
        max_attempts: int = 500,
        exploration_rate: float = 0.30,
        rate_delay: float = 2.0,
        progress_callback: Optional[Callable[[str, int, str, float], None]] = None,
        exfil_url: Optional[str] = None,
    ) -> None:
        self.platform = platform
        self.stage_contexts = stage_contexts
        self.max_attempts = max_attempts
        self.exploration_rate = exploration_rate
        self.rate_delay = rate_delay
        self.progress_callback = progress_callback

        self._analyser = ResponseAnalyser()
        self._generator = PayloadGenerator(exfil_url=exfil_url)
        self._mutator = MutationEngine(generator=self._generator)

    async def run(self, stages: Optional[list[str]] = None) -> PSBResult:
        """Run the PSB across specified stages (default: all 6 LPCI stages)."""
        all_stages = list(self.stage_contexts.keys())
        target_stages = stages or all_stages

        result = PSBResult(
            platform=self.platform.name,
            model=str(self.platform.model or self.platform.default_model),
        )
        t_start = time.monotonic()
        seed_payload: Optional[Payload] = None

        for stage_id in target_stages:
            if stage_id not in self.stage_contexts:
                log.warning("stage_not_found", stage_id=stage_id)
                continue

            system_prompt, goal = self.stage_contexts[stage_id]
            stage_result = await self._run_stage(
                stage_id=stage_id,
                system_prompt=system_prompt,
                goal=goal,
                seed_payload=seed_payload,
            )
            result.stages.append(stage_result)
            result.total_attempts += stage_result.attempts

            if stage_result.broken and stage_result.winning_payload:
                seed_payload = stage_result.winning_payload
                seed_payload.is_seed = True
                log.info(
                    "stage_broken",
                    stage=stage_id,
                    attempts=stage_result.attempts,
                    technique=stage_result.winning_payload.technique_id,
                )
            else:
                seed_payload = None
                log.warning("stage_not_broken", stage=stage_id, attempts=stage_result.attempts)

        result.total_duration_seconds = time.monotonic() - t_start
        return result

    async def _run_stage(
        self,
        stage_id: str,
        system_prompt: str,
        goal: str,
        seed_payload: Optional[Payload],
    ) -> StageResult:
        t_stage = time.monotonic()
        consecutive_blocks = 0
        best_warning: Optional[tuple[Payload, float]] = None
        outcomes: dict[str, int] = {"EXECUTED": 0, "BLOCKED": 0, "WARNING": 0, "UNKNOWN": 0}

        for attempt in range(1, self.max_attempts + 1):
            # Adaptive strategy selection
            strategy = self._mutator.select_strategy(consecutive_blocks)

            # 30% random exploration (simulated annealing)
            if random.random() < self.exploration_rate or seed_payload is None:
                payloads = self._generator.generate(count=1)
            else:
                payloads = self._mutator.mutate(seed_payload, strategy=strategy, count=1)

            if not payloads:
                continue
            payload = payloads[0]
            payload.stage = stage_id

            # Send to target
            try:
                await asyncio.sleep(self.rate_delay)
                response = await self.platform.send(system_prompt, payload.content)
            except Exception as exc:
                log.warning("send_error", stage=stage_id, attempt=attempt, error=str(exc))
                continue

            outcome, confidence = self._analyser.analyse(response.content)
            outcomes[outcome.value] = outcomes.get(outcome.value, 0) + 1

            if self.progress_callback:
                self.progress_callback(stage_id, attempt, outcome.value, confidence)

            if outcome == Outcome.EXECUTED:
                return StageResult(
                    stage_id=stage_id,
                    stage_name=goal,
                    broken=True,
                    attempts=attempt,
                    winning_payload=payload,
                    winning_outcome=outcome,
                    winning_confidence=confidence,
                    duration_seconds=time.monotonic() - t_stage,
                    all_outcomes=outcomes,
                    winning_payload_content=payload.content,
                    winning_response=response.content,
                    winning_raw_instruction=payload.raw_instruction,
                )

            if outcome == Outcome.WARNING:
                if best_warning is None or confidence > best_warning[1]:
                    best_warning = (payload, confidence)
                # Only reset escalation on a genuine partial success (high-confidence
                # WARNING). Low-confidence WARNING (benign model responses) must not
                # reset the counter — otherwise reframe/compound strategies are never
                # reached against cooperative models.
                if confidence >= 0.5:
                    consecutive_blocks = 0
                else:
                    consecutive_blocks += 1
            else:
                consecutive_blocks += 1

            # Update seed only when a detectable signal was present.
            # EXECUTED/WARNING carry structural information worth mutating from.
            # UNKNOWN means the payload had no measurable effect — not useful as seed.
            # BLOCKED means the model explicitly refused — not useful as seed either.
            if outcome in (Outcome.EXECUTED, Outcome.WARNING) and payload:
                seed_payload = payload

        # Stage not broken within Amax
        warning_payload = best_warning[0] if best_warning else None
        return StageResult(
            stage_id=stage_id,
            stage_name=goal,
            broken=False,
            attempts=self.max_attempts,
            winning_payload=warning_payload,
            winning_outcome=Outcome.WARNING if warning_payload else Outcome.BLOCKED,
            winning_confidence=best_warning[1] if best_warning else 0.0,
            duration_seconds=time.monotonic() - t_stage,
            all_outcomes=outcomes,
        )
