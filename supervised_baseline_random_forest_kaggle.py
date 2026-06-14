from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split


# ============================================================
# SUPERVISED BASELINE FOR KAGGLE
# BENIGN = 0 | ATTACK = 1
# Output files will be saved to /kaggle/working
# ============================================================

KAGGLE_INPUT_DIR = Path("/kaggle/input")
KAGGLE_WORKING_DIR = Path("/kaggle/working")

LOCAL_PROJECT_DIR = Path(__file__).resolve().parent

TARGET_FILE_NAME = "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv"

TRAFFIC_FEATURES = [
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Fwd Packet Length Max",
    "Fwd Packet Length Min",
    "Fwd Packet Length Mean",
    "Fwd Packet Length Std",
    "Bwd Packet Length Max",
    "Bwd Packet Length Min",
    "Bwd Packet Length Mean",
    "Bwd Packet Length Std",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Flow IAT Mean",
    "Flow IAT Std",
    "Flow IAT Max",
    "Flow IAT Min",
    "Fwd IAT Total",
    "Fwd IAT Mean",
    "Fwd IAT Std",
    "Fwd IAT Max",
    "Fwd IAT Min",
    "Bwd IAT Total",
    "Bwd IAT Mean",
    "Bwd IAT Std",
    "Bwd IAT Max",
    "Bwd IAT Min",
    "Fwd PSH Flags",
    "Fwd Header Length",
    "Bwd Header Length",
    "Fwd Packets/s",
    "Bwd Packets/s",
    "Min Packet Length",
    "Max Packet Length",
    "Packet Length Mean",
    "Packet Length Std",
    "Packet Length Variance",
    "FIN Flag Count",
    "SYN Flag Count",
    "RST Flag Count",
    "PSH Flag Count",
    "ACK Flag Count",
    "URG Flag Count",
    "Average Packet Size",
    "Avg Bwd Segment Size",
]


def find_dataset_file() -> Path:
    """
    Kaggle input paths can differ depending on how the dataset is attached.
    This function searches /kaggle/input first, then falls back to local project data.
    """

    preferred_candidates = [
        KAGGLE_INPUT_DIR
        / "datasets"
        / "nguyenhuuhuynh"
        / "cicids2017"
        / "MachineLearningCVE"
        / TARGET_FILE_NAME,
        KAGGLE_INPUT_DIR
        / "cicids2017"
        / "MachineLearningCVE"
        / TARGET_FILE_NAME,
        KAGGLE_INPUT_DIR
        / "MachineLearningCVE"
        / TARGET_FILE_NAME,
    ]

    for candidate in preferred_candidates:
        if candidate.exists():
            return candidate

    if KAGGLE_INPUT_DIR.exists():
        matches = list(KAGGLE_INPUT_DIR.rglob(TARGET_FILE_NAME))
        if matches:
            return matches[0]

    local_candidate = (
        LOCAL_PROJECT_DIR
        / "dataset"
        / TARGET_FILE_NAME
    )
    if local_candidate.exists():
        return local_candidate

    raise FileNotFoundError(
        f"Cannot find {TARGET_FILE_NAME}. "
        "On Kaggle, attach the CICIDS2017 dataset that contains this CSV."
    )


def get_output_dir() -> Path:
    if KAGGLE_WORKING_DIR.exists():
        return KAGGLE_WORKING_DIR
    return LOCAL_PROJECT_DIR


def load_dataset(data_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(data_path)
    df.columns = df.columns.str.strip()

    missing = [
        col for col in TRAFFIC_FEATURES + ["Label"]
        if col not in df.columns
    ]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    x = df[TRAFFIC_FEATURES].copy()
    y = (df["Label"] != "BENIGN").astype(int)

    x.replace([np.inf, -np.inf], np.nan, inplace=True)
    x = x.apply(pd.to_numeric, errors="coerce")

    data = pd.concat(
        [
            x,
            y.rename("target")
        ],
        axis=1
    )
    data.dropna(inplace=True)

    return data[TRAFFIC_FEATURES], data["target"].astype(int)


def main() -> None:
    output_dir = get_output_dir()
    data_path = find_dataset_file()

    result_txt = output_dir / "supervised_baseline_results.txt"
    result_json = output_dir / "supervised_baseline_metrics.json"
    model_path = output_dir / "random_forest_supervised_baseline.pkl"

    print("================================================")
    print("SUPERVISED BASELINE - RANDOM FOREST")
    print("BENIGN = 0 | ATTACK = 1")
    print("================================================")
    print(f"Dataset path: {data_path}")
    print(f"Output dir  : {output_dir}")

    x, y = load_dataset(data_path)
    print(f"Dataset shape: {x.shape}")
    print(f"Label distribution: {y.value_counts().to_dict()}")

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.30,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced",
    )

    print("\n[DANG TRAIN RANDOM FOREST...]")
    model.fit(x_train, y_train)

    print("[DANG DANH GIA...]")
    y_pred = model.predict(x_test)

    metrics = {
        "dataset": str(data_path),
        "model": "RandomForestClassifier",
        "features": len(TRAFFIC_FEATURES),
        "train_samples": int(len(x_train)),
        "test_samples": int(len(x_test)),
        "label_mapping": {
            "BENIGN": 0,
            "ATTACK": 1,
        },
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "classification_report": classification_report(
            y_test,
            y_pred,
            target_names=["BENIGN", "ATTACK"],
            digits=4,
            zero_division=0,
        ),
    }

    report_lines = [
        "================================================",
        "SUPERVISED BASELINE - RANDOM FOREST",
        "================================================",
        f"Dataset: {data_path.name}",
        "Label mapping: BENIGN = 0, ATTACK = 1",
        f"Feature count: {len(TRAFFIC_FEATURES)}",
        f"Train samples: {metrics['train_samples']}",
        f"Test samples: {metrics['test_samples']}",
        "",
        f"Accuracy : {metrics['accuracy']:.6f}",
        f"Precision: {metrics['precision']:.6f}",
        f"Recall   : {metrics['recall']:.6f}",
        f"F1-score : {metrics['f1_score']:.6f}",
        "",
        "Confusion Matrix [[TN, FP], [FN, TP]]:",
        str(metrics["confusion_matrix"]),
        "",
        "Classification Report:",
        metrics["classification_report"],
        "",
        "Ghi chu:",
        "- Day la supervised baseline dung de so sanh voi Autoencoder unsupervised.",
        "- Supervised model can label khi train.",
        "- Autoencoder khong can label attack khi train, phat hien anomaly bang reconstruction error.",
    ]

    result_txt.write_text("\n".join(report_lines), encoding="utf-8")
    result_json.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    joblib.dump(model, model_path)

    print("\n".join(report_lines))
    print("\n================================================")
    print("CAC FILE CAN TAI VE TU /kaggle/working:")
    print(f"1. {result_txt.name}")
    print(f"2. {result_json.name}")
    print(f"3. {model_path.name}")
    print("================================================")


if __name__ == "__main__":
    main()
