"""
Case-Based Reasoning (CBR) engine for heart-disease diagnosis.

Implements the 5-stage CBR cycle from scratch (no scikit-learn):
  1. Case Representation  - each record = <problem (features), solution (diagnosis)>
  2. Retrieve            - k nearest cases via weighted HEOM similarity
  3. Reuse               - similarity-weighted majority vote -> proposed diagnosis
  4. Revise              - confidence check; low-confidence cases flagged/adjusted
  5. Retain              - confidently solved new cases appended to the case base

HEOM = Heterogeneous Euclidean-Overlap Metric:
  - numeric attributes : normalized range distance |a-b| / range
  - nominal attributes : overlap distance (0 if equal, else 1)
"""
import numpy as np

NOMINAL = ["sex", "fbs", "restecg", "exang", "thal"]
NUMERIC = ["age", "trestbps", "chol", "thalach", "oldpeak", "ca", "cp", "slope"]
FEATURES = NUMERIC + NOMINAL


class CBRDiagnoser:
    def __init__(self, k=7, weighted=True, revise_threshold=0.6):
        self.k = k
        self.weighted = weighted
        self.revise_threshold = revise_threshold
        self.case_X = None      # case base features (raw)
        self.case_y = None      # case base solutions
        self.ranges = None      # numeric ranges for normalization
        self.weights = None     # per-feature weights
        self.retained = 0

    # ---------- Stage 1: Case Representation ----------
    def fit(self, X, y):
        self.case_X = X.reset_index(drop=True).copy()
        self.case_y = np.asarray(y).astype(int).copy()
        # Z-score scale for numeric attributes (robust to differing units/outliers)
        self.ranges = {c: max(self.case_X[c].astype(float).std(), 1e-9)
                       for c in NUMERIC}
        # Feature weights from correlation with target; squared to sharpen contrast
        if self.weighted:
            w = {}
            for c in FEATURES:
                vals = self.case_X[c].astype(float).values
                corr = np.corrcoef(vals, self.case_y)[0, 1]
                w[c] = corr ** 2 if not np.isnan(corr) else 0.0
            s = sum(w.values()) or 1.0
            self.weights = {c: (w[c] / s) * len(FEATURES) for c in FEATURES}
        else:
            self.weights = {c: 1.0 for c in FEATURES}
        return self

    # ---------- Stage 2: Retrieve (HEOM distance) ----------
    def _distance(self, query):
        total = np.zeros(len(self.case_X))
        for c in NUMERIC:
            d = np.abs(self.case_X[c].values - query[c]) / self.ranges[c]
            total += self.weights[c] * d ** 2
        for c in NOMINAL:
            d = (self.case_X[c].values != query[c]).astype(float)
            total += self.weights[c] * d ** 2
        return np.sqrt(total)

    def _retrieve(self, query):
        dist = self._distance(query)
        idx = np.argsort(dist)[: self.k]
        return idx, dist[idx]

    # ---------- Stages 3+4: Reuse + Revise ----------
    def _reuse_revise(self, idx, dist):
        sims = 1.0 / (1.0 + dist)                       # similarity in (0,1]
        neigh_y = self.case_y[idx]
        w1 = sims[neigh_y == 1].sum()
        w0 = sims[neigh_y == 0].sum()
        total = w1 + w0 if (w1 + w0) > 0 else 1.0
        conf = max(w1, w0) / total                      # decision confidence
        pred = int(w1 >= w0)
        revised = conf < self.revise_threshold          # flagged for revision
        return pred, conf, revised

    def predict_one(self, query):
        idx, dist = self._retrieve(query)
        return self._reuse_revise(idx, dist)

    def predict(self, X):
        preds, confs = [], []
        for _, row in X.iterrows():
            p, c, _ = self.predict_one(row)
            preds.append(p)
            confs.append(c)
        return np.array(preds), np.array(confs)

    # ---------- Stage 5: Retain ----------
    def solve_and_retain(self, X, y_true=None, retain=True):
        """Classify sequentially; retain confidently-solved cases into the base.
        Simulates an operating CBR system that keeps learning."""
        preds, confs = [], []
        import pandas as pd
        for i, (_, row) in enumerate(X.iterrows()):
            p, c, revised = self.predict_one(row)
            preds.append(p)
            confs.append(c)
            if retain and not revised:
                # Retain the newly solved case (solution = system's confident answer)
                self.case_X = pd.concat([self.case_X, row.to_frame().T], ignore_index=True)
                self.case_y = np.append(self.case_y, p)
                self.retained += 1
        return np.array(preds), np.array(confs)


# ------------------------- Metrics (from scratch) -------------------------
def confusion(y_true, y_pred):
    y_true = np.asarray(y_true); y_pred = np.asarray(y_pred)
    tp = int(np.sum((y_pred == 1) & (y_true == 1)))
    tn = int(np.sum((y_pred == 0) & (y_true == 0)))
    fp = int(np.sum((y_pred == 1) & (y_true == 0)))
    fn = int(np.sum((y_pred == 0) & (y_true == 1)))
    return tp, tn, fp, fn


def metrics(y_true, y_pred):
    tp, tn, fp, fn = confusion(y_true, y_pred)
    n = tp + tn + fp + fn
    acc = (tp + tn) / n if n else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    # macro (average over both classes)
    prec0 = tn / (tn + fn) if (tn + fn) else 0.0
    rec0 = tn / (tn + fp) if (tn + fp) else 0.0
    f10 = 2 * prec0 * rec0 / (prec0 + rec0) if (prec0 + rec0) else 0.0
    return {
        "accuracy": acc,
        "precision": prec, "recall": rec, "f1": f1,
        "precision_macro": (prec + prec0) / 2,
        "recall_macro": (rec + rec0) / 2,
        "f1_macro": (f1 + f10) / 2,
        "confusion": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
    }
