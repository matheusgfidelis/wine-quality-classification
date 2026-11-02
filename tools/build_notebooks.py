"""Gera os notebooks 01, 02 e 03 (nbformat). Rodar: python tools/build_notebooks.py"""
import nbformat as nbf
from pathlib import Path

NB = Path(__file__).resolve().parents[1] / "notebooks"
SETUP = '''import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")
ROOT = Path.cwd().resolve()
if ROOT.name == "notebooks":      # funciona rodando de notebooks/ ou da raiz do repositório
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

import numpy as np, pandas as pd, matplotlib.pyplot as plt
from IPython.display import display, Markdown
from src import config, eda
from src.preprocessing import carregar_dados, criar_alvo, NOMES_PT

pd.set_option("display.width", 200); pd.set_option("display.max_columns", 30)
CAMINHO = config.resolve_data_path()
print("BASE USADA:", CAMINHO.name, "" if config.is_official(CAMINHO) else
      f"  <-- ATENÇÃO: não é a base oficial ({config.OFFICIAL_DATASET}); execução de ENSAIO")
df = carregar_dados(CAMINHO)
config.ensure_dirs()'''


def nb(cells):
    n = nbf.v4.new_notebook()
    n.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    n.cells = [nbf.v4.new_markdown_cell(c[1]) if c[0] == "md" else nbf.v4.new_code_cell(c[1]) for c in cells]
    return n


# ------------------------------------------------------------------ 01 EDA
eda_cells = [
("md", """# 01 · Análise exploratória — qualidade de vinhos
Tech Challenge Fase 2. **Pergunta central:** o que distingue vinhos de alta qualidade (`quality ≥ 7`) dos demais?
Todas as figuras são salvas em `results/figures/`. Conclusões abaixo são geradas a partir dos dados.
> Correlação/associação **não** é causalidade. Aqui descrevemos o que *aparece junto*, não o que *causa*."""),
("code", SETUP),
("md", "## 1. Estrutura, tipos, nulos e duplicatas"),
("code", """resumo = eda.resumo_estrutural(df)
display(pd.Series(resumo, name="valor").to_frame())
display(df.dtypes.to_frame("tipo").T)
display(df.describe().T.round(3))"""),
("md", "## 2. Variável-alvo: nota original e classe binária (corte `quality ≥ 7`)"),
("code", """por_nota, binaria, fig = eda.distribuicao_alvo(df)
display(por_nota); display(binaria); plt.show()
n_alta = int((df.quality >= 7).sum())
display(Markdown(f"**Desbalanceamento:** {n_alta} vinhos de alta qualidade ({n_alta/len(df):.1%}). "
  f"Um classificador que sempre responde 'baixa/média' teria acurácia de {1-n_alta/len(df):.1%} — "
  "por isso a acurácia não é a métrica principal."))"""),
("md", """## 3. Distribuições das variáveis
Assimetria (*skewness*) alta indica cauda longa à direita — relevante para modelos lineares (ver notebook 02)."""),
("code", """eda.histogramas(df); plt.show()"""),
("md", """## 4. Variáveis × classe (substitui os gráficos de linha da média por nota)
**Por que mudar:** gráficos de linha ligam *médias* de variáveis em escalas muito diferentes (ex.: SO₂ em dezenas e cloretos em centésimos) e
sugerem uma tendência contínua que as poucas amostras das notas extremas (3 e 8) não sustentam. Boxplots por classe mostram mediana, dispersão e sobreposição."""),
("code", """eda.boxplots_por_classe(df); plt.show()
tab = eda.tabela_classes(df)
display(tab.round(3))"""),
("code", """top = tab.head(3)
txt = "; ".join(f"**{NOMES_PT.get(v, v)}** (mediana {r.mediana_alta:.3g} na alta vs {r.mediana_baixa_media:.3g} na baixa/média, Cliff's δ={r.cliffs_delta:.2f})" for v, r in top.iterrows())
display(Markdown("**Maiores diferenças entre classes (por tamanho de efeito):** " + txt +
  ".  \\n*Interpretação:* são **associações**. Mann-Whitney sem correção para 11 testes — leia os p-valores como descritivos."))"""),
("md", "## 5. Correlações"),
("code", """corr, com_alvo, fig = eda.correlacoes(df); plt.show()
display(com_alvo.round(3))
display(Markdown("**Pares de variáveis muito correlacionados (|ρ| ≥ 0,6)** — relevante para interpretar importâncias:"))
display(eda.pares_muito_correlacionados(corr).round(2))"""),
("md", """### Justificativa de cada correlação forte (exigência da especificação)
`tipo`: **mecânica** = identidade/definição; **química** = relação físico-química conhecida; **hipótese** = plausível, *não* comprovada pelos dados."""),
("code", """pd.set_option("display.max_colwidth", 120)
just = eda.justificar_correlacoes(corr, limite=0.5)
just.to_csv(config.RESULTS_DIR / "correlacoes_justificadas.csv", index=False)
display(just)"""),
("md", """## 6. Outliers e valores inconsistentes
Outliers por IQR são **candidatos**; em química de vinho valores altos de açúcar e cloretos são plausíveis. **Não removemos outliers**
(sem evidência de erro de medição), e usamos transformação e modelos robustos."""),
("code", """display(eda.outliers_iqr(df))
display(eda.inconsistencias(df))"""),
("md", "## 7. Síntese (gerada automaticamente)"),
("code", """top_c = com_alvo.head(3)
display(Markdown("**Fatos observados:** " +
  f"{len(df)} linhas, {resumo['nulos_total']} nulos, {resumo['duplicatas']} duplicatas exatas ({resumo['pct_duplicatas']:.1%}); " +
  "maiores associações com a nota: " + ", ".join(f"{NOMES_PT.get(v, v)} (ρ={r.spearman_quality:.2f})" for v, r in top_c.iterrows()) + ".  \\n" +
  "**Cautelas:** associação ≠ causalidade; variáveis correlacionadas entre si; classe alta é minoritária."))"""),
]

# ------------------------------------------------------------------ 02 PRÉ-PROC
pre_cells = [
("md", """# 02 · Pré-processamento, duplicatas e vazamento de dados
Decide, com evidência, o que entra no pipeline final. Princípio: **tudo que aprende dos dados** (padronização, Yeo-Johnson, medianas)
fica dentro de um `Pipeline` e é ajustado só no treino de cada dobra."""),
("code", SETUP + """
from sklearn.model_selection import RepeatedStratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PowerTransformer, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from scipy import stats
from src.preprocessing import (LogAssimetricas, FeaturesEnologicas, COLUNAS_ASSIMETRICAS,
                               contar_vazamento_duplicatas, remover_duplicatas)
RS = config.RANDOM_STATE
X, y = criar_alvo(df)"""),
("md", """## 1. Dados faltantes
O desafio pede tratar faltantes *se houver*. Verificamos e **não** criamos etapa de imputação desnecessária."""),
("code", """print("Valores faltantes:", int(df.isna().sum().sum()))"""),
("md", """## 2. Duplicatas e vazamento treino→teste
Linhas 100% idênticas podem cair uma no treino e outra no teste: o modelo seria avaliado em algo que já viu.
**Ressalva:** os valores são arredondados, então vinhos *diferentes* podem coincidir; não dá para provar que são erros. Por isso a decisão é acompanhada de análise de sensibilidade (notebook 03)."""),
("code", """n_dup = int(df.duplicated().sum())
print(f"Duplicatas exatas: {n_dup} ({n_dup/len(df):.1%})")
Xa, Xb, ya, yb = train_test_split(X, y, test_size=.2, stratify=y, random_state=RS)
v = contar_vazamento_duplicatas(Xa, Xb)
print(f"Split SEM remover duplicatas: {v} de {len(Xb)} linhas do teste ({v/len(Xb):.1%}) têm cópia exata no treino")
df_sd = remover_duplicatas(df)
Xs, ys = criar_alvo(df_sd)
Xa, Xb, ya, yb = train_test_split(Xs, ys, test_size=.2, stratify=ys, random_state=RS)
print(f"Split APÓS remover duplicatas: {contar_vazamento_duplicatas(Xa, Xb)} linhas de teste com cópia no treino")
X, y = Xs, ys   # a partir daqui, base sem duplicatas (decisão documentada no README)"""),
("md", """## 3. Assimetria e outliers
Mede quais variáveis têm cauda longa. Outliers **não** são removidos (podem ser reais)."""),
("code", """assim = X.skew().sort_values(ascending=False).round(2)
q1, q3 = X.quantile(.25), X.quantile(.75); iqr = q3 - q1
pct = (((X < q1 - 1.5*iqr) | (X > q3 + 1.5*iqr)).mean()*100).round(1)
display(pd.DataFrame({"assimetria": assim, "% outliers IQR": pct.reindex(assim.index)}))
colunas_skew = [c for c in assim.index if assim[c] > 1]
print("Colunas com assimetria > 1 nesta base:", colunas_skew)
print("COLUNAS_ASSIMETRICAS em src/preprocessing.py:", COLUNAS_ASSIMETRICAS)"""),
("md", """## 4. log(1+x) × Yeo-Johnson
Para valores pequenos (cloretos ≈ 0,08), `log(1+x) ≈ x` e quase não corrige a assimetria. *Nota:* aqui o ajuste é feito na base inteira **apenas para descrever**; no modelo, o ajuste ocorre dentro do Pipeline."""),
("code", """X_log = LogAssimetricas().fit(X).transform(X)
X_yj = pd.DataFrame(PowerTransformer().fit_transform(X), columns=X.columns)
cols = [c for c in COLUNAS_ASSIMETRICAS if c in X.columns]
display(pd.DataFrame({"original": X[cols].skew(), "log(1+x)": X_log[cols].skew(), "Yeo-Johnson": X_yj[cols].skew()}).round(2))"""),
("md", """## 5. Demonstração de vazamento no ajuste do scaler
Ajustar o padronizador em **todos** os dados (antes do split) usa informação do teste. O efeito costuma ser pequeno, mas o procedimento correto é gratuito."""),
("code", """Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.2, stratify=y, random_state=RS)
d = pd.DataFrame({"desvio_fit_tudo": X.std(), "desvio_fit_treino": Xtr.std()})
d["diferenca_%"] = ((d.desvio_fit_tudo/d.desvio_fit_treino-1)*100).round(2)
display(d.reindex(d["diferenca_%"].abs().sort_values(ascending=False).index).round(4).head(6))"""),
("md", """## 6. Qual pré-processamento para qual modelo? (CV 5×3 repetida, ROC-AUC, scaler **dentro** do Pipeline)
Diferenças de CV repetida não são independentes: p-valores abaixo são **otimistas**; interprete principalmente o `delta` e o `% de folds vencidos`."""),
("code", """cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=RS)
def lr(prep): return Pipeline(prep + [("clf", LogisticRegression(class_weight="balanced", max_iter=5000, random_state=RS))])
def rf(prep): return Pipeline(prep + [("clf", RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=RS, n_jobs=1))])
cenarios = {
 "LogReg": {
   "A. StandardScaler":           lr([("s", StandardScaler())]),
   "B. log(assim.)+StandardScaler": lr([("l", LogAssimetricas()), ("s", StandardScaler())]),
   "C. Yeo-Johnson":              lr([("p", PowerTransformer())]),
   "D. Yeo-Johnson + features novas": lr([("f", FeaturesEnologicas()), ("p", PowerTransformer())]),
 },
 "RandomForest": {
   "A. sem transformação":        rf([("pass", "passthrough")]),
   "C. Yeo-Johnson":              rf([("p", PowerTransformer())]),
   "D. features novas":           rf([("f", FeaturesEnologicas())]),
 }}
notas = {}
for m, cs in cenarios.items():
    for nome, pipe in cs.items():
        notas[(m, nome)] = cross_val_score(pipe, X, y, cv=cv, scoring="roc_auc")
linhas = []
for m, cs in cenarios.items():
    base = notas[(m, list(cs)[0])]
    for nome in cs:
        s = notas[(m, nome)]
        linhas.append({"modelo": m, "cenario": nome, "ROC-AUC": s.mean(), "dp": s.std(ddof=1),
                       "delta vs A": (s-base).mean(), "% folds melhores": (s > base).mean()*100,
                       "p (Wilcoxon, otimista)": stats.wilcoxon(s, base).pvalue if nome != list(cs)[0] and not np.allclose(s, base) else np.nan})
res = pd.DataFrame(linhas); display(res.round(4))
res.to_csv(config.RESULTS_DIR / "preprocessamento_ab.csv", index=False)"""),
("code", """import seaborn as sns
fig, ax = plt.subplots(figsize=(10, 4.2))
sns.barplot(data=res, x="cenario", y="ROC-AUC", hue="modelo", ax=ax)
ax.set_ylim(res["ROC-AUC"].min()-0.02, res["ROC-AUC"].max()+0.015)
ax.set_title("ROC-AUC (CV repetida) por pré-processamento e modelo"); plt.xticks(rotation=15, ha="right")
fig.tight_layout(); fig.savefig(config.FIG_DIR / "05_ab_preprocessamento.png", dpi=150); plt.show()"""),
("md", "## 7. Decisões (geradas dos números acima)"),
("code", """g = lambda m, c: res[(res.modelo==m)&(res.cenario==c)].iloc[0]
d_lr_yj = g("LogReg","C. Yeo-Johnson")["delta vs A"]; d_lr_fe = g("LogReg","D. Yeo-Johnson + features novas")["delta vs A"] - d_lr_yj
d_rf_yj = g("RandomForest","C. Yeo-Johnson")["delta vs A"]; d_rf_fe = g("RandomForest","D. features novas")["delta vs A"]
LIM = 0.002   # diferença mínima de ROC-AUC para considerar relevante
esc_yj = "Adotar (somente perfil linear)" if d_lr_yj > LIM else "Efeito desprezível nesta base: manter só no perfil linear (padroniza; não prejudica)"
esc_fe_l = "Não adotar: ganho marginal e redundância com variáveis existentes" if d_lr_fe <= LIM else "Ganho relevante: avaliar adoção (reportar no README)"
esc_fe_r = "Não adotar" if d_rf_fe <= LIM else "Ganho relevante: avaliar adoção (reportar no README)"
display(Markdown(f'''| Decisão | Evidência nesta base | Escolha |
|---|---|---|
| Yeo-Johnson para modelos lineares | Δ ROC-AUC vs StandardScaler = {d_lr_yj:+.4f} | {esc_yj} |
| Yeo-Johnson para árvores | Δ vs sem transformação = {d_rf_yj:+.4f} | Não aplicar (árvores usam limiares: transformação monotônica não muda os cortes) |
| Features enológicas (linear) | ganho adicional sobre Yeo-Johnson = {d_lr_fe:+.4f} | {esc_fe_l} |
| Features enológicas (Random Forest) | Δ vs sem transformação = {d_rf_fe:+.4f} | {esc_fe_r} |
| Duplicatas | ver bloco 2 e sensibilidade no notebook 03 | Remover antes do split e reportar os dois cenários |
| Faltantes / outliers | 0 faltantes; outliers plausíveis | Nada a imputar; outliers mantidos |'''))"""),
]

# ------------------------------------------------------------------ 03 MODELAGEM
mod_cells = [
("md", """# 03 · Modelagem, avaliação e interpretação
Fluxo (tudo em `src/train.py`, `random_state=42`): split 80/20 estratificado → **CV aninhada** no treino → `GridSearchCV` otimizando **PR-AUC** →
limiar 0,5 *e* limiar F1-ótimo (via *out-of-fold* do treino) → avaliação única no teste + IC bootstrap.
O teste **não** participa de nenhuma escolha."""),
("code", SETUP + """
from src import train, report, evaluate
RS = config.RANDOM_STATE"""),
("md", "## 1. Treino e comparação (≈ 2 min)"),
("code", """r = train.executar(df, remover_dup=config.REMOVE_DUPLICATES)"""),
("md", "## 2. Validação cruzada aninhada — média ± desvio-padrão entre folds"),
("code", """display(report.tabela_cv(r["cv"]))
print("Hiperparâmetros escolhidos:", r["params"])"""),
("md", "## 3. Teste — todas as métricas da classe alta"),
("code", """cols = ["modelo","decisao","accuracy","precision_alta","recall_alta","f1_alta","roc_auc","pr_auc"]
display(r["teste"][cols].round(3))
ic = pd.DataFrame([{"modelo": n, "decisao": d, **{k: f"[{a:.2f}; {b:.2f}]" for k,(a,b) in v.items()}} for (n,d),v in r["ics"].items()])
display(Markdown("**IC 95% por bootstrap no teste** (largos: poucos positivos no teste)")); display(ic)"""),
("md", "## 4. Matrizes de confusão e curvas"),
("code", """from IPython.display import Image
display(Image(str(config.RESULTS_DIR / "confusion_matrices.png")))
display(Image(str(config.FIG_DIR / "curvas_roc_pr.png")))"""),
("md", "## 5. Escolha do modelo (regra do 1 desvio-padrão, só com a CV)"),
("code", """display(Markdown(f"**Modelo escolhido: {r['melhor_modelo']}** — {r['justificativa_modelo']}."))"""),
("md", """## 6. Variáveis mais influentes
Três visões **preditivas** (nenhuma é causal): permutação no teste, importância por impureza (árvores) e coeficiente padronizado (linear), com estabilidade do sinal em 200 bootstraps."""),
("code", """imp = r["importancias"]
display(imp[imp.modelo==r["melhor_modelo"]].sort_values("perm_importance_media", ascending=False).round(4))
display(Image(str(config.RESULTS_DIR / "feature_importance.png")))"""),
("md", "## 7. Sensibilidade a duplicatas (≈ 3-4 min)"),
("code", """sens = train.sensibilidade_duplicatas(df, verbose=False)
display(report.tabela_sens(sens))"""),
("md", "## 8. Salvar resultados e regenerar README/slides/roteiro"),
("code", """train.salvar_resultados(r, sens, eda.resumo_estrutural(df), CAMINHO)
report.gerar_tudo()
print("Arquivos em:", config.RESULTS_DIR)"""),
]

for nome, cells in (("01_eda.ipynb", eda_cells), ("02_preprocessamento.ipynb", pre_cells), ("03_modelagem.ipynb", mod_cells)):
    nbf.write(nb(cells), NB / nome)
    print("escrito", nome)
