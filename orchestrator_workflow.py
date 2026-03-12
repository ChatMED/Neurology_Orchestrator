import pandas as pd
import json
from tqdm import tqdm
import traceback
from concurrent.futures import ThreadPoolExecutor
from Neurology_Orchestrator.steps.a0 import A0Step
from Neurology_Orchestrator.steps.a1 import A1Step
from Neurology_Orchestrator.steps.a21 import A21Step
from Neurology_Orchestrator.steps.a22 import A22Step
from Neurology_Orchestrator.steps.a23 import A23Step
from Neurology_Orchestrator.steps.a24 import A24Step
from Neurology_Orchestrator.steps.a3 import A3Step
from Neurology_Orchestrator.steps.a31 import A31Step
from Neurology_Orchestrator.steps.a25 import A25Step
from Neurology_Orchestrator.steps.a4 import A4Step
from Neurology_Orchestrator.steps.a5 import A5Step
from Neurology_Orchestrator.steps.a55 import A55Step
from Neurology_Orchestrator.steps.a6 import A6Step
from Neurology_Orchestrator.steps.hypothesis_refiner import DiagnosicResultsExtractor, HypothesisRefiner


def get_meta_field(row, field):
    try:
        meta = json.loads(row["A0"])
        return meta.get(field)
    except:
        return None


def build_input_h1(row):
    meta = json.loads(row["A0"])
    return {
        "chief_complaint": meta.get("chief_complaint"),
        "neuro_exam": meta.get("neuro_exam"),
        "chief_complaint_tempo": meta.get("chief_complaint_tempo"),
        "neuroradiology_tests": meta.get("neuroradiology_tests"),
        "electrophysiology_tests": meta.get("electrophysiology_tests")
    }


def build_input_h2(row):
    meta = json.loads(row["A0"])
    h1 = json.loads(row["A2-H1"])

    return {
        "localization_hypotheses": h1,
        "chief_complaint_tempo": meta.get("chief_complaint_tempo"),
        "past_medical_history": meta.get("past_medical_history"),
        "family_history": meta.get("family_history"),
        "somatic_exam": meta.get("somatic_exam"),
        "age": meta.get("age"),
        "sex": meta.get("sex"),
        "present_actual_disease": meta.get("present_actual_disease")
    }


def build_input_h3(row):
    h1 = json.loads(row["A2-H1"])
    h2 = json.loads(row["A2-H2"])
    meta = json.loads(row["A0"])
    risk_assesments = json.loads(row["A1"])

    return {
        "age": meta.get("age"),
        "sex": meta.get("sex"),
        "past_medical_history": meta.get("past_medical_history"),
        "present_actual_disease": meta.get("present_actual_disease"),
        "family_history": meta.get("family_history"),
        "pathophysiology_hypotheses": h2,
        "localization_hypotheses": h1,
        "risk_assesments": risk_assesments,
    }


def build_input_h4(row):
    meta = json.loads(row["A0"])
    h3 = json.loads(row["A2-H3"])
    risk_assesments = json.loads(row["A1"])

    return {
        "diagnosis_list": h3,
        "age": meta.get("age"),
        "sex": meta.get("sex"),
        "past_medical_history": meta.get("past_medical_history"),
        "family_history": meta.get("family_history"),
        "present_actual_disease": meta.get("present_actual_disease"),
        "risk_assesments": risk_assesments
    }


def build_diagnostic_input(row):
    meta = json.loads(row["A0"])
    h4 = json.loads(row["A2-H4"])
    return {
        "hypothesis": h4,
        "laboratory_tests": meta.get("laboratory_tests"),
        "neuroradiology_tests": meta.get("neuroradiology_tests"),
        "electrophysiology_tests": meta.get("electrophysiology_tests"),
        "additional_tests": meta.get("additional_tests"),
        "neuro_exam": meta.get("neuro_exam"),
        "somatic_exam": meta.get("somatic_exam"),
        "psychic_exam": meta.get("psychic_exam")
    }


base_path = r"..\neurology_dataset.csv"
df = pd.read_csv(base_path)
INPUT_BUILDERS = {
    "A2-H1": build_input_h1,
    "A2-H2": build_input_h2,
    "A2-H3": build_input_h3,
    "A2-H4": build_input_h4,
    "A4": build_diagnostic_input
}

PIPELINE = [
    ("A0", A0Step, ["Introduction"]),
    ("A1", A25Step, ["A0"]),
    ("A2-H1", A21Step, ["A0"]),
    ("A2-H2", A22Step, ["A0", "A2-H1"]),
    ("A2-H3", A23Step, ["A0", "A1", "A2-H1", "A2-H2"]),
    ("A2-H4", A24Step, ["A0", "A1", "A2-H3"]),
    ("A3", A3Step, ["A0", "A1", "A2-H4"]),
    ("A3.1", A31Step, ["A0", "A1", "A3"]),
    ("A2-H5", A26Step, ["A0", "A3.1"]),
    ("A4", A4Step, ["A2-H5"]),
    ("A5", A5Step, ["A0", "A2-H5", "A4"]),
    ("A5.5", A55Step, ["A0", "A5"]),
    ("A6", A6Step, ["A0", "A2-H1", "A2-H2", "A2-H3", "A2-H4", "A1", "A3", "A3.1", "A2-H5", "A4", "A5", "A5.5"]),
    ("diagnostic_tests_results", DiagnosicResultsExtractor, ["A0", "A2-H5"]),
    ("hypothesis_refiner", HypothesisRefiner, ["A2-H5", "diagnostic_tests_results"])
]

for step_name, StepClass, source_cols in PIPELINE:
    print(f"\n{'═' * 12}  Running step: {step_name}  {'═' * 12}")

    step_instance = StepClass()


    def run_step(row):
        try:
          if step_name in INPUT_BUILDERS:
              clean_input = INPUT_BUILDERS[step_name](row)
              payload = json.dumps(clean_input, ensure_ascii=False)

              row_copy = row.copy()
              row_copy["_payload"] = payload

              out = step_instance.iterate(
                  row_copy,
                  step_name,
                  source_columns=["_payload"],
              )

              if "_payload" in out:
                  del out["_payload"]
              return out
          else:
              return step_instance.iterate(
                  row,
                  step_name,
                  source_columns=source_cols,
              )



        except Exception as e:
            row_id = row.get("ID", "unknown")
            print(f"ERROR in row {row_id} at step {step_name}: {e}")
            traceback.print_exc()
            return row


    tqdm.pandas()
    NUM_WORKERS = 12  

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        rows = [row for _, row in df.iterrows()]
        results = list(tqdm(
            executor.map(run_step, rows),
            total=len(rows)
        ))

    df = pd.DataFrame(results)

    out_path = fr"..\out\step_{step_name}.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved: {out_path}")
