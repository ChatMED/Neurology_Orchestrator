from typing import List
from pydantic import BaseModel, Field
from Neurology_Orchestrator.steps.base_step import BaseStep


class RankedDiagnosisHypothesis(BaseModel):
    diagnosis: str = Field(
        description="Name of the diagnosis."
    )
    rationale: str = Field(
        description="One-sentence rationale explaining why this diagnosis is likely for THIS patient, including clinical features and risk factors."
    )
    likelihood: float = Field(
        description="Estimated probability (0–1) that this diagnosis is correct."
    )


class RankedDiagnosisHypotheses(BaseModel):
    hypotheses: List[RankedDiagnosisHypothesis] = Field(
        description="Rank-ordered list of diagnoses with explicit likelihoods."
    )
class A24Step(BaseStep):

    def __init__(self):
        super().__init__(system_prompt="""
You are an experienced neurologist.

INPUT:
1) Patient-specific data
2) An UNRANKED differential diagnosis list 

TASK:
- Re-assess these diagnoses for THIS specific patient.
- Rank them from MOST to LEAST likely.
- Assign a numeric likelihood (0–1) to each item.

Return a SINGLE JSON object with the field `hypotheses`.

- `hypotheses` is a list (max 8 items), ordered from MOST to LEAST likely.
- Each item is an object with:
  - diagnosis (str)
  - rationale (str): One-sentence reasoning that explicitly uses patient features 
    (age, sex, tempo, PMH, family_history, medications) to justify the likelihood.
  - likelihood (float): Probability between 0 and 1.

Rules:
- Ensure the list is strictly sorted in DESCENDING likelihood.
Return ONLY valid JSON. No extra commentary.
- Do NOT include comments (no // or /* */)
- Do NOT include trailing commas
- Do NOT return empty lists
""",base_class=RankedDiagnosisHypotheses)
