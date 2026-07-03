"""
Generate a realistic Heart Disease dataset following the UCI Cleveland schema.

The UCI Heart Disease (Cleveland) dataset is the canonical source behind most
"Heart Disease" datasets on Kaggle. Since this sandbox has no internet access,
we reproduce its exact 13-attribute + target schema and synthesize records
using clinically-informed relationships so that the data carries a learnable
signal (comparable difficulty to the original ~303-row dataset).

Columns (UCI Cleveland schema):
  age      : age in years
  sex      : 1 = male, 0 = female
  cp       : chest pain type (0 typical angina, 1 atypical, 2 non-anginal, 3 asymptomatic)
  trestbps : resting blood pressure (mm Hg)
  chol     : serum cholesterol (mg/dl)
  fbs      : fasting blood sugar > 120 mg/dl (1 true, 0 false)
  restecg  : resting ECG (0 normal, 1 ST-T abnormality, 2 LV hypertrophy)
  thalach  : maximum heart rate achieved
  exang    : exercise-induced angina (1 yes, 0 no)
  oldpeak  : ST depression induced by exercise relative to rest
  slope    : slope of peak exercise ST segment (0 up, 1 flat, 2 down)
  ca       : number of major vessels (0-3) colored by fluoroscopy
  thal     : 1 = normal, 2 = fixed defect, 3 = reversible defect
  target   : 1 = presence of heart disease, 0 = absence
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N = 303  # match the original Cleveland dataset size


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def generate():
    age = np.clip(RNG.normal(54, 9, N), 29, 77).round().astype(int)
    sex = RNG.binomial(1, 0.68, N)  # dataset skews male
    cp = RNG.choice([0, 1, 2, 3], N, p=[0.23, 0.17, 0.28, 0.32])
    trestbps = np.clip(RNG.normal(131, 17, N), 94, 200).round().astype(int)
    chol = np.clip(RNG.normal(246, 51, N), 126, 564).round().astype(int)
    fbs = RNG.binomial(1, 0.15, N)
    restecg = RNG.choice([0, 1, 2], N, p=[0.49, 0.04, 0.47])
    # thalach (max heart rate) tends to fall with age
    thalach = np.clip(202 - 0.7 * age + RNG.normal(0, 17, N), 71, 202).round().astype(int)
    exang = RNG.binomial(1, 0.33, N)
    oldpeak = np.clip(RNG.gamma(1.4, 0.75, N), 0, 6.2).round(1)
    slope = RNG.choice([0, 1, 2], N, p=[0.21, 0.46, 0.33])
    ca = RNG.choice([0, 1, 2, 3], N, p=[0.58, 0.22, 0.13, 0.07])
    thal = RNG.choice([1, 2, 3], N, p=[0.55, 0.07, 0.38])

    # Clinically-informed latent risk score -> probability of disease
    z = (
        -5.6
        + 0.034 * (age - 54)
        + 1.00 * sex
        + 0.75 * cp
        + 0.020 * (trestbps - 131)
        + 0.0040 * (chol - 246)
        + 0.30 * fbs
        + 0.50 * restecg
        - 0.045 * (thalach - 150)
        + 1.45 * exang
        + 1.00 * oldpeak
        + 0.75 * slope
        + 1.40 * ca
        + 1.45 * (thal == 3).astype(float)
        + 0.55 * (thal == 2).astype(float)
    )
    p = sigmoid(z + RNG.normal(0, 0.15, N))  # mild noise -> realistic, learnable
    target = RNG.binomial(1, p)

    df = pd.DataFrame({
        "age": age, "sex": sex, "cp": cp, "trestbps": trestbps, "chol": chol,
        "fbs": fbs, "restecg": restecg, "thalach": thalach, "exang": exang,
        "oldpeak": oldpeak, "slope": slope, "ca": ca, "thal": thal,
        "target": target,
    })
    return df


if __name__ == "__main__":
    df = generate()
    import os
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(ROOT, "data", "heart_disease.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    df.to_csv(out, index=False)
    print("Saved", out, df.shape)
    print(df.head())
    print("\nClass balance:\n", df["target"].value_counts())
    print("\nDisease rate:", round(df["target"].mean(), 3))
