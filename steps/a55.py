from typing import List

from pydantic import BaseModel, Field
from Neurology_Orchestrator.steps.base_step import BaseStep


class DrugInteraction(BaseModel):
    drug1: str = Field(description="First drug in the interaction pair.")
    drug2: str = Field(description="Second drug in the interaction pair.")
    severity: str = Field(
        description='Severity of interaction. One of: "contraindicated" | "major" | "moderate" | "minor".'
    )
    mechanism: str = Field(description="Mechanism of the interaction.")
    clinical_effect: str = Field(description="Clinical effect or consequence of the interaction.")
    management: str = Field(
        description='Recommended management. One of: "avoid" | "adjust_dose" | "monitor" | "separate_timing".'
    )


class Contraindication(BaseModel):
    drug: str = Field(description="Drug that is contraindicated.")
    reason: str = Field(description="Reason for the contraindication.")
    type: str = Field(
        description='Type of contraindication. One of: "absolute" | "relative".'
    )
    alternative_options: List[str] = Field(
        description="List of safer alternative options if this drug is contraindicated."
    )


class DoseAdjustment(BaseModel):
    drug: str = Field(description="Drug that requires dose adjustment.")
    factor: str = Field(
        description='Reason for adjustment. One of: "age" | "weight" | "renal" | "hepatic".'
    )
    original_dose: str = Field(description="Original dose as stated.")
    adjusted_dose: str = Field(description="Recommended adjusted dose.")
    rationale: str = Field(description="Short rationale for the adjustment.")
    monitoring_required: List[str] = Field(
        description="List of parameters that should be monitored (e.g. creatinine, LFTs, drug levels)."
    )


class MonitoringItem(BaseModel):
    parameter: str = Field(description="Clinical or laboratory parameter to monitor.")
    frequency: str = Field(description="How often the parameter should be monitored.")
    target_range: str = Field(description="Target range or desired goal, if applicable.")

class AllergyAlert(BaseModel):
    substance: str = Field(description="Drug or substance the patient is allergic to (e.g. penicillin, iodine contrast).")
    reaction: str = Field(description="Description of the allergic reaction (e.g. rash, anaphylaxis, angioedema).")
    severity: str = Field(description='Severity of allergy. One of: "mild" | "moderate" | "severe" | "anaphylaxis".')
    management: str = Field(description="Recommended management (e.g. avoid, premedicate, desensitization, use alternative drug).")

class SafetyCheck(BaseModel):
    drug_interactions: List[DrugInteraction] = Field(description="All relevant drug-drug interactions with severity, mechanism, clinical effect, and management.")
    contraindications: List[Contraindication] = Field(description="List of absolute and relative contraindications.")
    dose_adjustments: List[DoseAdjustment] = Field(description="Recommended dose adjustments based on age, renal, hepatic, or weight factors.")
    therapeutic_duplications: List[str] = Field(description="List of therapeutic duplications (e.g., multiple drugs from same class without clear reason).")
    monitoring_plan: List[MonitoringItem] = Field(description="Comprehensive monitoring plan for high-risk or adjusted therapies.")
    safe_to_proceed: bool = Field(description="Overall judgement if it is safe to proceed with the proposed regimen as is.")
    requires_modification: bool = Field(description="Whether treatment plan requires modification before it is safe.")
    pharmacy_consultation_needed: bool = Field(description="Whether a live clinical pharmacist consultation is required.")
    high_alert_medications: List[str] = Field(description="List of high-alert medications in the regimen that need extra caution.")


class SafetyCheckEnvelope(BaseModel):
    safety_check: SafetyCheck = Field(description="Top-level safety_check object containing all safety assessment fields.")
class A55Step(BaseStep):

    def __init__(self):
        super().__init__(
            system_prompt="""
            SYSTEM:
            You are a clinical pharmacist specializing in neurology reviewing medication safety and interactions.
            TASK:
            1. Check ALL drug-drug interactions:
               - Between proposed and current medications
               - Between multiple proposed medications
               - Classify severity: contraindicated > major > moderate > minor
            2. Identify contraindications:
               - Absolute (never give)
               - Relative (use with caution)
               - Provide alternatives for contraindicated drugs
            3. Calculate dose adjustments:
               - Elderly (>65): consider reduced dosing
               - Renal impairment: use CrCl if available
               - Hepatic impairment: check LFTs
               - Pediatric: weight-based dosing
            4. Check for therapeutic duplications
            5. Create monitoring plan for high-risk drugs
            Critical interactions to check:
            - Enzyme inducers (carbamazepine, phenytoin) → reduced efficacy of other drugs
            - Enzyme inhibitors → increased toxicity
            - QT prolongation risk (multiple psychotropics)
            - Bleeding risk (antiplatelet + anticoagulant)
            - Serotonin syndrome risk (SSRIs + other serotonergic drugs)
            - Lithium interactions (NSAIDs, ACE-I, thiazides)
            Neurological drug considerations:
            - Antiepileptics: check for Stevens-Johnson risk (HLA-B*1502 in Asians)
            - Benzodiazepines in elderly: fall risk, cognitive impairment
            - Anticholinergics: cognitive burden in elderly
            - Dopamine antagonists: extrapyramidal symptoms
            6. Evaluate ALLERGIES:
               - Identify any proposed drugs that are contraindicated due to known allergies.
               - Include both drug-specific allergies (e.g. penicillin) and class allergies (e.g. beta-lactams).
               - Suggest safe alternatives where possible.

For the safety_check object must include these fields:

- "drug_interactions": (list[dict]) – List of all drug–drug interactions. Each item MUST contain:
  - "drug1": (str) – First drug in the interaction pair.
  - "drug2": (str) – Second drug in the interaction pair.
  - "severity": (str) – Severity of the interaction. One of: "contraindicated" | "major" | "moderate" | "minor".
  - "mechanism": (str) – Mechanism of the interaction.
  - "clinical_effect": (str) – Clinical effect or consequence of the interaction.
  - "management": (str) – Recommended management. One of: "avoid" | "adjust_dose" | "monitor" | "separate_timing".
- "contraindications": (list[dict]) – List of absolute and relative contraindications. Each item MUST contain:
  - "drug": (str) – Drug that is contraindicated.
  - "reason": (str) – Reason for the contraindication.
  - "type": (str) – Type of contraindication. One of: "absolute" | "relative".
  - "alternative_options": (list[str]) – Safer alternative options if this drug is contraindicated.
- "dose_adjustments": (list[dict]) – Dose adjustments based on age, weight, renal, or hepatic function. Each item MUST contain:
  - "drug": (str) – Drug that requires dose adjustment.
  - "factor": (str) – Reason for adjustment. One of: "age" | "weight" | "renal" | "hepatic".
  - "original_dose": (str) – Original dose as stated.
  - "adjusted_dose": (str) – Recommended adjusted dose.
  - "rationale": (str) – Short rationale for the adjustment.
  - "monitoring_required": (list[str]) – Parameters that should be monitored (e.g. creatinine, LFTs, drug levels).
- "therapeutic_duplications": (list[str]) – List of therapeutic duplications (e.g. multiple drugs from same class without clear reason).
- "monitoring_plan": (list[dict]) – Monitoring plan for high-risk or adjusted therapies. Each item MUST contain:
  - "parameter": (str) – Clinical or laboratory parameter to monitor.
  - "frequency": (str) – How often the parameter should be monitored.
  - "target_range": (str) – Target range or desired goal, if applicable.
- "allergy_alerts": (list[dict]) – Allergy-related safety issues. Each item MUST contain:
  - "substance": (str) – Drug or substance the patient is allergic to.
  - "reaction": (str) – Description of the allergic reaction.
  - "severity": (str) – One of: "mild" | "moderate" | "severe" | "anaphylaxis".
  - "management": (str) – Recommended management (e.g. avoid, premedicate, alternative drug).
- "safe_to_proceed": (bool) – Overall judgement if it is safe to proceed with the proposed regimen as is.
- "requires_modification": (bool) – Whether the treatment plan requires modification before it is safe.
- "pharmacy_consultation_needed": (bool) – Whether a live clinical pharmacist consultation is required.
- "high_alert_medications": (list[str]) – List of high-alert medications in the regimen that need extra caution.
Output must be valid JSON (one top key `safety_check`, which contains all of the above safety assessment information) – no extra keys. 
Do not add any other text outside the JSON structure.

            """,
            base_class=SafetyCheckEnvelope,)
