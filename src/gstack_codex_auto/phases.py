"""Original phase briefs. Third-party skills are read locally, never vendored."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Phase:
    id: str
    skill: str | None
    write: bool
    brief: str
    reviews: str | None = None


PHASES = [
    Phase("01-ceo", "plan-ceo-review", False,
          "Define the user problem, smallest valuable scope, alternatives, risks and measurable acceptance criteria."),
    Phase("02-challenge-ceo", None, False,
          "Challenge the CEO plan against the spec. Identify unsupported assumptions and blockers with concrete corrections.", "01-ceo"),
    Phase("03-engineering", "plan-eng-review", False,
          "Inspect the repository. Design file-level implementation, interfaces, tests, migration and rollback."),
    Phase("04-challenge-engineering", None, False,
          "Challenge architecture and testability; find failure modes, overengineering and missing requirements.", "03-engineering"),
    Phase("05-design", "plan-design-review", False,
          "Design the interface, usability and accessibility. For a non-UI project review CLI/API ergonomics instead."),
    Phase("06-challenge-design", None, False,
          "Challenge usability and error recovery; check that proposed interaction is feasible and meets the spec.", "05-design"),
    Phase("07-reconcile", "plan-eng-review", False,
          "Reconcile product, engineering and design into one ordered implementation plan with objective checks."),
    Phase("08-challenge-final", None, False,
          "Review the reconciled plan for unresolved blockers, contradictory requirements and missing verification.", "07-reconcile"),
    Phase("09-implement", None, True,
          "Implement the reviewed plan in this worktree. Read previous artifacts; run relevant tests. Do not commit, push, deploy, or change the external gate configuration."),
    Phase("10-review", "review", False,
          "Review the entire candidate diff from BASE_SHA to the current tree. Check correctness, security and regressions. Report blocking issues; do not fix code."),
    Phase("11-qa", "qa", False,
          "Verify actual behavior and acceptance criteria. For UI use browser QA when available; otherwise use CLI/API checks. Missing required runtime evidence is blocked, not passed. Do not fix code."),
    Phase("12-document", "document-release", True,
          "Update documentation for the actual behavior, install instructions and limitations. Do not change product code or commit, push or deploy."),
    Phase("13-score", "retro", False,
          "Independently assess the final diff, objective gate receipts and remaining issues. Score functionality, correctness, maintainability, usability and spec adherence from 0 to 10. Scores are model judgments, not proof of quality."),
]
REPAIR = Phase("repair", None, True,
               "Fix only the blocking review/QA findings and failing objective gates in the supplied evidence. Preserve existing behavior; do not weaken tests or alter gate configuration. Do not commit, push or deploy.")

RESPONSE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["status", "summary", "findings", "scores"],
    "properties": {
        "status": {"type": "string", "enum": ["pass", "blocked"]},
        "summary": {"type": "string"},
        "findings": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["severity", "detail"],
            "properties": {"severity": {"type": "string", "enum": ["blocker", "warning", "info"]},
                           "detail": {"type": "string"}}}},
        "scores": {"type": "object", "additionalProperties": False,
                   "required": ["functionality", "correctness", "maintainability", "usability", "spec_adherence"],
                   "properties": {k: {"type": "number", "minimum": 0, "maximum": 10}
                                  for k in ["functionality", "correctness", "maintainability", "usability", "spec_adherence"]}},
    },
}
