"""Gera results/RESULTADOS.md e preenche os templates em docs/templates/.

TODO número que aparece em README/slides/roteiro vem de results/*.csv|json.
Nada é digitado à mão: se a base ou o modelo mudarem, basta rodar de novo.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from . import config, eda
from .preprocessing import NOMES_PT, carregar_dados


def _f(x, n=3) -> str:
    return f"{x:.{n}f}".replace(".", ",")


def _pct(x, n=1) -> str:
    return f"{x * 100:.{n}f}".replace(".", ",") + "%"


def _md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    l = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        l.append("| " + " | ".join(str(v) for v in r.values) + " |")
    return "\n".join(l)


def _conclusao(row, cv, escolhido) -> str:
    m, d = "cv_pr_auc_media", "cv_pr_auc_dp"
    topo = cv.sort_values(m, ascending=False).iloc[0]
    if row["modelo"] == escolhido:
        return "**Modelo escolhido**"
    r = cv.set_index("modelo").loc[row["modelo"]]
    if r[m] >= topo[m] - topo[d]:
        return "Empate técnico com o melhor; não adotado (mais complexo)"
    return f"Inferior na CV (PR-AUC {_f(r[m], 2)} vs {_f(topo[m], 2)})"


def tabela_comparativa(metrics: pd.DataFrame, cv: pd.DataFrame, escolhido: str) -> pd.DataFrame:
    t = metrics.copy()
    out = pd.DataFrame({
        "Modelo": t["modelo"], "Pré-processamento": t["estrategia_preprocessamento"],
        "Decisão": t["decisao"], "Accuracy": t["accuracy"].map(_f),
        "Precision (alta)": t["precision_alta"].map(_f), "Recall (alta)": t["recall_alta"].map(_f),
        "F1 (alta)": t["f1_alta"].map(_f), "ROC-AUC": t["roc_auc"].map(_f), "PR-AUC": t["pr_auc"].map(_f),
        "PR-AUC CV (média ± dp)": [f"{_f(a)} ± {_f(b)}" for a, b in zip(t["cv_pr_auc_media"], t["cv_pr_auc_dp"])],
        "Conclusão": [_conclusao(r, cv, escolhido) for _, r in t.iterrows()],
    })
    return out


def tabela_cv(cv: pd.DataFrame) -> pd.DataFrame:
    o = pd.DataFrame({"Modelo": cv["modelo"]})
    for k, nome in (("roc_auc", "ROC-AUC"), ("pr_auc", "PR-AUC"), ("f1_alta", "F1 (alta)"),
                    ("recall_alta", "Recall (alta)"), ("precision_alta", "Precision (alta)")):
        o[nome] = [f"{_f(a)} ± {_f(b)}" for a, b in zip(cv[f"cv_{k}_media"], cv[f"cv_{k}_dp"])]
    return o


def tabela_sens(sens: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "Cenário": sens["cenario"], "Linhas": sens["n_total"],
        "Teste c/ cópia no treino": sens["teste_com_copia_no_treino"], "Modelo": sens["modelo"],
        "ROC-AUC teste": sens["teste_roc_auc"].map(_f), "PR-AUC teste": sens["teste_pr_auc"].map(_f),
        "F1 alta (teste)": sens["teste_f1_alta"].map(_f), "PR-AUC CV": sens["cv_pr_auc_media"].map(_f)})


def _tab_classes(classes: pd.DataFrame) -> pd.DataFrame:
    p = lambda v: "<0,001" if v < 0.001 else _f(v, 3)
    return pd.DataFrame({
        "Variável": [NOMES_PT.get(v, v) for v in classes.index],
        "Mediana baixa/média": [_f(x, 3) for x in classes["mediana_baixa_media"]],
        "Mediana alta": [_f(x, 3) for x in classes["mediana_alta"]],
        "Dif. (alta − baixa/média)": [_f(x, 3) for x in classes["dif_medianas"]],
        "Cliff's δ": [_f(x, 2) for x in classes["cliffs_delta"]],
        "p (Mann-Whitney)": [p(x) for x in classes["p_valor"]]})


def _linhas_variaveis(imp, classes, escolhido, k=5) -> str:
    d = imp[imp["modelo"] == escolhido].sort_values("perm_importance_media", ascending=False).head(k)
    L = []
    for _, r in d.iterrows():
        v = r["variavel"]; c = classes.loc[v]
        sentido = "maior" if c["cliffs_delta"] > 0 else "menor"
        s = (f"- **{NOMES_PT.get(v, v)}**: importância por permutação {_f(r['perm_importance_media'])} "
             f"(± {_f(r['perm_importance_dp'])}); a classe alta tem valor tipicamente {sentido} "
             f"(mediana {_f(c['mediana_alta'], 2)} vs {_f(c['mediana_baixa_media'], 2)} na baixa/média).")
        if "estabilidade_sinal_bootstrap" in r and pd.notna(r.get("estabilidade_sinal_bootstrap")):
            s += f" Sinal do coeficiente estável em {_pct(r['estabilidade_sinal_bootstrap'], 0)} dos bootstraps."
        L.append(s)
    return "\n".join(L)


def montar_contexto() -> dict:
    R = config.RESULTS_DIR
    info = json.loads((R / "run_info.json").read_text(encoding="utf-8"))
    metrics = pd.read_csv(R / "metrics.csv"); cv = pd.read_csv(R / "metrics_cv.csv")
    sens = pd.read_csv(R / "sensibilidade_duplicatas.csv")
    imp = pd.read_csv(R / "feature_importance.csv")
    ic = pd.read_csv(R / "metrics_test_bootstrap_ic95.csv")
    df = carregar_dados(config.DATA_DIR / info["base_usada"]) if (config.DATA_DIR / info["base_usada"]).exists() \
        else carregar_dados(config.resolve_data_path())
    classes = eda.tabela_classes(df)
    corr, com_alvo, _ = eda.correlacoes(df)
    por_nota, binaria, _ = eda.distribuicao_alvo(df)
    esc = info["modelo_escolhido"]

    n_alta = int((df["quality"] >= 7).sum()); n = len(df)
    m05 = metrics[(metrics.modelo == esc) & (metrics.decisao == "limiar 0,5")].iloc[0]
    mop = metrics[(metrics.modelo == esc) & (metrics.decisao != "limiar 0,5")].iloc[0]
    ic05 = ic[(ic.modelo == esc) & (ic.decisao == "limiar 0,5")].iloc[0]
    icop = ic[(ic.modelo == esc) & (ic.decisao != "limiar 0,5")].iloc[0]
    top_imp = imp[imp.modelo == esc].sort_values("perm_importance_media", ascending=False)
    _nm = lambda v: NOMES_PT.get(v, v) if NOMES_PT.get(v, v)[:2] in ("SO", "pH") else NOMES_PT.get(v, v).lower()
    top3 = [_nm(v) for v in top_imp["variavel"].head(3)]
    top_corr = com_alvo.head(3)
    _n3 = [_nm(v) for v in top_corr.index]
    corr_nomes = f"{_n3[0]}, {_n3[1]} e {_n3[2]}"
    corr_txt = ", ".join(f"{_nm(v)} (ρ={_f(r.spearman_quality, 2)})" for v, r in top_corr.iterrows())
    sp = sens.set_index(["cenario", "modelo"])
    c_com, c_sem = "com duplicatas (split aleatório)", "sem duplicatas"
    modelos_s = list(sens["modelo"].unique())
    d_cv = {m: sp.loc[(c_com, m), "cv_pr_auc_media"] - sp.loc[(c_sem, m), "cv_pr_auc_media"] for m in modelos_s}
    d_te = {m: sp.loc[(c_com, m), "teste_roc_auc"] - sp.loc[(c_sem, m), "teste_roc_auc"] for m in modelos_s}
    sg = lambda v: ("+" if v >= 0 else "−") + _f(abs(v), 3)
    pior = max(d_cv, key=d_cv.get)
    delta_txt = ("diferença (com − sem duplicatas) na **PR-AUC da validação cruzada**: " +
                 "; ".join(f"{m} {sg(v)}" for m, v in d_cv.items()) +
                 ". Na **ROC-AUC do teste** (uma única partição pequena): " +
                 "; ".join(f"{m} {sg(v)}" for m, v in d_te.items()) +
                 f". O maior ganho aparente com duplicatas está em **{pior}** ({sg(d_cv[pior])}); " +
                 "ganhos assim sugerem memorização de linhas repetidas, e não melhor generalização.")

    mt = metrics[metrics.decisao == "limiar 0,5"].sort_values("pr_auc", ascending=False).iloc[0]
    if mt["modelo"] != esc:
        nota_teste = (f"> **Atenção — teste × validação cruzada.** No teste, {mt['modelo']} teve PR-AUC {_f(mt['pr_auc'], 2)} "
                      f"contra {_f(m05.pr_auc, 2)} de {esc}. A escolha do modelo foi feita **antes** de olhar o teste, só com a validação "
                      f"cruzada (que usa muito mais exemplos da classe alta); o teste tem apenas {info['n_alta_teste']} positivos e seus "
                      f"intervalos de confiança são largos. Por isso a escolha **não foi alterada** pelo resultado do teste — trocar de "
                      f"modelo ao ver o teste seria selecionar com os dados de avaliação. Esta divergência é um ponto a declarar e a validar "
                      f"com mais dados.")
    else:
        nota_teste = ""
    descr = {"Regressão Logística": "um método estatístico clássico, simples e fácil de explicar",
             "Decision Tree": "um conjunto de regras do tipo “se… então”, fácil de ler",
             "Random Forest": "um conjunto de muitas árvores de decisão que “votam” juntas"}[esc]
    ensaio = not info["base_oficial"]
    aviso = ("> ⚠️ **RESULTADOS DE ENSAIO.** Esta execução usou `" + info["base_usada"] +
             "`, e **não** a base oficial `" + config.OFFICIAL_DATASET + "`. Os números abaixo validam o código "
             "mas **não** podem ser apresentados como resultados finais. Para a entrega: coloque "
             f"`data/{config.OFFICIAL_DATASET}` e rode `python -m src.run_all`.") if ensaio else ""

    return {
        "AVISO_BASE": aviso, "NOTA_TESTE": nota_teste, "DESCR_MODELO": descr, "BASE_USADA": info["base_usada"],
        "N_LINHAS": f"{n:,}".replace(",", "."), "N_COLUNAS": str(pd.read_csv(config.resolve_data_path(), nrows=0).shape[1]),
        "N_DUP": str(int(df.duplicated().sum())), "PCT_DUP": _pct(df.duplicated().mean()),
        "N_ALTA": str(n_alta), "N_BAIXA": f"{n - n_alta:,}".replace(",", "."), "PCT_ALTA": _pct(n_alta / n),
        "RAZAO": f"1 : {(n - n_alta) / n_alta:.1f}".replace(".", ","),
        "N_TREINO": f'{info["n_treino"]:,}'.replace(",", "."), "N_TESTE": f'{info["n_teste"]:,}'.replace(",", "."), "N_ALTA_TESTE": str(info["n_alta_teste"]),
        "MODELO": esc, "JUSTIF_MODELO": info["justificativa_modelo"],
        "TAB_COMPARATIVA": _md(tabela_comparativa(metrics, cv, esc)),
        "TAB_CV": _md(tabela_cv(cv)), "TAB_SENS": _md(tabela_sens(sens)),
        "RECALL_05": _f(m05.recall_alta, 2), "PREC_05": _f(m05.precision_alta, 2),
        "RECALL_05_PCT": _pct(m05.recall_alta, 0), "PREC_05_PCT": _pct(m05.precision_alta, 0), "F1_05": _f(m05.f1_alta, 2),
        "RECALL_OPT": _f(mop.recall_alta, 2), "PREC_OPT": _f(mop.precision_alta, 2), "F1_OPT": _f(mop.f1_alta, 2),
        "LIMIAR_OPT": _f(mop.limiar, 2), "ROC": _f(m05.roc_auc, 2), "PR": _f(m05.pr_auc, 2),
        "PR_BASE": _f(n_alta / n, 2),
        "IC_RECALL_05": ic05.recall_alta_ic95.replace(".", ","), "IC_F1_05": ic05.f1_alta_ic95.replace(".", ","),
        "IC_RECALL_OPT": icop.recall_alta_ic95.replace(".", ","), "IC_F1_OPT": icop.f1_alta_ic95.replace(".", ","),
        "ACC_05": _f(m05.accuracy, 2), "ACC_ALVO_TRIVIAL": _pct(1 - n_alta / n),
        "TOP3": f"{top3[0]}, {top3[1]} e {top3[2]}", "TOP1": top3[0], "CORR_TOP": corr_txt, "CORR_NOMES": corr_nomes,
        "LINHAS_VARIAVEIS": _linhas_variaveis(imp, classes, esc),
        "DELTA_TXT": delta_txt,
        "CV_PR_MED": _f(cv.set_index("modelo").loc[esc, "cv_pr_auc_media"], 2),
        "CV_PR_DP": _f(cv.set_index("modelo").loc[esc, "cv_pr_auc_dp"], 2),
        "CV_REC_MED": _f(cv.set_index("modelo").loc[esc, "cv_recall_alta_media"], 2),
        "CV_REC_DP": _f(cv.set_index("modelo").loc[esc, "cv_recall_alta_dp"], 2),
        "TAB_CLASSES": _md(_tab_classes(classes)),
        "MELHORES_PARAMS": json.dumps(json.loads((R / "best_params.json").read_text(encoding="utf-8")),
                                      ensure_ascii=False),
    }


def _preencher(texto: str, ctx: dict) -> str:
    def sub(m):
        k = m.group(1)
        if k not in ctx:
            raise KeyError(f"placeholder sem valor: {k}")
        return str(ctx[k])
    return re.sub(r"\{\{([A-Z0-9_]+)\}\}", sub, texto)


def gerar_tudo() -> None:
    ctx = montar_contexto()
    corpo = f"""# Resultados (gerado automaticamente por `src/report.py`)

{ctx['AVISO_BASE']}

Base: `{ctx['BASE_USADA']}` — {ctx['N_LINHAS']} linhas, {ctx['N_DUP']} duplicatas exatas ({ctx['PCT_DUP']}).
Classe alta: {ctx['N_ALTA']} ({ctx['PCT_ALTA']}); baixa/média: {ctx['N_BAIXA']}. Proporção {ctx['RAZAO']}.
Treino: {ctx['N_TREINO']} · Teste: {ctx['N_TESTE']} (classe alta no teste: {ctx['N_ALTA_TESTE']}).

## Modelo escolhido
**{ctx['MODELO']}** — {ctx['JUSTIF_MODELO']}.
Hiperparâmetros selecionados no treino: `{ctx['MELHORES_PARAMS']}`

## Tabela comparativa final (conjunto de teste + CV aninhada)
{ctx['TAB_COMPARATIVA']}

## Validação cruzada aninhada (5 folds externos, treino apenas): média ± desvio-padrão
{ctx['TAB_CV']}

## Análise de sensibilidade: com × sem duplicatas
{ctx['TAB_SENS']}

## Variáveis × classe (associação, não causalidade)
{ctx['TAB_CLASSES']}

## Variáveis mais relevantes para o modelo escolhido
{ctx['LINHAS_VARIAVEIS']}
"""
    (config.RESULTS_DIR / "RESULTADOS.md").write_text(corpo, encoding="utf-8")

    # templates -> saídas (slides primeiro: a fala deles alimenta o roteiro do vídeo)
    def render(nome, destino, extra=None):
        t = config.DOCS_DIR / "templates" / nome
        if t.exists():
            destino.write_text(_preencher(t.read_text(encoding="utf-8"), {**ctx, **(extra or {})}), encoding="utf-8")

    render("README.template.md", config.ROOT / "README.md")
    slides_md = config.DOCS_DIR / "apresentacao_slides.md"
    render("apresentacao_slides.template.md", slides_md)
    falas = {}
    if slides_md.exists():
        for blk in re.split(r"\n## Slide ", slides_md.read_text(encoding="utf-8"))[1:]:
            num = int(blk.split(" ", 1)[0])
            m = re.search(r'\*\*Fala:\*\*\s*"(.*?)"\n', blk, flags=re.S)
            if m:
                falas[f"FALA_{num}"] = m.group(1)
    palavras = sum(len(v.split()) for v in falas.values())
    mm = lambda w: f"{int(w // 1)}:{int(round((w % 1) * 60)):02d}"
    falas.update({"N_PALAVRAS": str(palavras), "MIN_RAPIDO": mm(palavras / 130), "MIN_CALMO": mm(palavras / 105)})
    render("roteiro_video.template.md", config.DOCS_DIR / "roteiro_video.md", falas)
    (config.RESULTS_DIR / "summary.json").write_text(
        json.dumps({k: v for k, v in ctx.items() if not k.startswith("TAB_")}, ensure_ascii=False, indent=2),
        encoding="utf-8")
