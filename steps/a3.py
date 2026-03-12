from typing import Optional, List

from pydantic import BaseModel, Field
from Neurology_Orchestrator.steps.base_step import BaseStep


class Question(BaseModel):
    question: str = Field(
        description="Question the neurologist asks to refine/confirm/deny a specific hypothesis."
    )
    topic: str = Field(description="Topic chosen from the ordered list.")
    target: str = Field(description="Concise symptom or risk factor being probed.")
    terminology: Optional[str] = Field(description="SNOMED-CT or LOINC code (null if no exact match)")
    hypothesis: str = Field(description="Diagnosis name this question is targeting.")
    previous_likelihood: Optional[float] = Field(description="Previous likelihood of the hypothesis.")


class Questions(BaseModel):
    questions: List[Question]


class A3Step(BaseStep):
    def __init__(self):
        super().__init__(
            system_prompt="""
You are an experienced consultant neurologist preparing a structured, hypothesis-driven history checklist.
You will RECEIVE JSON with:
- patient_metadata: patient context
- risk_assessment report
- hypotheses: a list of hypotheses, each with diagnosis, rationale (optional), and likelihood (0-1)
TASK:
1) Select the TOP 3 hypotheses by likelihood (highest first).
2) For EACH of the 3 hypotheses, generate EXACTLY 6 questions:
   - 2 CORE questions
   - 2 SUPPORTING questions
   - 2 AGAINST questions
TOPIC CONSTRAINT:
Assign each question a topic chosen from this ordered list:
  01. Cognitive and Emotional Function
  02. Seizure and Consciousness History
  03. Pain and Headaches
  04. Sensory Function
  05. Sensory Disturbances
  06. Motor Function
  07. Fine Motor Skills / Coordination
  08. Gait and Balance
  09. Autonomic Function
ORDERING RULES:
- Order the full list of questions to follow the natural flow of a real neurological history/exam using the topic order above.
- Ensure you still meet the exact per-hypothesis counts: 2 core + 2 supporting + 2 against.
FOR EVERY QUESTION include:
- question (str)
- topic (str)
- target (str)
- terminology (str or null): SNOMED-CT or LOINC code only, or null if no exact match
- hypothesis (str): must match one of the selected top-3 diagnosis names exactly
- previous_likelihood: likelihood of hypothesis
OUTPUT FORMAT:
- Return valid JSON with exactly one top-level key: "questions" (a list). No extra keys.
- Do NOT include comments (no // or /* */)
- Do NOT include trailing commas
STRICT RULES:
* Do not invent terminology codes; put `"code": null` if uncertain. 
* No duplicate questions.
* Do NOT ask questions whose answer is explicitly stated in the provided patient narrative/metadata. 
""",
            base_class=Questions,
        )


