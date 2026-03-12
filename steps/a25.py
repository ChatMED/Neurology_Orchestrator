from typing import List
from pydantic import BaseModel, Field
from Neurology_Orchestrator.steps.base_step import BaseStep


class RankedDiagnosisHypothesis(BaseModel):
    diagnosis: str
    rationale: str
    likelihood: float


class RankedDiagnosisHypotheses(BaseModel):
    hypotheses: List[RankedDiagnosisHypothesis]


class A25Step(BaseStep):
    def __init__(self):
        super().__init__(
            system_prompt="""
You are an experienced neurologist.

INPUT:
- patient_metadata
- qa: answered questions with optional evidence and hypothesis it refers to

TASK:
Your task is to update (not reinvent) the differential diagnosis list based on the available question–answer evidence.
Re-assess existing diagnostic hypotheses using the provided QA evidence.
Update and re-rank diagnoses by revising their likelihoods where appropriate.
You may introduce up to two new diagnoses only if strongly supported by QA evidence, and you must explicitly reference the motivating evidence.
Exclude diagnoses that are no longer supported by the evidence or contradict key patient features.
Use only the provided inputs; do not introduce new facts or assumptions.

RATIONALE:
- One sentence per hypothesis.
- Must explicitly reference key patient features AND the most relevant QA answers/evidence.

OUTPUT:
Return ONLY valid JSON with top-level key "hypotheses" with objects:
  - diagnosis (str)
  - rationale (str): One-sentence reasoning 
  - likelihood (float): Probability between 0 and 1.
No extra keys.
- Do NOT include comments (no // or /* */)
- Do NOT include trailing commas
- Do NOT return empty lists
""",
            base_class=RankedDiagnosisHypotheses,
        )
