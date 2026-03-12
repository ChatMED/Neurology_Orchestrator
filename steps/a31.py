from typing import List, Optional
from pydantic import BaseModel, Field
from Neurology_Orchestrator.steps.base_step import BaseStep

class AnsweredQA(BaseModel):
    diagnosis: Optional[str] = Field(description="diagnosis that question is referred to")
    previous_likelihood: Optional[float] = Field(description="previous likelihood that question is referred to")
    question: Optional[str] = Field(description="a question that is answered")
    answer: Optional[str]= Field(
        description="Answer to the question"
    )
    short_justification: Optional[str] = Field(
        default=None,
        description="Very short justification grounded in the provided patient text/metadata."
    )
    evidence: Optional[str] = Field(
        default=None,
        description="Copy a short phrase from the provided inputs that supports the answer; null if unknown."
    )


class AnsweredQAs(BaseModel):
    qa: List[AnsweredQA]


class A31Step(BaseStep):
    def __init__(self):
        super().__init__(
            system_prompt="""
You are a neurologist assistant doing STRICT information extraction.

INPUT:
- patient_metadata (structured)
- risk_assessment
- questions (list)

TASK:
For each question, answer using ONLY the information present in the inputs.

For each item, return:
- diagnosis (copy exactly)
- previous_likelihood (copy exactly)
- question (copy exactly)
- answer: answer to the question
- short_justification: one short sentence grounded in the inputs (or null if unknown)
For each item, return:
- diagnosis (copy exactly)
- previous_likelihood (copy exactly)
- question (copy exactly)
- answer: answer to the question
- short_justification: one short sentence grounded in the inputs (or null if unknown)
- evidence: a short exact phrase from the PATIENT DATA that supports the answer (or null if unknown)
            Evidence must be ACTUAL TEXT from patient data, NOT field names or structure.
            If there are multiple evidence phrases, concatenate them into ONE single string separated by semicolon and space.
            
CRITICAL JSON RULES:
- Return ONLY valid JSON with one top-level key: "qa"
- Do NOT include comments (no // or /* */)
- Do NOT include trailing commas
- Do NOT include field names like "family_history": null in the evidence field
- Evidence must be plain text ONLY, not JSON structure

Correct output formats:
"evidence": null
"evidence": "GCS 15/15"
"evidence": "essential tremor; impulsive behavior"

Incorrect output formats (DO NOT DO THIS):
"evidence": "null"
"evidence": "family_history": null
"evidence": "field": "value"
""",
            base_class=AnsweredQAs,  # remove if BaseStep doesn't support it
        )
