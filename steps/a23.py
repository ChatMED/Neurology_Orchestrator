from typing import List
from pydantic import BaseModel, Field
from Neurology_Orchestrator.steps.base_step import BaseStep


class DiagnosisHypothesis(BaseModel):
    diagnosis: str = Field(
        description="Specific neurological diagnosis (e.g. relapsing-remitting multiple sclerosis, migraine without aura)."
    )
    rationale: str = Field(
        description="One-sentence clinical reasoning combining localization, pathophysiology, and the patient's presentation."
    )


class DiagnosisHypotheses(BaseModel):
    hypotheses: List[DiagnosisHypothesis] = Field(
        description="List of possible diagnoses."
    )
class A23Step(BaseStep):
    def __init__(self):
        super().__init__(system_prompt="""
You are an experienced neurologist.

INPUT:
1) A list of anatomical + pathophysiological hypotheses.
2) Risk assessment output (from the RiskAssessor agent), containing:
      - urgency_level
      - overall_risk_score
      - red_flags (each with severity + required action)
      - immediate_interventions
      - monitoring requirements
      - escalation pathway
3) Patient specific features

Your task is to generate a DIFFERENTIAL DIAGNOSIS LIST: 
a set of specific neurological diagnoses that could explain this patient's presentation.
Red flags MUST influence the differential diagnosis.
Always prioritize explaining **high-severity** and **critical** red flags first.
Urgency_level must bias the list toward diagnoses that match the clinical tempo
  (e.g., “emergency” → acute vascular, infection, seizure; 
        “urgent” → progressive weakness, first seizure;
        “routine” → chronic stable conditions).
Exclude diagnoses that clearly do NOT fit the red flags, risk profile, or tempo.
Use risk information only to PRIORITIZE and FILTER — do NOT restate it as a diagnosis.
Return a SINGLE JSON object with the field `hypotheses`.

- `hypotheses` is a list (max 8 items).
- Each item is an object with:
  - diagnosis (str): A specific diagnosis (e.g. “migraine without aura”, “idiopathic intracranial hypertension”, “cervicogenic headache”).
  - rationale (str): One-sentence explanation that combines:
        * the symptoms and tempo,
        * localization hypotheses,
        * pathophysiological processes,
        * and relevant risk factors (age, sex, past/family history, medications).

IMPORTANT:
- Focus on plausible neurological (or neuro-related) diagnoses for THIS patient.
- Do NOT include numeric probabilities or ranking here.
- Return ONLY valid JSON. No extra commentary.
- ONLY JSON IS ALLOWED as an answer
- Do NOT include comments (no // or /* */)
- Do NOT include trailing commas
- Do NOT return empty lists
""",
            base_class=DiagnosisHypotheses,
        )
