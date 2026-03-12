from typing import Optional
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from Neurology_Orchestrator.steps.base_step import BaseStep
import ast


class Hypothesis(BaseModel):
    anatomical_position: str = Field(description="Anatomical position of the diagnosis")
    pathophysiology: str = Field(description="Pathophysiology of the diagnosis")
    rationale: str = Field(description="One‑sentence rationale.")
    likelihood: float = Field(description="Probability that the diagnosis was correct.")


class Hypotheses(BaseModel):
    hypotheses: list[Hypothesis] = Field(
        description="List of possible anatomical position and pathophysiology of the diagnosis.")
    differential_summary: str = Field(description="Differential summary and reasoning of the diagnosis hypotheses.")


class DiagnosticResult(BaseModel):
    type: Optional[str] = Field(description="Type of the diagnostic test.")
    date: Optional[str] = Field(description="Date of the diagnostic test.")
    key_finding: str = Field(description="Key finding of the diagnostic test.")
    coded: str = Field(description="Coded version of key finding using SNOMED.")
    impression: Optional[str] = Field(description="Impression of the diagnostic test.")
    modality: Optional[str] = Field(description="Modality of the diagnostic test.")
    body_region: Optional[str] = Field(description="Body region of the diagnostic test.")


class DiagnosticResults(BaseModel):
    results: list[DiagnosticResult] = Field(description="List of diagnostic test results.")


class DiagnosicResultsExtractor(BaseStep):

    def __init__(self):
        super().__init__(system_prompt="""
            You are a medical data extraction specialist. Your role is to parse unstructured medical text reports and extract structured, coded data for clinical decision support. 
            You must identify all clinically relevant findings, preserve interpretations, and flag critical values.
            HYPOTHESIS CORRELATION:
            For each finding, consider which current hypotheses it supports or refutes:
            - If abnormal EEG → impacts epilepsy hypothesis
            - If elevated CK → impacts muscle disease hypothesis
            - If brain lesion → impacts structural hypothesis

            For every input you must include:
            "type": str = Field(description="Type of the diagnostic test.")
            "date": str = Field(description="Date of the diagnostic test.")
            "key_finding": str = Field(description="Key finding of the diagnostic test.")
            "coded": str = Field(description="Coded version of key finding using SNOMED in the following format `SNOMED code|SNOMED description`.")
            "impression": str = Field(description="Impression of the diagnostic test.")
            "modality": str = Field(description="Modality of the diagnostic test.")
            "body_region": str = Field(description="Body region of the diagnostic test.")

            IMPORTANT:
            - Extract data exactly as written - do not interpret or diagnose
            - Preserve all numerical values with original units
            - Include both normal and abnormal findings
            - Flag anything requiring immediate clinical attention
            - If genetic report, just extract - GeneticAnalysisSpecialist will interpret
            - If imaging available as pixels, note "Images available for VisionAnalyzer.

        YOU MUST RETURN valid JSON (one top key 'results', which contains a list of all DiagnosticResult) – no extra keys.
        Do not add any other text outside the JSON structure. DO NOT return just a list. You MUST wrap it in an object with "results" key.
        - Do NOT include comments (no // or /* */)
- Do NOT include trailing commas""", base_class=DiagnosticResults)

    def execute(self, input_text, patient_meta, hypotheses):
        parser = PydanticOutputParser(pydantic_object=self.base_class)
        query = input_text
        chain = self.prompt | self.llm | parser
        report = chain.invoke({"query": query, "patient_metadata": patient_meta, "hypotheses": hypotheses})
        return report

    def iterate(
            self,
            row,
            target_column,
            source_column=None,
            source_columns=[],
            patient_meta="a0",
            hypotheses="a24",
    ):
        fields_to_analyse = ["Further Investigations I", "Further Investigations II"]
        results = {}

        any_extracted = False

        for field in fields_to_analyse:
            text = row.get(field, None)

            if text is None or (isinstance(text, str) and text.strip() == ""):
                results[field] = []
                continue

            output = self.execute(text, row.get(patient_meta), row.get(hypotheses))
            extracted = [r.dict() for r in output.results]

            results[field] = extracted
            if len(extracted) > 0:
                any_extracted = True

        if not any_extracted:
            results["summary"] = {
                "message": "No additional diagnostic test results were provided in these sections."
            }

        row[target_column] = results
        return row


class HypothesisRefiner(BaseStep):

    def __init__(self):
        super().__init__(system_prompt="""
        You are a differential diagnosis expert capable of refining differential diagnoses. You may consider using Bayesian probability and clinical decision theory. You update diagnostic probabilities based on new evidence (diagnostic results) while considering test characteristics and disease prevalence.
        INPUT:
        Current Differential: {hypotheses}
        All Previous Results: {diagnostic_results}
        Clinical Trajectory: {clinical_trajectory}
        TASK:
        1. Bayesian update for each diagnosis (make deeper research about this):
           - Pre-test probability: current probability
           - Likelihood ratio: based on test sensitivity/specificity
           - Post-test probability: calculated update
           - Consider disease prevalence (base rates)
        2. Diagnostic criteria check:
           - For each diagnosis, check if formal criteria are met
           - Examples: 
             * McDonald criteria for MS
             * ICHD-3 for headache disorders
        3. Rule out diagnoses if:
           - Definitive negative test (NPV >95%)
           - Multiple contradicting findings
           - Probability <0.05
           - Key criterion definitively absent
        4. Rule in diagnoses if:
           - Pathognomonic finding present
           - All major criteria met
           - Probability >0.90 with confirming test
        5. Add new diagnoses if:
           - Unexpected findings suggest unconsidered diagnosis
           - Clinical trajectory doesn't match current differential
           - Incidental finding requires investigation
        6. Assess convergence:
           - Strong convergence: top diagnosis >0.80, others <0.20
           - Moderate: top diagnosis 0.50-0.80
           - Weak: all diagnoses <0.50
           - Divergent: findings support multiple diagnoses equally
        7. Identify next test:
           - What would maximally discriminate between top 2 diagnoses?
           - Consider: sensitivity, specificity, cost, risk, availability
        Special considerations:
        - avoid sticking to initial diagnosis

         You should extract structured output (SINGLE JSON Object, which contains a differential_summary: (str) and list of Hypothesis in the field `hypotheses`) of up to 8 hypotheses related to the patient state.
         Never use // comments or /* */ comments inside JSON. Do not add any other text outside the JSON structure
         Each hypothesis (json object) should contain information about:
         - anatomical_position (str): Anatomical position of the diagnosis;
         - pathophysiology (str): Pathophysiology of the diagnosis;
         - rationale (str): One sentence rationale about the reasoning why the hypothesis was chosen;
         - likelihood (float): Probability that the diagnosis was correct (from 0 to 1).
         Rules:
         - Do NOT include comments (no // or /* */)
- Do NOT include trailing commas

        """, base_class=Hypotheses)

    def iterate(
            self,
            row,
            target_column,
            source_column=None,
            source_columns=[],
            hypotheses_column="a26",
            diagnostic_results_column="diagnostic_tests_results",
    ):
        fields = ["Further Investigations I", "Further Investigations II"]

        has_any_field = any(
            row.get(field) and
            (not isinstance(row.get(field), str) or row.get(field).strip())
            for field in fields
        )

        if not has_any_field:
            row[target_column] = {
                "summary": {
                    "message": "No Further Investigations I, Further Investigations II fields present. Refinement skipped.",
                    "hypotheses": row.get(hypotheses_column)
                }
            }
            return row

        raw_val = row.get(diagnostic_results_column, {})
        if isinstance(raw_val, dict):
            diagnostic_results = raw_val
        elif isinstance(raw_val, str) and raw_val.strip():
            diagnostic_results = ast.literal_eval(raw_val)
        else:
            diagnostic_results = {}

        current_hypotheses = row.get(hypotheses_column)
        results = {}

        any_refinement = False

        for idx, field in enumerate(fields):
            if not row.get(field):
                continue

            current_step_results = diagnostic_results.get(field, [])
            if not current_step_results:
                continue

            any_refinement = True

            prior_results = [diagnostic_results.get(fields[i], []) for i in range(idx)]

            trajectory = []
            for i in range(idx + 1):
                for r in diagnostic_results.get(fields[i], []):
                    if isinstance(r, dict) and "type" in r:
                        trajectory.append(r["type"])

            output = self.execute(
                input_text=None,
                hypotheses=current_hypotheses,
                diagnostic_results=prior_results,
                current_diagnostic_results=current_step_results,
                clinical_trajectory=trajectory,
            )

            results[field] = output.dict()
            current_hypotheses = output.dict()

        if not any_refinement:
            results["summary"] = {
                "message": "No additional diagnostic tests or clinical information were received for further refinement.",
                "hypotheses": current_hypotheses,
            }

        row[target_column] = results
        return row

    def execute(self, input_text, hypotheses, diagnostic_results, current_diagnostic_results, clinical_trajectory):
        parser = PydanticOutputParser(pydantic_object=self.base_class)
        chain = self.prompt | self.llm | parser
        report = chain.invoke(
            {"query": current_diagnostic_results, "hypotheses": hypotheses, "diagnostic_results": diagnostic_results,
             "clinical_trajectory": clinical_trajectory})
        return report