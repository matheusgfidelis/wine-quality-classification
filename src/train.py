"""Treino e comparação de modelos — Wine Quality (reprodutível, sem vazamento).

Fluxo (tudo com random_state fixo):
 1. carrega a base, cria o alvo binário (quality >= 7);
 2. [opcional, padrão] remove duplicatas exatas ANTES do split;
 3. split estratificado 80/20 — o TESTE só é usado no fim, para relatar;
 4. por modelo: validação cruzada ANINHADA no treino (estimativa honesta do
    desempenho + estabilidade entre folds) e GridSearchCV no treino inteiro,
    otimizando PR-AUC (average_precision) — não acurácia;
 5. limiar de decisão: padrão 0,5 e um limiar que maximiza F1 escolhido SÓ com
    probabilidades out-of-fold do treino;
 6. avaliação final no teste + IC bootstrap; importâncias; figuras e CSVs.
"""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (GridSearchCV, StratifiedKFold, cross_val_predict,
                                     cross_validate, train_test_split)
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from . import config, evaluate
from .preprocessing import (carregar_dados, construir_preprocessador, contar_vazamento_duplicatas,
                            criar_alvo, remover_duplicatas)

RS = config.RANDOM_STATE
SCORING = {"roc_auc": "roc_auc", "pr_auc": "average_precision",
           "f1_alta": "f1", "recall_alta": "recall", "precision_alta": "precision"}
SELECAO = "pr_auc"  # métrica de seleção de hiperparâmetros e de modelo (ver README)

# Ordem de simplicidade/interpretabilidade, usada na regra do 1 desvio-padrão
COMPLEXIDADE = {"Regressão Logística": 1, "Decision Tree": 2, "Random Forest": 3}

ESTRATEGIA = {
    "Regressão Logística": "Yeo-Johnson + padronização (dentro do Pipeline); class_weight=balanced",
    "Decision Tree": "sem transformação; class_weight=balanced",
    "Random Forest": "sem transformação; class_weight=balanced",
}


def definir_modelos() -> dict:
    """{nome: (pipeline, grade de hiperparâmetros)}"""
    return {
        "Regressão Logística": (
            Pipeline([("prep", construir_preprocessador("linear")),
                      ("clf", LogisticRegression(class_weight="balanced", max_iter=5000,
                                                 random_state=RS))]),
            {"clf__C": [0.01, 0.1, 1, 10]}),
        "Decision Tree": (
            Pipeline([("prep", construir_preprocessador("arvore")),
                      ("clf", DecisionTreeClassifier(class_weight="balanced", random_state=RS))]),
            {"clf__max_depth": [3, 4, 5, 6], "clf__min_samples_leaf": [5, 10, 20, 40]}),
        "Random Forest": (
            Pipeline([("prep", construir_preprocessador("arvore")),
                      ("clf", RandomForestClassifier(n_estimators=200, class_weight="balanced",
                                                     random_state=RS, n_jobs=1))]),
            {"clf__max_depth": [3, 5, 8, None], "clf__min_samples_leaf": [1, 3, 5]}),
    }


def escolher_modelo(cv_df: pd.DataFrame) -> tuple[str, str]:
    """Regra do 1 desvio-padrão sobre a PR-AUC da CV aninhada (NUNCA usa o teste).

    1. acha o modelo de maior média;
    2. mantém todos cuja média esteja dentro de 1 desvio-padrão do melhor;
    3. entre eles, escolhe o mais simples/interpretável.
    Devolve (modelo, justificativa).
    """
    c = lambda x: f"{x:.3f}".replace(".", ",")
    m, d = f"cv_{SELECAO}_media", f"cv_{SELECAO}_dp"
    topo = cv_df.sort_values(m, ascending=False).iloc[0]
    candidatos = cv_df[cv_df[m] >= topo[m] - topo[d]]
    escolhido = candidatos.sort_values("modelo", key=lambda s: s.map(COMPLEXIDADE)).iloc[0]["modelo"]
    if escolhido == topo["modelo"]:
        just = f"maior PR-AUC média na CV aninhada ({c(topo[m])} ± {c(topo[d])})"
    else:
        e = cv_df.set_index("modelo").loc[escolhido]
        just = (f"empate técnico: {escolhido} ({c(e[m])} ± {c(e[d])}) está dentro de 1 desvio-padrão "
                f"de {topo['modelo']} ({c(topo[m])} ± {c(topo[d])}); adotado por ser mais simples e interpretável")
    return escolhido, just


def preparar(df: pd.DataFrame, remover_dup: bool, verbose=True):
    if remover_dup:
        df = remover_duplicatas(df, verbose=verbose)
    X, y = criar_alvo(df)
    return train_test_split(X, y, test_size=config.TEST_SIZE, stratify=y, random_state=RS)


def executar(df: pd.DataFrame, remover_dup: bool = True, verbose: bool = True,
             salvar_figuras: bool = True) -> dict:
    warnings.filterwarnings("ignore")
    X_tr, X_te, y_tr, y_te = preparar(df, remover_dup, verbose)
    vazados = contar_vazamento_duplicatas(X_tr, X_te)
    if verbose:
        print(f"Treino: {len(X_tr)} | Teste: {len(X_te)} | classe alta no teste: {int(y_te.sum())}")
        print(f"Linhas do teste com cópia exata no treino: {vazados} ({vazados/len(X_te):.1%})")

    interno = StratifiedKFold(3, shuffle=True, random_state=RS)
    externo = StratifiedKFold(5, shuffle=True, random_state=RS)
    oof_cv = StratifiedKFold(5, shuffle=True, random_state=RS)

    linhas_teste, linhas_cv, estimadores, probas, params, ics = [], [], {}, {}, {}, {}
    for nome, (pipe, grade) in definir_modelos().items():
        if verbose:
            print(f"-> {nome}")
        busca = GridSearchCV(pipe, grade, scoring=SCORING, refit=SELECAO, cv=interno, n_jobs=1)
        # CV aninhada: a seleção de hiperparâmetros acontece DENTRO de cada fold externo
        aninhada = cross_validate(clone(busca), X_tr, y_tr, cv=externo, scoring=SCORING, n_jobs=1)
        cv_row = {"modelo": nome}
        for k in SCORING:
            v = aninhada[f"test_{k}"]
            cv_row[f"cv_{k}_media"] = v.mean(); cv_row[f"cv_{k}_dp"] = v.std(ddof=1)
        linhas_cv.append(cv_row)

        busca.fit(X_tr, y_tr)
        est = busca.best_estimator_
        estimadores[nome] = est
        params[nome] = {k.replace("clf__", ""): v for k, v in busca.best_params_.items()}

        oof = cross_val_predict(clone(est), X_tr, y_tr, cv=oof_cv, method="predict_proba")[:, 1]
        thr_opt = evaluate.melhor_limiar_f1(y_tr, oof)
        p_te = est.predict_proba(X_te)[:, 1]
        probas[nome] = p_te
        for estrategia, thr in (("limiar 0,5", 0.5), ("limiar ótimo F1 (OOF treino)", thr_opt)):
            m = evaluate.metricas(y_te, p_te, thr)
            linhas_teste.append({"modelo": nome, "estrategia_preprocessamento": ESTRATEGIA[nome],
                                 "decisao": estrategia, **m})
            ics[(nome, estrategia)] = evaluate.bootstrap_ic(y_te, p_te, thr)

    cv_df = pd.DataFrame(linhas_cv)
    teste_df = pd.DataFrame(linhas_teste)
    metrics = teste_df.merge(cv_df, on="modelo")

    resultado = {"X_tr": X_tr, "X_te": X_te, "y_tr": y_tr, "y_te": y_te, "vazados": vazados,
                 "cv": cv_df, "teste": teste_df, "metrics": metrics, "estimadores": estimadores,
                 "probas": probas, "params": params, "ics": ics,
                 }
    resultado["melhor_modelo"], resultado["justificativa_modelo"] = escolher_modelo(cv_df)

    if salvar_figuras:
        res_cm = {n: (y_te, (probas[n] >= 0.5).astype(int)) for n in estimadores}
        evaluate.plot_matrizes_confusao(res_cm)
        evaluate.plot_curvas(probas, y_te)
        imp = evaluate.importancias(estimadores, X_te, y_te, X_tr, y_tr)
        evaluate.plot_importancias(imp)
        resultado["importancias"] = imp
    return resultado


def sensibilidade_duplicatas(df: pd.DataFrame, verbose=True) -> pd.DataFrame:
    """Roda o fluxo completo COM e SEM duplicatas e compara."""
    linhas = []
    for rotulo, rem in (("com duplicatas (split aleatório)", False), ("sem duplicatas", True)):
        if verbose:
            print(f"\n=== Cenário: {rotulo} ===")
        r = executar(df, remover_dup=rem, verbose=verbose, salvar_figuras=False)
        t = r["teste"].query("decisao == 'limiar 0,5'")
        for _, row in t.iterrows():
            cvr = r["cv"].set_index("modelo").loc[row["modelo"]]
            linhas.append({"cenario": rotulo, "n_total": len(r["X_tr"]) + len(r["X_te"]),
                           "teste_com_copia_no_treino": r["vazados"], "modelo": row["modelo"],
                           "teste_roc_auc": row["roc_auc"], "teste_pr_auc": row["pr_auc"],
                           "teste_f1_alta": row["f1_alta"], "teste_recall_alta": row["recall_alta"],
                           "cv_pr_auc_media": cvr["cv_pr_auc_media"]})
    return pd.DataFrame(linhas)


def salvar_resultados(r: dict, sens: pd.DataFrame, df_resumo: dict, caminho_dados) -> None:
    config.ensure_dirs()
    R = config.RESULTS_DIR
    r["metrics"].to_csv(R / "metrics.csv", index=False)
    r["cv"].to_csv(R / "metrics_cv.csv", index=False)
    sens.to_csv(R / "sensibilidade_duplicatas.csv", index=False)
    if "importancias" in r:
        r["importancias"].to_csv(R / "feature_importance.csv", index=False)
    ic_rows = [{"modelo": n, "decisao": d, **{k: f"[{v[0]:.3f}; {v[1]:.3f}]" for k, v in ic.items()}}
               for (n, d), ic in r["ics"].items()]
    pd.DataFrame(ic_rows).to_csv(R / "metrics_test_bootstrap_ic95.csv", index=False)
    (R / "best_params.json").write_text(json.dumps(r["params"], indent=2, default=str), encoding="utf-8")
    info = {"base_usada": caminho_dados.name, "base_oficial": config.is_official(caminho_dados),
            "random_state": RS, "remover_duplicatas": True, "metrica_selecao": SELECAO,
            "modelo_escolhido": r["melhor_modelo"],
            "justificativa_modelo": r["justificativa_modelo"], **df_resumo,
            "n_treino": int(len(r["X_tr"])), "n_teste": int(len(r["X_te"])),
            "n_alta_teste": int(r["y_te"].sum()), "n_alta_treino": int(r["y_tr"].sum())}
    (R / "run_info.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
