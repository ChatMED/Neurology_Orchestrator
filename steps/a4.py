from pydantic import BaseModel, Field
from Neurology_Orchestrator.steps.base_step import BaseStep

class Investigation(BaseModel):
    investigation: str = Field(description="The test/examination/investigation that the patient should make.")
    batch_id: int= Field(description="The order id of the investigation. Lower id means more urgent investigation. Set the same batch id if the investigations should be performed simultaneously.")
    guideline_refs: str = Field(description="Attach guideline references (e.g., \"NICE CG137 1.6.4\"). If there are multiple conflicting or consistent recommendations, provide a reference to all of them. ")
    reason: str = Field(description="The reason why the patient should take the investigation/test.")
    urgency: str= Field(description="The urgency of the investigation.")
    mandatory: str= Field(description="Is the investigation mandatory or optional?")
    timing: str = Field(description="The timeframe within which the patient should perform the investigation/test.")


class InvestigationPlan(BaseModel):
    investigations: list[Investigation] = Field(description="List of possible investigations/tests the user should take based on the summary and hypotheses.")


class A4Step(BaseStep):

    def __init__(self):
        super().__init__(system_prompt="""
         You are drafting an evidence-based investigation plan based on the given input that provides the neurologist summary and highest ranked hypothesis for diagnosis.
         Propose test/examination/investigation that can confirm or rule out top hypothesis.
         Each proposed test/examination/investigation should be aligned with the reason why it is needed.
         Group tests that must be ordered simultaneously, mark with the same "batch_id".
         Mark each as mandatory/optional and urgent/routine with timing. Make sure that the urgency and necessity are in accordance with international guidelines (e.g., EAN, AAN, NICE).
         Attach guideline references (e.g., "NICE CG137 1.6.4"). If there are multiple conflicting or consistent recommendations, provide a reference to all of them. 
         You will also receive the following fields:
         - "laboratory_tests": (string or null) — tests that have ALREADY been completed from the laboratory domain.
         - "neuroradiology_tests": (string or null) — imaging tests that have ALREADY been performed (MRI, CT, X-ray, ultrasound).
         - "electrophysiology_tests": (string or null) — neurophysiology investigations ALREADY completed (EEG, EMG, NCS, evoked potentials).
         - "additional_tests": (string or null) — any other diagnostic tests already performed (genetic tests, CSF analysis, biopsies, etc.)
         - "neuro_exam"
         - "somatic_exam"
         - "psychic_exam"
         These fields list investigations that are already completed so that you DO NOT recommend them again.
         Only propose NEW investigations that have not yet been carried out and are needed to confirm or rule out the working hypotheses.

         For every investigation include:
         - "investigation": (str) - The test/examination/investigation that the patient should make.
         - "batch_id": (int) - The order id of the investigation. Lower id means more urgent investigation. Set the same batch id if the investigations should be performed simultaneously. 
         - "guideline_refs": (str)– Attach guideline references (e.g., "NICE CG137 1.6.4"). If there are multiple conflicting or consistent recommendations, provide a reference to all of them. 
         - "reason": (str) – The reason why the patient should take the investigation/test.
         - "urgency": (str) - Urgent or non-urgent
         - "mandatory": (str) - Is the investigation mandatory or optional?
         - "timing": (str) - The timeframe within which the patient should perform the investigation/test.
         
        URGENCY + TIMING RULES (use these defaults unless red flags are present):
            - "Urgent" = same day / within 24 hours (ED/acute setting).
            - "Non-urgent" = days to weeks (outpatient).

        DEFAULTS FOR NEW-ONSET OR RECURRENT SEIZURES / SYNCOPE-LIKE EPISODES:
        - Basic bloods (CBC, electrolytes, glucose, Ca/Mg, renal/liver) are "Urgent" and timing = "same day (ideally within hours in ED)".
        - Routine interictal EEG is "Mandatory"; urgency = "Urgent" if inpatient/acute presentation OR recent events; timing = "as soon as available, ideally next working day".
        - MRI brain (epilepsy protocol) is "Mandatory" but typically "Non-urgent" if patient is stable; timing = can be more than a week (unless acute focal deficit/status epilepticus).

        Output must be valid JSON (one top key `investigations`, which contains a list of all the required info related to each investigation) – no extra keys.
        - Do NOT include comments (no // or /* */)
- Do NOT include trailing commas
""", base_class=InvestigationPlan)


