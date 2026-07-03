"""End-to-end CBR experiment: split -> tune k (CV) -> evaluate -> plots."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from cbr import CBRDiagnoser, metrics, FEATURES, NUMERIC, NOMINAL

RNG = np.random.default_rng(7)
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(_ROOT, "data", "heart_disease.csv")
RES = os.path.join(_ROOT, "results")
os.makedirs(RES, exist_ok=True)
plt.rcParams.update({"font.size": 11, "figure.dpi": 150})
BLUE, RED, GREEN = "#2563eb", "#dc2626", "#16a34a"


def stratified_split(df, test_frac=0.2, seed=7):
    rng = np.random.default_rng(seed)
    test_idx = []
    for cls in df["target"].unique():
        idx = df.index[df["target"] == cls].to_numpy().copy()
        rng.shuffle(idx)
        n_test = int(round(len(idx) * test_frac))
        test_idx.extend(idx[:n_test])
    test_mask = df.index.isin(test_idx)
    return df[~test_mask].reset_index(drop=True), df[test_mask].reset_index(drop=True)


def stratified_folds(y, n_folds=5, seed=7):
    rng = np.random.default_rng(seed)
    folds = [[] for _ in range(n_folds)]
    for cls in np.unique(y):
        idx = np.where(y == cls)[0].copy()
        rng.shuffle(idx)
        for i, v in enumerate(idx):
            folds[i % n_folds].append(v)
    return [np.array(sorted(f)) for f in folds]


def cross_val_accuracy(Xtr, ytr, k, weighted=True, n_folds=5):
    folds = stratified_folds(ytr, n_folds)
    accs = []
    for i in range(n_folds):
        val = folds[i]
        train = np.concatenate([folds[j] for j in range(n_folds) if j != i])
        model = CBRDiagnoser(k=k, weighted=weighted)
        model.fit(Xtr.iloc[train], ytr[train])
        preds, _ = model.predict(Xtr.iloc[val])
        accs.append(metrics(ytr[val], preds)["accuracy"])
    return float(np.mean(accs)), float(np.std(accs))


def cross_val_metrics(X, y, k, weighted=True, n_folds=5):
    """Full metric CV on a dataset: returns mean of acc/prec/rec/f1 + aggregate CM."""
    folds = stratified_folds(y, n_folds)
    accs, precs, recs, f1s = [], [], [], []
    tp = tn = fp = fn = 0
    for i in range(n_folds):
        val = folds[i]
        train = np.concatenate([folds[j] for j in range(n_folds) if j != i])
        model = CBRDiagnoser(k=k, weighted=weighted)
        model.fit(X.iloc[train], y[train])
        preds, _ = model.predict(X.iloc[val])
        m = metrics(y[val], preds)
        accs.append(m["accuracy"]); precs.append(m["precision"])
        recs.append(m["recall"]); f1s.append(m["f1"])
        c = m["confusion"]; tp += c["tp"]; tn += c["tn"]; fp += c["fp"]; fn += c["fn"]
    return {
        "accuracy": float(np.mean(accs)), "accuracy_std": float(np.std(accs)),
        "precision": float(np.mean(precs)), "recall": float(np.mean(recs)),
        "f1": float(np.mean(f1s)),
        "confusion": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
    }


def main():
    df = pd.read_csv(DATA)
    train_df, test_df = stratified_split(df, 0.2)
    Xtr, ytr = train_df[FEATURES], train_df["target"].to_numpy()
    Xte, yte = test_df[FEATURES], test_df["target"].to_numpy()
    print(f"Train={len(train_df)}  Test={len(test_df)}  "
          f"(disease train={ytr.mean():.2f}, test={yte.mean():.2f})")

    # ---- Tune k via 5-fold CV on training set ----
    k_grid = [1, 3, 5, 7, 9, 11, 15, 21]
    cv_mean, cv_std = [], []
    for k in k_grid:
        m, s = cross_val_accuracy(Xtr, ytr, k, weighted=True)
        cv_mean.append(m); cv_std.append(s)
        print(f"k={k:2d}  CV acc={m:.3f} +/- {s:.3f}")
    best_k = k_grid[int(np.argmax(cv_mean))]
    print("Best k =", best_k)

    # ---- Ablation: weighted vs unweighted similarity (CV) ----
    w_acc, _ = cross_val_accuracy(Xtr, ytr, best_k, weighted=True)
    u_acc, _ = cross_val_accuracy(Xtr, ytr, best_k, weighted=False)

    # ---- Final model on full training set, evaluate on held-out test ----
    model = CBRDiagnoser(k=best_k, weighted=True)
    model.fit(Xtr, ytr)
    train_pred, _ = model.predict(Xtr)
    test_pred, test_conf = model.predict(Xte)
    train_m = metrics(ytr, train_pred)
    test_m = metrics(yte, test_pred)
    print("\nTRAIN:", {k: round(v, 3) for k, v in train_m.items() if k != 'confusion'})
    print("TEST :", {k: round(v, 3) for k, v in test_m.items() if k != 'confusion'})

    # ---- Retain-stage effect: static vs learning case base ----
    m_static = CBRDiagnoser(k=best_k, weighted=True).fit(Xtr, ytr)
    p_static, _ = m_static.solve_and_retain(Xte, retain=False)
    acc_static = metrics(yte, p_static)["accuracy"]
    m_retain = CBRDiagnoser(k=best_k, weighted=True).fit(Xtr, ytr)
    p_retain, _ = m_retain.solve_and_retain(Xte, retain=True)
    acc_retain = metrics(yte, p_retain)["accuracy"]
    print(f"Retain OFF acc={acc_static:.3f} | Retain ON acc={acc_retain:.3f} "
          f"| retained {m_retain.retained} cases")

    # ---- Primary evaluation: 5-fold CV on full dataset (stable) ----
    Xall, yall = df[FEATURES], df["target"].to_numpy()
    cv_full = cross_val_metrics(Xall, yall, best_k, weighted=True)
    print("\nCV-FULL:", {k: round(v, 3) for k, v in cv_full.items() if k != 'confusion'})

    feat_weights = {c: round(model.weights[c], 3) for c in FEATURES}

    results = {
        "n_total": len(df), "n_train": len(train_df), "n_test": len(test_df),
        "disease_rate_total": round(float(df['target'].mean()), 3),
        "best_k": best_k, "k_grid": k_grid,
        "cv_mean": [round(x, 4) for x in cv_mean],
        "cv_std": [round(x, 4) for x in cv_std],
        "weighted_cv_acc": round(w_acc, 4), "unweighted_cv_acc": round(u_acc, 4),
        "train_metrics": train_m, "test_metrics": test_m,
        "cv_full_metrics": cv_full,
        "retain_off_acc": round(acc_static, 4), "retain_on_acc": round(acc_retain, 4),
        "retained_cases": m_retain.retained,
        "feature_weights": feat_weights,
    }
    with open(f"{RES}/metrics.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved metrics.json")

    # ============================ PLOTS ============================
    # 1. Class distribution
    fig, ax = plt.subplots(figsize=(5, 3.4))
    vc = df["target"].value_counts().sort_index()
    ax.bar(["Sehat (0)", "Sakit (1)"], vc.values, color=[GREEN, RED])
    for i, v in enumerate(vc.values):
        ax.text(i, v + 2, str(v), ha="center", fontweight="bold")
    ax.set_ylabel("Jumlah pasien"); ax.set_title("Distribusi Kelas Dataset")
    fig.tight_layout(); fig.savefig(f"{RES}/fig_class_distribution.png"); plt.close(fig)

    # 2. k vs CV accuracy
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    ax.errorbar(k_grid, cv_mean, yerr=cv_std, marker="o", color=BLUE, capsize=3)
    ax.axvline(best_k, ls="--", color=RED, alpha=0.7, label=f"k terbaik = {best_k}")
    ax.set_xlabel("Jumlah tetangga (k)"); ax.set_ylabel("Akurasi CV (5-fold)")
    ax.set_title("Pemilihan k via Cross-Validation"); ax.legend()
    fig.tight_layout(); fig.savefig(f"{RES}/fig_k_selection.png"); plt.close(fig)

    # 3. Confusion matrix (5-fold CV aggregate on full data)
    cm_d = cv_full["confusion"]
    cm = np.array([[cm_d["tn"], cm_d["fp"]], [cm_d["fn"], cm_d["tp"]]])
    fig, ax = plt.subplots(figsize=(4.2, 3.8))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["Pred Sehat", "Pred Sakit"])
    ax.set_yticklabels(["Asli Sehat", "Asli Sakit"])
    thr = cm.max() / 2
    for i in range(2):
        for j in range(2):
            ax.text(j, i, cm[i, j], ha="center", va="center",
                    color="white" if cm[i, j] > thr else "black",
                    fontsize=15, fontweight="bold")
    ax.set_title("Confusion Matrix (5-fold CV)")
    fig.colorbar(im, fraction=0.046, pad=0.04)
    fig.tight_layout(); fig.savefig(f"{RES}/fig_confusion_matrix.png"); plt.close(fig)

    # 4. Metrics bar (train vs test)
    labels = ["Accuracy", "Precision", "Recall", "F1-Score"]
    te = [cv_full["accuracy"], cv_full["precision"], cv_full["recall"], cv_full["f1"]]
    ho = [test_m["accuracy"], test_m["precision"], test_m["recall"], test_m["f1"]]
    x = np.arange(len(labels)); w = 0.38
    fig, ax = plt.subplots(figsize=(6, 3.6))
    b1 = ax.bar(x - w/2, te, w, label="5-fold CV", color=BLUE)
    b2 = ax.bar(x + w/2, ho, w, label="Hold-out test", color="#93c5fd")
    for b in list(b1) + list(b2):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.01,
                f"{b.get_height():.2f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 1.08)
    ax.set_ylabel("Skor"); ax.set_title("Metrik Evaluasi CBR"); ax.legend()
    fig.tight_layout(); fig.savefig(f"{RES}/fig_metrics.png"); plt.close(fig)

    # 5. Feature weights
    fw = dict(sorted(feat_weights.items(), key=lambda kv: kv[1]))
    fig, ax = plt.subplots(figsize=(5.4, 4))
    ax.barh(list(fw.keys()), list(fw.values()), color=BLUE)
    ax.set_xlabel("Bobot (relatif)"); ax.set_title("Bobot Fitur (korelasi thd diagnosis)")
    fig.tight_layout(); fig.savefig(f"{RES}/fig_feature_weights.png"); plt.close(fig)

    # 6. Retain effect
    fig, ax = plt.subplots(figsize=(4.6, 3.4))
    bars = ax.bar(["Tanpa Retain", "Dengan Retain"], [acc_static, acc_retain],
                  color=["#93c5fd", BLUE])
    for b in bars:
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.005,
                f"{b.get_height():.3f}", ha="center", fontweight="bold")
    ax.set_ylim(0, 1.0); ax.set_ylabel("Akurasi (data uji)")
    ax.set_title("Pengaruh Tahap Retain")
    fig.tight_layout(); fig.savefig(f"{RES}/fig_retain_effect.png"); plt.close(fig)

    print("Saved 6 figures to results/")


if __name__ == "__main__":
    main()
