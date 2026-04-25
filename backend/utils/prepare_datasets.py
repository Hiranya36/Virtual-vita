import os
import random
from typing import List

import pandas as pd


def _normalize_symptom(value: str) -> str:
    return str(value).strip().replace("_", " ").lower()


def _extract_symptoms_from_row(row: pd.Series, symptom_columns: List[str]) -> List[str]:
    items = []
    for col in symptom_columns:
        val = row.get(col)
        if pd.notna(val) and str(val).strip():
            items.append(_normalize_symptom(val))
    # Remove duplicates while keeping order.
    return list(dict.fromkeys(items))


def _to_noisy_text(symptoms: List[str]) -> str:
    templates = [
        "I have {symptoms}.",
        "Since morning I am feeling {symptoms}.",
        "Patient reports {symptoms}.",
        "I am experiencing {symptoms} for two days.",
        "Complaint: {symptoms}.",
    ]
    joined = ", ".join(symptoms)
    return random.choice(templates).format(symptoms=joined)


def main():
    random.seed(42)
    base_dir = os.path.dirname(os.path.dirname(__file__))
    dataset_dir = os.path.join(base_dir, "dataset")
    input_path = os.path.join(dataset_dir, "dataset.csv")
    cleaned_path = os.path.join(dataset_dir, "dataset_cleaned.csv")
    eval_path = os.path.join(dataset_dir, "cases_eval.csv")

    df = pd.read_csv(input_path)
    symptom_columns = [c for c in df.columns if c.lower().startswith("symptom_")]
    if not symptom_columns:
        raise ValueError("No symptom columns found. Expected Symptom_1..Symptom_n format.")

    rows = []
    seen = set()
    eval_rows = []

    for idx, row in df.iterrows():
        disease = str(row.get("Disease", "")).strip()
        symptoms = _extract_symptoms_from_row(row, symptom_columns)
        if not disease or not symptoms:
            continue

        signature = (disease.lower(), tuple(sorted(symptoms)))
        if signature in seen:
            continue
        seen.add(signature)

        clean_row = {"Disease": disease}
        for i in range(1, 18):
            clean_row[f"Symptom_{i}"] = symptoms[i - 1] if i <= len(symptoms) else ""
        clean_row["symptoms"] = ", ".join(symptoms)
        rows.append(clean_row)

        # Build robust eval entries using complete and incomplete/noisy symptom narratives.
        eval_rows.append(
            {
                "case_id": f"EVAL-{idx:05d}-A",
                "disease_label": disease,
                "symptoms_text": _to_noisy_text(symptoms[: min(5, len(symptoms))]),
                "symptom_tokens": ", ".join(symptoms),
                "input_quality": "complete",
            }
        )
        eval_rows.append(
            {
                "case_id": f"EVAL-{idx:05d}-B",
                "disease_label": disease,
                "symptoms_text": _to_noisy_text(symptoms[: max(1, min(2, len(symptoms)))]),
                "symptom_tokens": ", ".join(symptoms[: max(1, min(2, len(symptoms)))]),
                "input_quality": "incomplete",
            }
        )

    cleaned_df = pd.DataFrame(rows)
    cleaned_df.to_csv(cleaned_path, index=False)

    eval_df = pd.DataFrame(eval_rows)
    eval_df.to_csv(eval_path, index=False)

    print(f"Input rows: {len(df)}")
    print(f"Cleaned unique rows: {len(cleaned_df)}")
    print(f"Saved cleaned dataset: {cleaned_path}")
    print(f"Saved evaluation dataset: {eval_path}")


if __name__ == "__main__":
    main()
