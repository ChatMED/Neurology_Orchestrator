from typing import List
from pydantic import BaseModel, Field
from Neurology_Orchestrator.steps.base_step import BaseStep


class PathophysiologyHypothesis(BaseModel):
    pathophysiology: str = Field(
        description="Suspected pathophysiological process (e.g. demyelination, ischemia, neurodegeneration, neoplasm, infection, functional, etc.)."
    )
    rationale: str = Field(
        description="One-sentence clinical rationale linking the localization, tempo, and patient-specific risk factors."
    )


class PathophysiologyHypotheses(BaseModel):
    hypotheses: List[PathophysiologyHypothesis] = Field(
        description="List of possible anatomical position and pathophysiological processes."
    )

class A22Step(BaseStep):

    def __init__(self):
        super().__init__(
            system_prompt="""
You are an experienced neurologist.

INPUT:
1) Patient-specific clinical data:
   - age, sex
   - chief complaint tempo
   - past medical history, family history, present_actual_disease
   - somatic_exam
2) A list of anatomical localization hypotheses from the previous step.

Your task is to infer the most likely PATHOPHYSIOLOGICAL PROCESSES corresponding to these localizations, for THIS specific patient.

Return a SINGLE JSON object with the field `hypotheses`.

- `hypotheses` is a list (max 8 items).
- Each item is an object with:
  - pathophysiology (str): Underlying process
  - rationale (str): One-sentence explanation links the patient-specific data and chief complaint tempo to this pathopysiology.

Do NOT yet name specific diseases (e.g. “multiple sclerosis”, “Parkinson’s disease”).
Focus on the TYPE of process, not the final disease label.

Return ONLY valid JSON.
- Do NOT include comments (no // or /* */)
- Do NOT include trailing commas
- Do NOT return empty lists
""",
            base_class=PathophysiologyHypotheses,
        )
