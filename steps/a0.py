from typing import Optional
from pydantic import BaseModel, Field
from Neurology_Orchestrator.steps.base_step import BaseStep


class MetadataAttributes(BaseModel):
        age: Optional[float] = Field(description="Age in years (float); if infant/baby -> null.")
        age_months: Optional[float] = Field(description="Age in months for infants/babies; otherwise null.")
        sex: Optional[str] = Field(description='Patient sex: "male" or "female".')
        date_of_event: Optional[str] = Field(description="ISO date string 'YYYY-MM-DD' or null.")
        chief_complaint: Optional[str] = Field(description="Most recent symptoms/diseases; null if unclear.")
        chief_complaint_tempo: Optional[str] = Field(description="Tempo/pattern of the chief complaint.")
        present_actual_disease: Optional[str] = Field(description="Chronological current illness narrative; NOT PMH.")
        past_medical_history: Optional[str] = Field(description="Comma-separated PMH (and pregnancy route if infant).")
        family_history: Optional[str] = Field(description="Family history in direct relatives.")
        psychic_exam: Optional[str] = Field(
            description="Mental state: alertness, speech, orientation; copy verbatim when possible.")
        somatic_exam: Optional[str] = Field(
            description="General/internal medicine exam incl. vitals/cardiology; NOT neurology.")
        neuro_exam: Optional[str] = Field(description="Neurologic exam: CN, motor, sensory, cerebellar, reflexes, etc.")
        laboratory_tests: Optional[str] = Field(
            description="Blood/urine/CSF labs, toxicology, genetics if reported as labs; copy verbatim.")
        electrophysiology_tests: Optional[str] = Field(description="EEG/EMG/NCS and related; copy verbatim.")
        neuroradiology_tests: Optional[str] = Field(
            description="CT/MRI/angiography/PET/SPECT/fMRI etc.; copy verbatim.")
        additional_tests: Optional[str] = Field(
            description="Rare/advanced tests (biopsy, endoscopy, DEXA t/z-score etc.); copy verbatim.")

class A0Step(BaseStep):

    def __init__(self):
        super().__init__(system_prompt="""
         You are an information‑extraction engine for neurology case reports. 
            If a key is not found OR if the text explicitly states the data is absent 
            (e.g., "no personal or family medical history"), set the value to null. Do NOT invent data.
            Do NOT omit standardized clinical scores if present. Extract them verbatim with the numeric value.
            Never duplicate the same content across multiple fields. Each clinical finding must appear in only one field.

            TASK
            Extract the following fields in JSON format from the clinical text:

            • age (float, years), if it is infant or baby->null
            • age_months (float, months for infants, babies, else null)
            • sex ("male" | "female")  
            • date_of_event (string only date in ISO8601 format "yyyy-mm-dd" or null. DO NOT include comments. MUST be in string format "yyyy-mm-dd")
            • chief_complaint (string; presents just a simple list of main symptoms, which are then elaborated in detail in the history of the actual illness. If not clearly stated, return null.) 
            • chief_complaint_tempo (string, plain text, declare if symptoms are acute, subacute, chronic, progressive, episodic. Other things go to history)
            • present_actual_disease (string; This is a detailed, chronological account of a patient’s current illness, covering the onset, development, symptoms, and previous treatments(medications, anti-edema therapy, steroids, chemotherapy, radiotherapy, AND surgical procedures/outcomes) related to the present complaint. EXCLUDE examination-based scales/scores and named clinical tests (e.g., GCS, AIS, GOAT, Ranchos LOCF, CMSA, Timed Up and Go). This is NOT past medical history.)  
            • past_medical_history (comma‑separated string; Patient’s previous health conditions, illnesses, injuries, hospitalizations, surgeries, allergies and treatments prior to the current encounter, if it is a infant also a mother pregnancy clinical route if present)  
            • family_history (string; Medical information regarding a patient's direct blood relatives (parents, siblings, grandparents) to identify genetic predispositions, hereditary diseases, and shared environmental risk factors. If there is no data, put "no significant data")  
            • psychic_exam (string; copy includes assessment of a patient's current mental state (as quantitative function of alertness), speech, scales based on clinical examination and orientation from text. DO NOT EXTRACT neurological signs (e.g., tremor, rigidity, weakness, reflexes, gait, coordination, cranial nerves, tone, muscle findings) and physical/somatic exam findings.If a sentence contains mixed psychiatric and neurological findings, 
you MUST split the sentence and extract ONLY the psychiatric portion. DO not paraphrase. Do Not summarize)
            • somatic_exam (string; general observation, vital signs, cardiology findings like ECG, if it describes joint mobility or posture WITHOUT mentioning tone, rigidity, or neurologic cause or any other internal medicine findings, not neurology findings as they appear in text. DO NOT include patients complaints, concerns, laboratory findings. DO not paraphrase. Do Not summarize)
            • neuro_exam (Extract examination of cranial nerves, motor function, sensory function, cerebellar function, strength, reflexes, myotomes, dermatomes, scales based on clinical examination, if it describes abnormal tone, rigidity, tremor, reflex change, or neurologic sign etc. DO not paraphrase. Do Not summarize)
            • laboratory_tests — (copy ONLY Routine or advanced analysis of blood, urine, CSF et. In broad terms can include toxicology or genetic testing but it is usually performed and report latter than primary examination or admission)
            • electrophysiology_tests — Diagnostic procedures that measure and analyze the electrical activity of the central and peripheral nervous systems, as well as muscles, to evaluate their functional status. These tests include EEG, EMG, and NCS (nerve conduction study))
            • neuroradiology_tests (string; copy Radiology procedures like X-ray graph (nowadays rarely), CT, MRI, angiography, Also can include advanced techniques like SPECT, PET, functional MRI)
            • additional_tests — Advanced and rarely used methods, sometimes just mentioned by the name, results or final scores, like biopsy CSF analysis, biopsy (core needle/lesion biopsy), endoscopy, bone mineralometry / DEXA (t-score, z-score) etc.
            """, base_class=MetadataAttributes)


