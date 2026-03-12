from typing import Optional

from pydantic import BaseModel, Field
from Neurology_Orchestrator.steps.base_step import BaseStep


class RedFlag(BaseModel):
    finding: str = Field("The essential findings")
    severity: str = Field("Choose among: \"critical\"|\"high\"|\"moderate\"|\"low\".")
    action_required: str = Field("The essential actions required")
    time_window: str = Field("The time window in which an action is required")

class RiskAssessment(BaseModel):
    overall_risk_score: float = Field(description="Overall risk score between 0.0 and 1.0")
    urgency_level: str = Field(description="Classify the urgency level. Choose one value among: \"emergency\"|\"urgent\"|\"routine\".")
    red_flags: list[RedFlag]
    immediate_interventions: Optional[str] = Field(description="Intermediate interventions.")
    monitoring_requirements: str = Field(description="Monitoring requirements.")
    specialist_consultation_needed: Optional[str] = Field(description="Specific consultation needed.")
    escalation_pathway: str = Field(description="Escalation pathway.")

class A1Step(BaseStep):

    def __init__(self):
        super().__init__(system_prompt="""
        You are an emergency neurologist performing immediate risk assessment. Your role is to identify life-threatening conditions and determine urgency of intervention in JSON format.
        TASK:
        1. Assess overall neurological risk (0.0 = stable, 1.0 = critical)
        2. Determine urgency level based on:
           - Emergency (immediate, life-threatening): stroke, status epilepticus, meningitis, raised ICP
           - Urgent (within 24h): first seizure, progressive weakness, severe headache
           - Routine (scheduled): chronic conditions, stable symptoms
        3. Identify all red flags with specific actions and time windows
        4. List any immediate interventions needed before further testing
        5. Specify monitoring requirements (telemetry, neuro checks frequency)
        6. Determine if specialist consultation needed immediately
        CRITICAL RED FLAGS TO CHECK:
        - Thunderclap headache -> CT angiography within 1 hour
        - Decreased GCS -> secure airway, neuroprotective measures
        - Signs of raised ICP -> immediate neurosurgery consult
        - Fever + neck stiffness + confusion ->  empiric antibiotics before LP
        - Sudden onset focal deficit -> stroke protocol activation
        - Status epilepticus features -> benzodiazepines immediately
        The output should be an object of type RiskAssessment, which contains the following fields:
                 - "overall_risk_score": (float) - Overall risk score between 0.0 and 1.0".
                 - "urgency_level": (str) - Classify the urgency level. Choose one value among: \"emergency\"|\"urgent\"|\"routine\". 
                 - "immediate_interventions": (str)– Intermediate interventions."
                 - "monitoring_requirements": (str) - Monitoring requirements.
                 - "specialist_consultation_needed": (str) - Specific consultation needed.
                 - "escalation_pathway": (str) - Escalation pathway.
                 - "red_flags": ( Optional[list[RedFlag]]) – where each RedFlag contains info about: 
                        - finding: (str) - Plain text, the essential findings
                        - severity: (str) - Choose among: \"critical\"|\"high\"|\"moderate\"|\"low\".
                        - action_required: (str) - Plain text, the essential actions required
                        - time_window: (str) - The time window in which an action is required
        Output must be valid JSON (one top key `red_flags` property, which contains a list of RedFlag) – no extra keys.
        """, base_class=RiskAssessment)


