from typing import List
from pydantic import BaseModel, Field
from Neurology_Orchestrator.steps.base_step import BaseStep


class LocalizationHypothesis(BaseModel):
    anatomical_position: str = Field(description="Anatomical position of the suspected lesion (e.g., left frontal lobe, cervical spinal cord).")
    rationale: str = Field(description="One-sentence rationale explaining why this localization is suggested, based on the chief complaint and neurological examination.")


class LocalizationHypotheses(BaseModel):
    hypotheses: List[LocalizationHypothesis] = Field(description="List of possible anatomical localizations of the lesion.")

class A21Step(BaseStep):

    def __init__(self):
        super().__init__(system_prompt="""
You are an experienced neurologist.

You are given a INPUT:
- Chief complaint
- Chief complaint tempo
- Neurological examination findings
- Neuroradiology Tests
- Electrophysiology Tests


Your task is to infer the most likely anatomical localization(s) of the lesion.

Return a SINGLE JSON object with the field `hypotheses`.

- `hypotheses` is a list (max 8 items).
- Each item is an object with:
  - anatomical_position (str): Anatomical position of the suspected lesion 
    (e.g., left frontal lobe, right internal capsule, cervical spinal cord, peripheral nerve, neuromuscular junction, etc.).
  - rationale (str): One-sentence clinical reasoning that links the symptoms and exam findings to this localization.

Focus ONLY on localization, do NOT mention concrete disease names.
Return ONLY valid JSON, no extra text.
- Do NOT include comments (no // or /* */)
- Do NOT include trailing commas
- Do NOT return empty lists
""",
            base_class=LocalizationHypotheses,
        )
