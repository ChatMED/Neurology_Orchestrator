from typing import Optional

from pydantic import BaseModel, Field
from Neurology_Orchestrator.steps.base_step import BaseStep

class Treatment(BaseModel):
    treatment: Optional[str] = Field(description="Drug/therapy that the patient should take.")
    dose: Optional[str]= Field(description="The dose of the drug/therapy.")
    timing: Optional[str] = Field(description="Attach guideline references (e.g., \"NICE CG137 1.6.4\"). If there are multiple conflicting or consistent recommendations, provide a reference to all of them. ")
    reason: Optional[str] = Field(description="The reason why the patient should take the drug/therapy.")
    linked_hypothesis: Optional[str]= Field(description="The hypothesis that is linked for the drug/therapy.")
    mandatory: Optional[str] = Field(description="Is the drug/terapy mandatory or optional?")

class TreatmentPlanner(BaseModel):
    treatments: list[Treatment] = Field(description="List of possible drugs/therapies the user should take based on the summary and hypotheses and examinations.")


class A5Step(BaseStep):

    def __init__(self):
        super().__init__(system_prompt="""
         You are a neurologists that prepares an initial therapy plan.
         For the highest ranked hypothesis, list suitable drugs/therapies AND/OR “watchful waiting”, depending on clinical certainty.
         - Link to hypothesis by index.
         - Include dosage, timing, and brief reason citing guideline sections.
         
         
         For every drug/therapy must include these fields:
         - "treatment": (str) - The drug/therapy name that the patient should take.
         - "dose": (str) - The dose in string format. Mandatory field. If none/null write "N/A".
         - "linked_hypothesis": (str) - The string ID of the hypothesis that is linked for the drug/therapy. 
         - "reason": (str) – The reason why the patient should take the drug/therapy.
         - "mandatory": (str) - Is the drug/therapy mandatory or optional?
         - "timing": (str) - The timeframe within which the patient should take the drug/therapy.
         
         CLINICAL DECISION GATE:
        If EEG or key investigations are still pending AND the patient is clinically stable (no status epilepticus, no progressive deficits, no high-frequency seizures):
        
        - You MUST consider "Watchful waiting" as a primary option.
        - Drug therapy should usually be marked "Optional", not "Mandatory".
        - You MAY assign higher priority to watchful waiting than drug initiation.
        - Do NOT make antiepileptic treatment "Mandatory" unless there is clear high-risk (frequent seizures, injury risk, status epilepticus, or severe impairment).
        
        Therapy initiation depends on clinical context, comorbidities, and concurrent medications; if these are missing, avoid mandatory treatment.         
        Output must be valid JSON (one top key `treatments`, which contains list of all the required info related to each treatment) – no extra keys.
        - Do NOT include comments (no // or /* */)
- Do NOT include trailing commas
""", base_class=TreatmentPlanner)


