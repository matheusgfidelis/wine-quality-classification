"""Funções de análise exploratória. Cada função devolve tabelas e salva figuras
em results/figures/, para que gráfico, tabela e texto sejam rastreáveis."""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from . import config
from .preprocessing import NOMES_PT

COR_BAIXA, COR_ALTA = "#7f8c8d", "#8e1b3a"
sns.set_theme(style="whitegrid", font_scale=0.95)


def _salvar(fig, nome: str):
    config.ensure_dirs()
    caminho = config.FIG_DIR / nome
    fig.savefig(caminho, dpi=150, bbox_inches="tight")
    return caminho


def resumo_estrutural(df: pd.DataFrame) -> dict:
    return {
        "linhas": int(df.shape[0]),
        "colunas": int(df.shape[1]),
        "nulos_total": int(df.isna().sum().sum()),
        "duplicatas": int(df.duplicated().sum()),
        "pct_duplicatas": float(df.duplicated().mean()),
    }


def distribuicao_alvo(df: pd.DataFrame, cutoff: int = config.CUTOFF):
    """Contagem por nota original e por classe binária (+ figura)."""
    por_nota = df["quality"].value_counts().sort_index().rename("n").to_frame()
    por_nota["%"] = (por_nota["n"] / len(df) * 100).round(2)
    y = (df["quality"] >= cutoff).astype(int)
    binaria = y.map({0: "Baixa/média (<7)", 1: "Alta (≥7)"}).value_counts()
    binaria = binaria.rename("n").to_frame()
    binaria["%"] = (binaria["n"] / len(df) * 100).round(2)

    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    cores = [COR_ALTA if q >= cutoff else COR_BAIXA for q in por_nota.index]
    ax[0].bar(por_nota.index.astype(str), por_nota["n"], color=cores)
    for i, v in enumerate(por_nota["n"]):
        ax[0].text(i, v, str(v), ha="center", va="bottom", fontsize=9)
    ax[0].set_title("Vinhos por nota original (quality)")
    ax[0].set_xlabel("Nota (3 a 8)"); ax[0].set_ylabel("Nº de amostras")
    ordem = ["Baixa/média (<7)", "Alta (≥7)"]
    ax[1].bar(ordem, [binaria.loc[o, "n"] for o in ordem], color=[COR_BAIXA, COR_ALTA])
    for i, o in enumerate(ordem):
        ax[1].text(i, binaria.loc[o, "n"], f'{binaria.loc[o, "n"]} ({binaria.loc[o, "%"]:.1f}%)',
                   ha="center", va="bottom", fontsize=9)
    ax[1].set_title("Classe binária (corte quality ≥ 7)")
    ax[1].set_ylabel("Nº de amostras")
    fig.tight_layout()
    _salvar(fig, "01_distribuicao_alvo.png")
    return por_nota, binaria, fig


def tabela_classes(df: pd.DataFrame, cutoff: int = config.CUTOFF) -> pd.DataFrame:
    """Mediana por classe + teste de Mann-Whitney + tamanho de efeito (Cliff's delta).

    ASSOCIAÇÃO, não causalidade. p-valores sem correção (11 testes); trate-os
    como descritivos. Com Bonferroni o limiar seria 0,05/11.
    """
    X = df.drop(columns="quality")
    y = (df["quality"] >= cutoff).astype(int)
    linhas = []
    for c in X.columns:
        a, b = X.loc[y == 1, c], X.loc[y == 0, c]
        u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        delta = 2 * u / (len(a) * len(b)) - 1  # Cliff's delta
        linhas.append({
            "variavel": c, "mediana_baixa_media": b.median(), "mediana_alta": a.median(),
            "dif_medianas": a.median() - b.median(), "cliffs_delta": delta, "p_valor": p,
        })
    out = pd.DataFrame(linhas).set_index("variavel")
    return out.reindex(out["cliffs_delta"].abs().sort_values(ascending=False).index)


def boxplots_por_classe(df: pd.DataFrame, cutoff: int = config.CUTOFF):
    """Distribuição de cada variável por classe (substitui gráfico de linha da média)."""
    X = df.drop(columns="quality")
    y = (df["quality"] >= cutoff).map({False: "Baixa/média", True: "Alta"})
    cols = list(X.columns)
    n = len(cols); nc = 4; nl = int(np.ceil(n / nc))
    fig, axes = plt.subplots(nl, nc, figsize=(14, 3.0 * nl))
    for ax, c in zip(axes.ravel(), cols):
        sns.boxplot(x=y, y=X[c], order=["Baixa/média", "Alta"], hue=y, legend=False,
                    palette={"Baixa/média": COR_BAIXA, "Alta": COR_ALTA},
                    fliersize=2, linewidth=1, ax=ax)
        ax.set_title(NOMES_PT.get(c, c)); ax.set_xlabel(""); ax.set_ylabel("")
    for ax in axes.ravel()[n:]:
        ax.axis("off")
    fig.suptitle("Distribuição das variáveis físico-químicas por classe de qualidade", y=1.01)
    fig.tight_layout()
    _salvar(fig, "02_boxplots_por_classe.png")
    return fig


def histogramas(df: pd.DataFrame):
    X = df.drop(columns="quality")
    cols = list(X.columns); nc = 4; nl = int(np.ceil(len(cols) / nc))
    fig, axes = plt.subplots(nl, nc, figsize=(14, 2.8 * nl))
    for ax, c in zip(axes.ravel(), cols):
        sns.histplot(X[c], bins=30, color="#34495e", ax=ax)
        ax.set_title(f"{NOMES_PT.get(c, c)} (assim.={X[c].skew():.2f})")
        ax.set_xlabel(""); ax.set_ylabel("")
    for ax in axes.ravel()[len(cols):]:
        ax.axis("off")
    fig.suptitle("Distribuição das variáveis (assimetria = skewness)", y=1.01)
    fig.tight_layout()
    _salvar(fig, "03_histogramas.png")
    return fig


def outliers_iqr(df: pd.DataFrame) -> pd.DataFrame:
    """Outliers por IQR (1,5×). São candidatos, NÃO erros: em vinhos, valores
    altos de açúcar/cloretos são fisicamente plausíveis e não devem ser removidos
    sem evidência de erro de medição."""
    X = df.drop(columns="quality")
    q1, q3 = X.quantile(.25), X.quantile(.75)
    iqr = q3 - q1
    mask = (X < q1 - 1.5 * iqr) | (X > q3 + 1.5 * iqr)
    out = pd.DataFrame({"n_outliers": mask.sum(), "pct": (mask.mean() * 100).round(2),
                        "assimetria": X.skew().round(2)})
    return out.sort_values("pct", ascending=False)


def inconsistencias(df: pd.DataFrame) -> pd.DataFrame:
    """Verificações de consistência física/lógica."""
    X = df
    checks = {
        "valores negativos (qualquer feature)": int((X.drop(columns="quality") < 0).any(axis=1).sum()),
        "SO₂ livre > SO₂ total": int((X["free_sulfur_dioxide"] > X["total_sulfur_dioxide"]).sum()),
        "pH fora de [2,5; 4,5]": int(((X["ph"] < 2.5) | (X["ph"] > 4.5)).sum()),
        "teor alcoólico fora de [5; 17] %": int(((X["alcohol"] < 5) | (X["alcohol"] > 17)).sum()),
        "densidade fora de [0,98; 1,01]": int(((X["density"] < 0.98) | (X["density"] > 1.01)).sum()),
        "ácido cítrico = 0 (plausível, só informativo)": int((X["citric_acid"] == 0).sum()),
        "nota fora de 0–10": int(((X["quality"] < 0) | (X["quality"] > 10)).sum()),
    }
    return pd.Series(checks, name="n_linhas").to_frame()


def correlacoes(df: pd.DataFrame, cutoff: int = config.CUTOFF):
    """Matriz de Spearman entre features + correlação de cada feature com quality
    e com a classe alta. Correlação ≠ causalidade."""
    X = df.drop(columns="quality")
    corr = X.corr(method="spearman")
    y = (df["quality"] >= cutoff).astype(int)
    com_alvo = pd.DataFrame({
        "spearman_quality": X.apply(lambda s: stats.spearmanr(s, df["quality"])[0]),
        "pontobiserial_classe_alta": X.apply(lambda s: stats.pointbiserialr(y, s)[0]),
    }).sort_values("spearman_quality", key=np.abs, ascending=False)

    fig, ax = plt.subplots(1, 2, figsize=(15, 5.5), gridspec_kw={"width_ratios": [1.25, 1]})
    nomes = [NOMES_PT.get(c, c) for c in corr.columns]
    sns.heatmap(corr.set_axis(nomes, axis=0).set_axis(nomes, axis=1), annot=True, fmt=".2f",
                cmap="coolwarm", center=0, vmin=-1, vmax=1, cbar_kws={"label": "Spearman"}, ax=ax[0])
    ax[0].set_title("Correlação (Spearman) entre variáveis")
    ordem = com_alvo["spearman_quality"].sort_values()
    ax[1].barh([NOMES_PT.get(i, i) for i in ordem.index], ordem.values,
               color=[COR_ALTA if v > 0 else COR_BAIXA for v in ordem.values])
    ax[1].axvline(0, color="k", lw=.8)
    ax[1].set_title("Correlação de cada variável com quality (Spearman)")
    ax[1].set_xlabel("ρ de Spearman")
    fig.tight_layout()
    _salvar(fig, "04_correlacoes.png")
    return corr, com_alvo, fig


def pares_muito_correlacionados(corr: pd.DataFrame, limite: float = 0.6) -> pd.DataFrame:
    pares = []
    cols = corr.columns
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            if abs(corr.iloc[i, j]) >= limite:
                pares.append((cols[i], cols[j], corr.iloc[i, j]))
    return pd.DataFrame(pares, columns=["var_a", "var_b", "spearman"]).sort_values(
        "spearman", key=np.abs, ascending=False)


# Justificativas de domínio (enologia/química) para pares de variáveis.
# tipo: "mecânica" (definição/identidade), "química" (relação físico-química
# conhecida) ou "hipótese" (plausível, NÃO comprovada por estes dados).
_JUSTIFICATIVAS = {
    frozenset(("free_sulfur_dioxide", "total_sulfur_dioxide")): (
        "mecânica", "SO₂ total = SO₂ livre + ligado; a parte livre compõe o total."),
    frozenset(("fixed_acidity", "ph")): (
        "química", "O pH mede acidez: mais ácidos fixos → pH menor (relação inversa esperada)."),
    frozenset(("citric_acid", "ph")): (
        "química", "O ácido cítrico é um ácido; mais cítrico → pH menor."),
    frozenset(("fixed_acidity", "citric_acid")): (
        "mecânica", "O ácido cítrico é um dos ácidos que compõem a acidez fixa."),
    frozenset(("fixed_acidity", "density")): (
        "química", "Ácidos fixos dissolvidos (ex.: tartárico) aumentam a massa por volume → densidade maior."),
    frozenset(("alcohol", "density")): (
        "química", "O álcool é menos denso que a água: mais álcool → densidade menor."),
    frozenset(("residual_sugar", "density")): (
        "química", "Açúcar dissolvido aumenta a densidade do líquido."),
    frozenset(("volatile_acidity", "citric_acid")): (
        "hipótese", "Associação inversa; pode refletir processos de fermentação/conservação distintos. Não comprovado aqui."),
    frozenset(("chlorides", "sulphates")): (
        "hipótese", "Ambos são sais/minerais; podem variar juntos por origem da uva ou prática do produtor. Não comprovado aqui."),
}


def justificar_correlacoes(corr: pd.DataFrame, limite: float = 0.5) -> pd.DataFrame:
    """Lista cada par com |ρ| ≥ limite e a justificativa de domínio.

    Pares sem justificativa pré-definida são marcados explicitamente — não
    inventamos explicação: tratam-se como associação empírica a investigar.
    """
    linhas = []
    cols = list(corr.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r = corr.iloc[i, j]
            if abs(r) >= limite:
                tipo, txt = _JUSTIFICATIVAS.get(
                    frozenset((cols[i], cols[j])),
                    ("sem justificativa pré-definida", "Associação empírica; investigar antes de interpretar."))
                linhas.append({"var_a": NOMES_PT.get(cols[i], cols[i]), "var_b": NOMES_PT.get(cols[j], cols[j]),
                               "spearman": round(r, 2), "tipo": tipo, "justificativa": txt})
    return pd.DataFrame(linhas).sort_values("spearman", key=np.abs, ascending=False).reset_index(drop=True)
