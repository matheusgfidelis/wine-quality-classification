"""Métricas, curvas, matrizes de confusão e interpretação de variáveis."""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.base import clone
from sklearn.inspection import permutation_importance
from sklearn.metrics import (accuracy_score, average_precision_score, confusion_matrix,
                             f1_score, precision_recall_curve, precision_score,
                             recall_score, roc_auc_score, roc_curve)

from . import config
from .eda import COR_ALTA, COR_BAIXA, _salvar
from .preprocessing import NOMES_PT


def metricas(y, proba, limiar: float = 0.5) -> dict:
    """Métricas da classe ALTA (rótulo 1) + métricas globais."""
    pred = (proba >= limiar).astype(int)
    return {
        "limiar": float(limiar),
        "accuracy": accuracy_score(y, pred),
        "precision_alta": precision_score(y, pred, zero_division=0),
        "recall_alta": recall_score(y, pred, zero_division=0),
        "f1_alta": f1_score(y, pred, zero_division=0),
        "roc_auc": roc_auc_score(y, proba),
        "pr_auc": average_precision_score(y, proba),
    }


def melhor_limiar_f1(y, proba) -> float:
    """Limiar que maximiza o F1 da classe alta (usar SÓ com probabilidades OOF do treino)."""
    grade = np.linspace(0.05, 0.95, 91)
    f1s = [f1_score(y, (proba >= t).astype(int), zero_division=0) for t in grade]
    return float(grade[int(np.argmax(f1s))])


def bootstrap_ic(y, proba, limiar=0.5, n=1000, seed=config.RANDOM_STATE) -> dict:
    """IC 95% por bootstrap no teste (o teste tem poucas amostras da classe alta)."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y); proba = np.asarray(proba)
    acc = {k: [] for k in ("recall_alta", "precision_alta", "f1_alta", "roc_auc", "pr_auc")}
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        if y[idx].sum() in (0, len(idx)):
            continue
        m = metricas(y[idx], proba[idx], limiar)
        for k in acc:
            acc[k].append(m[k])
    return {f"{k}_ic95": (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5)))
            for k, v in acc.items()}


def plot_matrizes_confusao(resultados: dict, nome="confusion_matrices.png"):
    """resultados: {modelo: (y_true, y_pred)}"""
    n = len(resultados)
    fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 3.8))
    axes = np.atleast_1d(axes)
    for ax, (nome_m, (y, pred)) in zip(axes, resultados.items()):
        cm = confusion_matrix(y, pred, labels=[0, 1])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax,
                    xticklabels=["Baixa/média", "Alta"], yticklabels=["Baixa/média", "Alta"])
        ax.set_title(nome_m); ax.set_xlabel("Previsto"); ax.set_ylabel("Real")
    fig.suptitle("Matrizes de confusão no conjunto de teste", y=1.02)
    fig.tight_layout()
    _salvar(fig, nome)
    # cópia na raiz de results/ (estrutura pedida)
    fig.savefig(config.RESULTS_DIR / nome, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_curvas(probas: dict, y_test, nome="curvas_roc_pr.png"):
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
    for nome_m, p in probas.items():
        fpr, tpr, _ = roc_curve(y_test, p)
        ax[0].plot(fpr, tpr, label=f"{nome_m} (AUC={roc_auc_score(y_test, p):.3f})")
        pr, rc, _ = precision_recall_curve(y_test, p)
        ax[1].plot(rc, pr, label=f"{nome_m} (AP={average_precision_score(y_test, p):.3f})")
    ax[0].plot([0, 1], [0, 1], "k--", lw=.8)
    ax[0].set_xlabel("Taxa de falsos positivos"); ax[0].set_ylabel("Taxa de verdadeiros positivos")
    ax[0].set_title("Curva ROC (teste)"); ax[0].legend(fontsize=8)
    ax[1].axhline(float(np.mean(y_test)), color="k", ls="--", lw=.8, label="Linha de base (prevalência)")
    ax[1].set_xlabel("Recall (classe alta)"); ax[1].set_ylabel("Precision (classe alta)")
    ax[1].set_title("Curva Precision–Recall (teste)"); ax[1].legend(fontsize=8)
    fig.tight_layout()
    _salvar(fig, nome)
    plt.close(fig)
    return fig


def importancias(modelos: dict, X_test, y_test, X_train, y_train,
                 n_repeats=30, n_boot=200, seed=config.RANDOM_STATE) -> pd.DataFrame:
    """Três visões de importância (todas PREDITIVAS, nenhuma causal):

    - permutation importance no TESTE (queda de PR-AUC ao embaralhar a variável);
    - impurity importance (árvores);
    - coeficiente padronizado da Regressão Logística + estabilidade do sinal em bootstrap.
    """
    linhas = []
    for nome, est in modelos.items():
        pi = permutation_importance(est, X_test, y_test, scoring="average_precision",
                                    n_repeats=n_repeats, random_state=seed, n_jobs=1)
        clf = est.named_steps["clf"]
        for i, f in enumerate(X_test.columns):
            linha = {"modelo": nome, "variavel": f,
                     "perm_importance_media": pi.importances_mean[i],
                     "perm_importance_dp": pi.importances_std[i]}
            if hasattr(clf, "feature_importances_"):
                linha["impurity_importance"] = clf.feature_importances_[i]
            if hasattr(clf, "coef_"):
                linha["coef_padronizado"] = float(clf.coef_[0][i])
            linhas.append(linha)

    # estabilidade do sinal dos coeficientes (apenas modelos lineares)
    rng = np.random.default_rng(seed)
    for nome, est in modelos.items():
        if not hasattr(est.named_steps["clf"], "coef_"):
            continue
        sinais = []
        for _ in range(n_boot):
            idx = rng.integers(0, len(X_train), len(X_train))
            yb = y_train.iloc[idx]
            if yb.nunique() < 2:
                continue
            m = clone(est).fit(X_train.iloc[idx], yb)
            sinais.append(np.sign(m.named_steps["clf"].coef_[0]))
        sinais = np.array(sinais)
        estab = {f: float((sinais[:, i] == np.sign(est.named_steps["clf"].coef_[0][i])).mean())
                 for i, f in enumerate(X_test.columns)}
        for l in linhas:
            if l["modelo"] == nome:
                l["estabilidade_sinal_bootstrap"] = estab[l["variavel"]]
    return pd.DataFrame(linhas)


def plot_importancias(df_imp: pd.DataFrame, nome="feature_importance.png"):
    modelos = list(df_imp["modelo"].unique())
    fig, axes = plt.subplots(1, len(modelos), figsize=(5.2 * len(modelos), 4.6), sharex=False)
    axes = np.atleast_1d(axes)
    for ax, m in zip(axes, modelos):
        d = df_imp[df_imp["modelo"] == m].sort_values("perm_importance_media")
        ax.barh([NOMES_PT.get(v, v) for v in d["variavel"]], d["perm_importance_media"],
                xerr=d["perm_importance_dp"], color=COR_ALTA, ecolor="#555", capsize=2)
        ax.axvline(0, color="k", lw=.8)
        ax.set_title(m); ax.set_xlabel("Queda de PR-AUC ao embaralhar (teste)")
    fig.suptitle("Importância preditiva por permutação (não é efeito causal)", y=1.02)
    fig.tight_layout()
    _salvar(fig, nome)
    fig.savefig(config.RESULTS_DIR / nome, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig
