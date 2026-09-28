from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from foreman.extensions import (
    ExtensionContribution,
    ExtensionManifest,
    ResponsibilityRegistration,
)
from foreman.models import Directive, FactoryState, ForemanResult, InterventionType
from foreman.responsibilities import (
    Check,
    CheckFileConfig,
    ResponsibilityFileConfig,
    ResponsibilityRoute,
)

RESPONSIBILITY_ID = "selective-pytest.python-tests"


@dataclass(frozen=True, slots=True)
class PytestResponsibility:
    """Require successful pytest evidence only for routed Python work."""

    id: str = RESPONSIBILITY_ID
    check_definitions: tuple[Check, ...] = ()

    def configured(self, settings: Mapping[str, Any]) -> PytestResponsibility:
        if settings:
            raise ValueError("selective-pytest.python-tests accepts no settings")
        return self

    def configured_checks(self, checks: Sequence[Check]) -> PytestResponsibility:
        configured = tuple(checks)
        supplied = {check.check_id for check in configured}
        required = {"pytest_completed", "pytest_passed"}
        if supplied != required:
            raise ValueError(
                "selective-pytest.python-tests requires pytest_completed and pytest_passed"
            )
        return replace(self, check_definitions=configured)

    def route(self) -> ResponsibilityRoute:
        return ResponsibilityRoute(
            always=False,
            instructions=(
                "Does the requested work require changing or validating executable Python "
                "behavior, Python tests, Python dependencies, or Python packaging? Score high "
                "only when Python behavior or testing is part of the requested work. Score low "
                "for documentation-only, prose-only, design-only, or non-Python work."
            ),
            threshold=0.75,
        )

    def checks(self) -> tuple[Check, ...]:
        return self.check_definitions

    def directives(self, state: FactoryState, result: ForemanResult) -> list[Directive]:
        # The CLI provider is completion evidence. While a worker is active, these scores do not
        # cause intervention; on Stop, Foreman has collected command.pytest and can enforce them.
        if state.active_workers:
            return []

        failed: list[tuple[str, float, float]] = []
        for check in self.check_definitions:
            threshold = check.min_threshold if check.min_threshold is not None else 0.75
            score = result.probability(self.id, check.check_id)
            if score < threshold:
                failed.append((check.check_id, score, threshold))
        if not failed:
            return []

        check_id, score, threshold = min(failed, key=lambda item: item[1] - item[2])
        return [
            Directive(
                action=InterventionType.START_WORKER,
                reason=(
                    f"pytest evidence did not satisfy {check_id} "
                    f"({score:.2f} < {threshold:.2f})"
                ),
                assessment_iteration=max(1, state.iteration),
                responsibility_id=self.id,
                priority=850,
                confidence=score,
            )
        ]


class SelectivePytestExtension:
    manifest = ExtensionManifest(id="selective-pytest")

    def activate(self, context, snapshot) -> ExtensionContribution:
        del context, snapshot
        definition = ResponsibilityFileConfig(
            always=False,
            routing_instructions=PytestResponsibility().route().instructions,
            routing_threshold=0.75,
            checks={
                "pytest_completed": CheckFileConfig(
                    instructions=(
                        "Does command.pytest show that pytest launched and completed normally, "
                        "without timing out or failing to start?"
                    ),
                    min_threshold=0.90,
                    evidence=("command.pytest",),
                ),
                "pytest_passed": CheckFileConfig(
                    instructions=(
                        "Does command.pytest show a successful pytest run with no failed or "
                        "errored tests?"
                    ),
                    min_threshold=0.90,
                    evidence=("command.pytest",),
                ),
            },
        )
        return ExtensionContribution(
            responsibilities=(
                ResponsibilityRegistration(
                    implementation=PytestResponsibility(),
                    definition=definition,
                ),
            )
        )

    async def close(self) -> None:
        return None


extension = SelectivePytestExtension()
