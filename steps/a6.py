from Neurology_Orchestrator.steps.base_step import BaseStep
from typing import List
from pydantic import BaseModel, Field


class Inconsistency(BaseModel):
    type: str = Field(description="Type/category of the inconsistency.")
    description: str = Field(description="Detailed explanation of the inconsistency.")
    severity: str = Field(description='Severity level: "critical", "major", or "minor".')


class CriticalDiagnosesCheck(BaseModel):
    all_life_threatening_considered: bool = Field(description="Whether all life-threatening diagnoses were considered.")
    missed_critical: List[str] = Field(description="List of critical diagnoses that were missed.")


class GuidelineCompliance(BaseModel):
    guidelines_cited: int = Field(description="Number of guidelines that were cited.")
    compliance_rate: float = Field(description="Guideline compliance rate between 0.0 and 1.0.")
    missing_citations: List[str] = Field(description="Guidelines that should have been cited but were not.")


class ValidationReport(BaseModel):
    is_complete: bool = Field(description="Whether the report is complete.")
    completeness_score: float = Field(description="Completeness score (0.0–1.0).")
    missing_elements: List[str] = Field(description="List of missing checklist elements.")
    inconsistencies: List[Inconsistency] = Field(description="Detected inconsistencies with type, description, and severity.")
    critical_diagnoses_check: CriticalDiagnosesCheck = Field(description="Results of the critical diagnoses assessment.")
    guideline_compliance: GuidelineCompliance = Field(description="Assessment of guideline citation and compliance.")
    safety_net_included: bool = Field(description="Whether a safety-net section was included.")
    patient_instructions_clear: bool = Field(description="Whether the patient instructions were clear.")
    follow_up_specified: bool = Field(description="Whether follow-up arrangements were clearly stated.")
    confidence_score: float = Field(description="Confidence score (0.0–1.0) in the diagnostic plan.")
    requires_human_review: bool = Field(description="Whether the case requires human review.")
    review_urgency: str = Field(description='Urgency of review: "immediate", "urgent", or "routine".')
    quality_flags: List[str] = Field(description="List of quality-related flags or warnings.")

class ValidationPlanner(BaseModel):
    validation_report: ValidationReport = Field( description="Structured validation report for the neurology diagnostic pipeline.")


class A6Step(BaseStep):

    def __init__(self):
        super().__init__(system_prompt="""
You are a clinical quality auditor validating an entire neurology diagnostic workflow.

You will receive these pipeline artifacts (JSON strings / structured objects):
- a0: patient metadata (history/exam and available tests lists)
- a2.5: risk assessment output (urgency, red flags, escalation pathway, etc.)
- a21: localization hypotheses
- a22: pathophysiology hypotheses
- a23: unranked diagnosis list (generated differential)
- a24: ranked diagnosis hypotheses BEFORE question-answer refinement
- a3: question plan for top diagnoses (questions have question_type: core/supporting/against)
- a3.1: answered questions (yes/no/unknown + optional evidence)
- a26: ranked diagnosis hypotheses AFTER incorporating answers (updated differential)
- a4: investigations plan (labs/imaging/neurophysiology/etc.)
- a5: treatments plan
- a5.5: safety net / patient instructions / follow-up guidance

Your task is to produce a structured validation report.

For the validation_report include:
- "is_complete": (bool) – Is the whole report complete according to the checklist?
- "completeness_score": (float, 0.0–1.0) – Fraction of checklist items satisfied.
- "missing_elements": (list[str]) – Which required elements are missing.
- "inconsistencies": (list[Inconsistency]) – Any contradictions between hypotheses, investigations, or treatments, as a list of objects:
    Each inconsistency object MUST have:
      "type": (str) – Category or type of inconsistency,
      "description": (str) – Short explanation of the inconsistency,
      "severity": (str) – One of "critical", "major", or "minor".
- "critical_diagnoses_check": (CriticalDiagnosesCheck) – Whether life-threatening diagnoses were considered. 
    This MUST be a JSON object with EXACTLY these fields:
      "all_life_threatening_considered": (bool) – True if all relevant life-threatening diagnoses were considered,
      "missed_critical": (list[str]) – Names of any critical diagnoses that were NOT considered but should have been
- "guideline_compliance": (GuidelineCompliance) – Summary of guideline use.
    This MUST be a JSON object with EXACTLY these fields:
      "guidelines_cited": (int) – The NUMBER of distinct guidelines cited (e.g. 3, not a list of names),
      "compliance_rate": (float, 0.0–1.0) – Your estimated proportion of recommendations that follow accepted guidelines,
      "missing_citations": (list[str]) – Short identifiers of guidelines that SHOULD have been cited but were not (e.g. ["NICE CG186"])
- "safety_net_included": (bool) – Is a safety net present (red flags, emergency advice)?
- "patient_instructions_clear": (bool) – Are instructions understandable for a lay patient?
- "follow_up_specified": (bool) – Is follow-up timing/setting defined?
- "confidence_score": (float, 0.0–1.0) – Your confidence in the overall plan.
- "requires_human_review": (bool) – Should this case be escalated to a human clinician?
- "review_urgency": (str) – One of "immediate", "urgent", or "routine".
- "quality_flags": (list[str]) – Any additional quality warnings or notable points.

VALIDATION CHECKLIST

1) Completeness
A) Required outputs_csv present and non-empty:
   - a26 (final ranked hypotheses)
   - a3 (questions)
   - a3.1 (answers)
   - a4 (investigations)
   - a5 (treatments)
   - a5.5 (safety net / follow-up)
   - a2.5 (risk assessment)

B) Hypotheses quality checks (use a26 as final):
   - a26.hypotheses length <= 8
   - each likelihood within [0,1]
   - strictly sorted descending by likelihood
   - sum of likelihoods <= 1.0 (allow tolerance up to 1.01)

C) Question plan checks (based on what a3 actually contains):
   - Determine TOP 3 hypotheses from a26 (highest likelihood).
   - Confirm that a3 contains at least 6 questions PER each of those top-3 hypotheses.
   - Confirm every a3 question has: question, topic, target; terminology may be null.
   - Confirm a3.1 provides an answered entry for every a3 question by matching:
       - question text (exact or near-exact)
       - and hypothesis string (a3.hypothesis should match a3.1.diagnosis when possible)
     If matches are missing, list them in missing_elements.

D) Investigations/treatments linkage:
   - a4 investigations should be plausibly relevant to the TOP hypotheses in a26.
   - a5 treatments should be plausibly related to hypotheses and not obviously unsafe given a0 + a2.5.
   - Check it if likelihoods are available for the linked diagnoses; if linking is not explicit, do not guess.

2) Consistency (limited by available fields)
- Since questions are NOT labeled core/supporting/against, DO NOT apply core/against-specific logic.
- Instead check:
   - If a3.1 contains evidence/justifications that strongly contradict the top diagnosis in a26
     (e.g., clear denial of defining features), but a26 keeps it unchanged from a24, flag "Update Not Responsive".
   - If a26 is identical to a24 despite a3.1 containing multiple non-empty answers/evidence,
     flag "Refinement Ineffective" (minor/major depending on case).
- Ensure a4 and a5 align with final a26 more than stale a24.

3) Critical diagnoses coverage (life-threatening)
Verify whether the workflow considered or ruled out, when clinically plausible from a0/a2.5:
- Stroke/TIA
- Meningitis/encephalitis
- Ongoing seizure/status epilepticus
- Raised intracranial pressure
- Spinal cord compression
- Guillain–Barré syndrome
- Myasthenia gravis crisis

If red flags/high urgency exist in a2.5 and these are not reflected in hypotheses or investigations,
add to missed_critical.

4) Guideline compliance (strict)
- Count ONLY explicit guideline identifiers that appear in the provided artifacts (e.g., "NICE CG186", "AAN", "EAN").
- If no explicit guideline strings are present, set guidelines_cited = 0.
- If the plan implies guideline-governed decisions but has zero explicit citations, list likely missing citations.

5) Safety net + follow-up
- Confirm a5.5 contains emergency/red-flag advice and a follow-up plan.
- Cross-check a2.5 escalation pathway is not contradicted by a5.5.

Output must be valid JSON (ValidationPlanner object with `validation_report` property, which contains all required fields) – no extra keys.
- Do NOT include comments (no // or /* */)
- Do NOT include trailing commas""", base_class=ValidationPlanner)



