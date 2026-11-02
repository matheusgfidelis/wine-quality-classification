"""Gera docs/apresentacao_executiva.pptx a partir de results/ (sem números digitados).

Requer: node + pptxgenjs (apenas para este passo opcional). Uso:  python tools/build_deck.py
Rode DEPOIS de `python -m src.run_all` (ou do notebook 03).
"""
import json, re, subprocess, sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import config, eda  # noqa: E402
from src.preprocessing import carregar_dados, NOMES_PT  # noqa: E402

R = config.RESULTS_DIR
info = json.loads((R / "run_info.json").read_text(encoding="utf-8"))
summ = json.loads((R / "summary.json").read_text(encoding="utf-8"))
metrics = pd.read_csv(R / "metrics.csv")
imp = pd.read_csv(R / "feature_importance.csv")
corrj = pd.read_csv(R / "correlacoes_justificadas.csv")
df = carregar_dados(config.DATA_DIR / info["base_usada"])
esc = info["modelo_escolhido"]

# --- figura dedicada: 3 variáveis com maior tamanho de efeito -------------------
tab = eda.tabela_classes(df)
top3 = list(tab.index[:3])
y = (df["quality"] >= config.CUTOFF).map({False: "Baixa/média", True: "Alta"})
fig, ax = plt.subplots(1, 3, figsize=(12, 4.2))
for a, c in zip(ax, top3):
    sns.boxplot(x=y, y=df[c], order=["Baixa/média", "Alta"], hue=y, legend=False,
                palette={"Baixa/média": "#7f8c8d", "Alta": "#8e1b3a"}, fliersize=2, linewidth=1.2, ax=a)
    a.set_title(NOMES_PT.get(c, c), fontsize=15, fontweight="bold"); a.set_xlabel(""); a.set_ylabel("")
    a.tick_params(labelsize=13)
fig.tight_layout(); fig.savefig(config.FIG_DIR / "06_top3_boxplots.png", dpi=160, bbox_inches="tight"); plt.close(fig)

# --- dados para o deck ------------------------------------------------------------
m05 = metrics[(metrics.decisao == "limiar 0,5")]
corr_q = eda.correlacoes(df)[1]["spearman_quality"].sort_values()
imp_e = imp[imp.modelo == esc].sort_values("perm_importance_media", ascending=False).head(6)
md = (ROOT / "docs" / "apresentacao_slides.md").read_text(encoding="utf-8")
notas = {}
for blk in re.split(r"\n## Slide ", md)[1:]:
    n = int(blk.split(" ", 1)[0])
    m = re.search(r'\*\*Fala:\*\*\s*"(.*?)"\n', blk, flags=re.S)
    notas[n] = m.group(1) if m else ""

n_alta = int((df.quality >= 7).sum()); n = len(df)
from PIL import Image
def _dim(p):
    w, h = Image.open(p).size
    return [w, h]
_cls = tab
direcoes = []
for v in imp_e.variavel.head(3):
    c = _cls.loc[v]
    direcoes.append(f"{NOMES_PT[v]}: {'maior' if c['cliffs_delta'] > 0 else 'menor'} nos bons vinhos (mediana {c['mediana_alta']:.3g} contra {c['mediana_baixa_media']:.3g})".replace(".", ","))
_pn = df["quality"].value_counts().sort_index()
dados = {
    "ensaio": not info["base_oficial"], "base": info["base_usada"],
    "n": n, "n_dup": int(df.duplicated().sum()),
    "pct_dup": float(df.duplicated().mean()), "n_alta": n_alta, "pct_alta": n_alta / n,
    "n_treino": info["n_treino"], "n_teste": info["n_teste"], "n_alta_teste": info["n_alta_teste"],
    "modelo": esc, "descr_modelo": summ["DESCR_MODELO"], "justif": info["justificativa_modelo"],
    "top3_nomes": [NOMES_PT[c] for c in top3],
    "modelos": [{"Regressão Logística": "Método estatístico clássico", "Decision Tree": "Regras “se… então”",
                 "Random Forest": "Conjunto de árvores"}.get(m, m) for m in m05["modelo"]], "recall": [round(v * 100) for v in m05["recall_alta"]],
    "precision": [round(v * 100) for v in m05["precision_alta"]],
    "recall_esc": round(float(m05[m05.modelo == esc].recall_alta.iloc[0]) * 100),
    "prec_esc": round(float(m05[m05.modelo == esc].precision_alta.iloc[0]) * 100),
    "corr_labels": [NOMES_PT[c] for c in corr_q.index], "corr_vals": [round(v, 2) for v in corr_q.values],
    "pares": corrj.head(2).to_dict("records"),
    "imp_labels": [NOMES_PT[v] for v in imp_e.variavel][::-1],
    "imp_vals": [round(v, 3) for v in imp_e.perm_importance_media][::-1],
    "notas": notas, "fig_dist": str(config.FIG_DIR / "01_distribuicao_alvo.png"),
    "fig_box": str(config.FIG_DIR / "06_top3_boxplots.png"),
    "nota_teste": summ.get("NOTA_TESTE", ""), "direcoes": direcoes, "nota_labels": [str(i) for i in _pn.index], "nota_vals": [int(v) for v in _pn.values],
    "dim_dist": _dim(config.FIG_DIR / "01_distribuicao_alvo.png"), "dim_box": _dim(config.FIG_DIR / "06_top3_boxplots.png"),
}
(ROOT / "tools" / "_deck_data.json").write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
out = ROOT / "docs" / "apresentacao_executiva.pptx"
subprocess.run(["node", str(ROOT / "tools" / "build_deck.js"), str(ROOT / "tools" / "_deck_data.json"), str(out)], check=True)
(ROOT / "tools" / "_deck_data.json").unlink()
print("gerado:", out)
