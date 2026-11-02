# Classificação da qualidade de vinhos com Machine Learning

**Tech Challenge — Fase 2 · POSTECH · Data Analytics**



> **Como ler este documento.** Cada seção separa **Fatos** (medidos nos dados), **Decisões**
> (escolhas metodológicas justificadas), **Interpretações** (leitura dos fatos, com cautela) e
> **Limitações/Recomendações**. Todos os números desta página são gerados por `src/report.py`
> a partir de `results/` — nenhum foi digitado à mão.

---

## 1. Contexto e problema de negócio

A avaliação sensorial de vinhos (feita por provadores) é cara, demorada e subjetiva. Já as medidas
físico-químicas (acidez, álcool, sulfatos, dióxido de enxofre etc.) são obtidas rotineiramente em
laboratório. **Pergunta:** é possível, apenas com essas medidas, sinalizar quais vinhos têm maior
chance de serem avaliados como de **alta qualidade**?

**Uso pretendido:** apoio à decisão de produtores e enólogos — por exemplo, priorizar quais lotes
merecem análise sensorial ou revisão do processo. **O modelo não substitui o especialista nem a
degustação**: ele estima uma probabilidade a partir de medidas químicas, e a nota original é, ela
própria, uma opinião humana.

## 2. Objetivo

Construir e comparar modelos de classificação binária que estimem se um vinho será de **alta
qualidade** (`quality ≥ 7`) ou de **baixa/média qualidade** (`quality < 7`), de forma reprodutível e
sem vazamento de dados, e traduzir os resultados em implicações para o processo produtivo.

**Variável-alvo (decisão):** `alta_qualidade = 1` se `quality ≥ 7`, senão `0`. O corte em 7 é o
definido pela especificação do desafio e separa os vinhos "de destaque" dos demais. *O que se perde:*
a binarização descarta a gradação entre notas (um 3 e um 6 viram a mesma classe).

## 3. Dados

| Item | Valor |
|---|---|
| Base usada nesta execução | `WineQT.csv` |
| Base oficial do projeto (decisão) | `WineQT.csv` |
| Linhas × colunas (arquivo) | 1.143 × 13 |
| Duplicatas exatas (todas as colunas) | 125 (10,9%) |
| Classe alta / baixa-média | 159 (13,9%) / 984 — proporção 1 : 6,2 |
| Treino / teste (80/20 estratificado, `random_state=42`) | 814 / 204 (classe alta no teste: 27) |

**Fonte.** Dados físico-químicos de vinho tinto *vinho verde* português (Cortez et al., 2009; UCI
*Wine Quality*). O `WineQT.csv` é a versão distribuída no Kaggle (`yasserh/wine-quality-dataset`) com
uma coluna `Id`; o `winequality-red.csv` é a versão original da UCI.

**Verificação (`python -m src.compare_datasets` → `results/comparacao_bases.md`):** todas as linhas da
`WineQT.csv` existem na `winequality-red.csv` — a WineQT é um **subconjunto** da base de vinho tinto, com
`Id`. A WineQT tem 125 duplicatas exatas; a red, 240.

**Decisão sobre a base.** Usamos **uma única base** — a `WineQT.csv` — em EDA, modelagem, apresentação
e vídeo. A `winequality-red.csv` aparece apenas como material de apoio do Tópico 2 e **não** é misturada
nos resultados finais: as duas diferem em nº de linhas e duplicatas, então métricas de uma não são
comparáveis às da outra. Para verificar a relação entre as bases: `python -m src.compare_datasets`.

### Dicionário de variáveis

| Variável | Descrição | Unidade |
|---|---|---|
| `fixed_acidity` | Acidez fixa (ácidos não voláteis, ex.: tartárico) | g/dm³ |
| `volatile_acidity` | Acidez volátil (principalmente ácido acético; em excesso, gosto de vinagre) | g/dm³ |
| `citric_acid` | Ácido cítrico | g/dm³ |
| `residual_sugar` | Açúcar residual após a fermentação | g/dm³ |
| `chlorides` | Cloretos (sal) | g/dm³ |
| `free_sulfur_dioxide` | SO₂ livre (conservante ativo) | mg/dm³ |
| `total_sulfur_dioxide` | SO₂ total (livre + ligado) | mg/dm³ |
| `density` | Densidade | g/cm³ |
| `ph` | pH | — |
| `sulphates` | Sulfatos | g/dm³ |
| `alcohol` | Teor alcoólico | % vol. |
| `quality` | Nota sensorial (mediana de avaliações de provadores), 3–8 neste conjunto | pontos |
| `Id` | Identificador de linha (**excluído** dos preditores) | — |

## 4. Metodologia

**Decisões metodológicas (e por quê)**

| Etapa | Decisão | Justificativa |
|---|---|---|
| Dados faltantes | Verificados; nenhuma imputação | Não há valores nulos. `dropna` do notebook original era inócuo e foi removido do fluxo final |
| Duplicatas | Remover linhas 100% idênticas **antes** do split (+ análise de sensibilidade, §6) | Cópias entre treino e teste inflam as métricas; valores são arredondados, então coincidências legítimas são possíveis — por isso reportamos os dois cenários |
| Escala | `PowerTransformer` (Yeo-Johnson) **somente** para Regressão Logística, dentro do `Pipeline` | Modelos lineares se beneficiam de variáveis simétricas e padronizadas; árvores dividem por limiar e dispensam escala |
| Feature engineering | Features enológicas testadas no notebook 02, **não** adotadas no modelo final | Ganho desprezível/negativo e duplicam informação, prejudicando a interpretação |
| Desbalanceamento | `class_weight="balanced"` | Simples, sem criar dados sintéticos |
| Validação | CV estratificada **aninhada** (5 folds externos × 3 internos) apenas no treino | Hiperparâmetros nunca são escolhidos olhando o teste |
| Métrica de seleção | **PR-AUC** (average precision) | Acurácia engana com 13,9% de classe alta: prever sempre "baixa/média" já daria 86,1% de acurácia |
| Escolha do modelo | Regra do 1 desvio-padrão sobre a PR-AUC da CV | Entre modelos tecnicamente empatados, prefere-se o mais simples |
| Limiar de decisão | 0,5 **e** limiar que maximiza F1 escolhido só com probabilidades *out-of-fold* do treino | O padrão 0,5 não é ótimo para classe rara |

**Modelos comparados:** Regressão Logística (interpretável, linear), Decision Tree (regras legíveis) e
Random Forest (não linear, mais robusto). Hiperparâmetros testados por `GridSearchCV` (grades em
`src/train.py`); selecionados: `{"Regressão Logística": {"C": 0.1}, "Decision Tree": {"max_depth": 5, "min_samples_leaf": 20}, "Random Forest": {"max_depth": null, "min_samples_leaf": 5}}`.

## 5. Análise exploratória (EDA)

Notebook: `notebooks/01_eda.ipynb`. Figuras em `results/figures/`.

**Fatos**
- Distribuição de `quality` e classe binária: `results/figures/01_distribuicao_alvo.png`.
- Variáveis mais associadas à nota (Spearman com `quality`): álcool (ρ=0,50), acidez volátil (ρ=-0,40), sulfatos (ρ=0,39).
- Diferença entre classes (mediana, Mann-Whitney, Cliff's δ):

| Variável | Mediana baixa/média | Mediana alta | Dif. (alta − baixa/média) | Cliff's δ | p (Mann-Whitney) |
|---|---|---|---|---|---|
| Álcool | 10,000 | 11,600 | 1,600 | 0,64 | <0,001 |
| Acidez volátil | 0,550 | 0,360 | -0,190 | -0,54 | <0,001 |
| Sulfatos | 0,600 | 0,740 | 0,140 | 0,49 | <0,001 |
| Ácido cítrico | 0,240 | 0,410 | 0,170 | 0,41 | <0,001 |
| Cloretos | 0,080 | 0,073 | -0,007 | -0,29 | <0,001 |
| Densidade | 0,997 | 0,996 | -0,001 | -0,26 | <0,001 |
| SO₂ total | 39,000 | 28,000 | -11,000 | -0,24 | <0,001 |
| Acidez fixa | 7,800 | 8,700 | 0,900 | 0,20 | <0,001 |
| pH | 3,315 | 3,270 | -0,045 | -0,13 | 0,006 |
| SO₂ livre | 14,000 | 12,000 | -2,000 | -0,11 | 0,029 |
| Açúcar residual | 2,200 | 2,300 | 0,100 | 0,10 | 0,041 |

- Outliers por IQR e verificações de consistência física estão no notebook 01 (outliers são
  **candidatos**, não erros: açúcar e cloretos têm cauda direita natural em vinhos).

**Interpretação (cautelosa).** As diferenças acima descrevem **associação**. Álcool, acidez volátil e
sulfatos separam melhor as classes, mas isso **não prova** que alterar essas variáveis causa mudança na
nota. O notebook original de EDA usava gráficos de linha da *média* por nota; eles foram substituídos
por boxplots por classe (`02_boxplots_por_classe.png`), que mostram dispersão e sobreposição.

## 6. Resultados

*(Gerado automaticamente — também em `results/RESULTADOS.md` e `results/metrics.csv`.)*

### 6.1 Comparação final — conjunto de teste (classe alta = rótulo 1)

| Modelo | Pré-processamento | Decisão | Accuracy | Precision (alta) | Recall (alta) | F1 (alta) | ROC-AUC | PR-AUC | PR-AUC CV (média ± dp) | Conclusão |
|---|---|---|---|---|---|---|---|---|---|---|
| Regressão Logística | Yeo-Johnson + padronização (dentro do Pipeline); class_weight=balanced | limiar 0,5 | 0,804 | 0,386 | 0,815 | 0,524 | 0,897 | 0,493 | 0,570 ± 0,119 | **Modelo escolhido** |
| Regressão Logística | Yeo-Johnson + padronização (dentro do Pipeline); class_weight=balanced | limiar ótimo F1 (OOF treino) | 0,863 | 0,486 | 0,630 | 0,548 | 0,897 | 0,493 | 0,570 ± 0,119 | **Modelo escolhido** |
| Decision Tree | sem transformação; class_weight=balanced | limiar 0,5 | 0,809 | 0,389 | 0,778 | 0,519 | 0,860 | 0,492 | 0,428 ± 0,144 | Inferior na CV (PR-AUC 0,43 vs 0,57) |
| Decision Tree | sem transformação; class_weight=balanced | limiar ótimo F1 (OOF treino) | 0,824 | 0,408 | 0,741 | 0,526 | 0,860 | 0,492 | 0,428 ± 0,144 | Inferior na CV (PR-AUC 0,43 vs 0,57) |
| Random Forest | sem transformação; class_weight=balanced | limiar 0,5 | 0,887 | 0,559 | 0,704 | 0,623 | 0,918 | 0,693 | 0,553 ± 0,147 | Empate técnico com o melhor; não adotado (mais complexo) |
| Random Forest | sem transformação; class_weight=balanced | limiar ótimo F1 (OOF treino) | 0,877 | 0,526 | 0,741 | 0,615 | 0,918 | 0,693 | 0,553 ± 0,147 | Empate técnico com o melhor; não adotado (mais complexo) |

### 6.2 Validação cruzada aninhada no treino (média ± desvio-padrão entre folds)

| Modelo | ROC-AUC | PR-AUC | F1 (alta) | Recall (alta) | Precision (alta) |
|---|---|---|---|---|---|
| Regressão Logística | 0,882 ± 0,041 | 0,570 ± 0,119 | 0,503 ± 0,041 | 0,800 ± 0,094 | 0,367 ± 0,025 |
| Decision Tree | 0,812 ± 0,092 | 0,428 ± 0,144 | 0,468 ± 0,084 | 0,755 ± 0,186 | 0,340 ± 0,050 |
| Random Forest | 0,873 ± 0,050 | 0,553 ± 0,147 | 0,485 ± 0,127 | 0,591 ± 0,255 | 0,430 ± 0,065 |

### 6.3 Sensibilidade: com × sem duplicatas

| Cenário | Linhas | Teste c/ cópia no treino | Modelo | ROC-AUC teste | PR-AUC teste | F1 alta (teste) | PR-AUC CV |
|---|---|---|---|---|---|---|---|
| com duplicatas (split aleatório) | 1143 | 34 | Regressão Logística | 0,832 | 0,515 | 0,489 | 0,558 |
| com duplicatas (split aleatório) | 1143 | 34 | Decision Tree | 0,836 | 0,505 | 0,471 | 0,446 |
| com duplicatas (split aleatório) | 1143 | 34 | Random Forest | 0,905 | 0,738 | 0,604 | 0,642 |
| sem duplicatas | 1018 | 0 | Regressão Logística | 0,897 | 0,493 | 0,524 | 0,570 |
| sem duplicatas | 1018 | 0 | Decision Tree | 0,860 | 0,492 | 0,519 | 0,428 |
| sem duplicatas | 1018 | 0 | Random Forest | 0,918 | 0,693 | 0,623 | 0,553 |

**Fato:** diferença (com − sem duplicatas) na **PR-AUC da validação cruzada**: Regressão Logística −0,012; Decision Tree +0,018; Random Forest +0,089. Na **ROC-AUC do teste** (uma única partição pequena): Regressão Logística −0,065; Decision Tree −0,024; Random Forest −0,012. O maior ganho aparente com duplicatas está em **Random Forest** (+0,089); ganhos assim sugerem memorização de linhas repetidas, e não melhor generalização.

### 6.4 Modelo escolhido

**Regressão Logística** — maior PR-AUC média na CV aninhada (0,570 ± 0,119).

No teste (27 vinhos de alta qualidade): com limiar 0,5, recall = 0,81 (IC95% [0,667; 0,957]),
precision = 0,39, F1 = 0,52; com limiar ajustado (0,70), recall = 0,63
(IC95% [0,450; 0,818]), precision = 0,49, F1 = 0,55. ROC-AUC = 0,90; PR-AUC = 0,49
(linha de base aleatória ≈ 0,14). Na CV aninhada: PR-AUC 0,57 ± 0,12; recall 0,80 ± 0,09.

> **Atenção — teste × validação cruzada.** No teste, Random Forest teve PR-AUC 0,69 contra 0,49 de Regressão Logística. A escolha do modelo foi feita **antes** de olhar o teste, só com a validação cruzada (que usa muito mais exemplos da classe alta); o teste tem apenas 27 positivos e seus intervalos de confiança são largos. Por isso a escolha **não foi alterada** pelo resultado do teste — trocar de modelo ao ver o teste seria selecionar com os dados de avaliação. Esta divergência é um ponto a declarar e a validar com mais dados.

> **Leitura executiva das métricas.** *Recall* = de todos os vinhos realmente de alta qualidade, quantos o
> modelo conseguiu apontar. *Precision* = de todos os que o modelo apontou como de alta qualidade, quantos
> realmente eram. Há um **trade-off**: subir o recall costuma derrubar a precision. O limiar define em que
> ponto desse equilíbrio operar — uma decisão de negócio (custo de deixar passar um bom lote × custo de
> investigar um lote que não era).

> **Cautela estatística.** O conjunto de teste tem poucos exemplos da classe alta; os intervalos de
> confiança acima são largos. Diferenças pequenas entre modelos não são conclusivas.

Figuras: `results/confusion_matrices.png`, `results/figures/curvas_roc_pr.png`.

## 7. Variáveis relevantes

Importância **preditiva** (queda de PR-AUC ao embaralhar a variável no teste), para o modelo escolhido.
Variáveis de maior importância: **álcool, sulfatos e acidez volátil**.

- **Álcool**: importância por permutação 0,125 (± 0,055); a classe alta tem valor tipicamente maior (mediana 11,60 vs 10,00 na baixa/média). Sinal do coeficiente estável em 100% dos bootstraps.
- **Sulfatos**: importância por permutação 0,077 (± 0,038); a classe alta tem valor tipicamente maior (mediana 0,74 vs 0,60 na baixa/média). Sinal do coeficiente estável em 100% dos bootstraps.
- **Acidez volátil**: importância por permutação 0,047 (± 0,029); a classe alta tem valor tipicamente menor (mediana 0,36 vs 0,55 na baixa/média). Sinal do coeficiente estável em 100% dos bootstraps.
- **SO₂ livre**: importância por permutação 0,019 (± 0,016); a classe alta tem valor tipicamente menor (mediana 12,00 vs 14,00 na baixa/média). Sinal do coeficiente estável em 92% dos bootstraps.
- **SO₂ total**: importância por permutação 0,019 (± 0,028); a classe alta tem valor tipicamente menor (mediana 28,00 vs 39,00 na baixa/média). Sinal do coeficiente estável em 100% dos bootstraps.

**Interpretação e cautelas.** (i) Importância preditiva ≠ efeito causal. (ii) Muitas variáveis são
correlacionadas entre si (ex.: SO₂ livre × total; acidez fixa × pH × densidade), então a importância pode se
dividir entre elas e variar entre amostras. (iii) A direção refere-se à associação observada neste conjunto.
Figuras: `results/feature_importance.png`; tabela completa em `results/feature_importance.csv`
(inclui coeficientes padronizados, importância por impureza e estabilidade do sinal).

## 8. Implicações para o processo produtivo (hipóteses a validar)

As relações abaixo vêm de **associações** e devem ser tratadas como hipóteses para teste controlado, não
como receitas.

| Tema | Como usar a evidência |
|---|---|
| Monitoramento da produção | Acompanhar de forma contínua as variáveis de maior importância (álcool, sulfatos e acidez volátil) como indicadores de alerta |
| Controle de acidez | Verificar se a acidez volátil elevada se associa a lotes de menor qualidade e priorizar a investigação de causas (fermentação, contaminação) |
| Teor alcoólico | Avaliar, em ensaios controlados, se o ponto de colheita/fermentação que eleva o álcool melhora a avaliação |
| Sulfatos e SO₂ | Calibrar dosagens com cautela: a relação nos dados é associativa e pode refletir práticas de produtores específicos |
| Padronização da qualidade | Usar o score do modelo para identificar lotes fora do perfil dos vinhos bem avaliados |
| Priorização de análises | Encaminhar à degustação primeiro os lotes com maior probabilidade estimada |
| Apoio à avaliação de lotes | Triagem auxiliar com revisão humana; **não** decisão automática |

## 9. Limitações

- Base pequena e com poucos exemplos de alta qualidade (159); teste com 27 positivos.
- Uma única origem (vinho tinto português) — não generaliza para outras regiões, safras ou tipos.
- `quality` é opinião humana; o ruído do rótulo limita o desempenho máximo possível.
- Binarização em `quality ≥ 7` descarta informação.
- Decisões sobre duplicatas: não é possível distinguir erro de registro de vinhos distintos com medidas iguais.
- Sem validação externa (outras safras/produtores) e sem custo financeiro de falsos positivos/negativos.

## 10. Conclusão e recomendações

**Fato:** Regressão Logística foi o modelo adotado (maior PR-AUC média na CV aninhada (0,570 ± 0,119)).
**Recomendação:** usar o modelo como **triagem** — para ordenar lotes e orientar a análise sensorial — e
**não** como substituto do enólogo. Antes de qualquer uso operacional: (1) validar com dados de outras
safras/produtores; (2) definir o limiar a partir do custo real de falsos positivos e falsos negativos;
(3) manter revisão humana nos casos de maior risco; (4) monitorar o desempenho ao longo do tempo.

## 11. Como executar

```bash
git clone <URL-DO-REPOSITORIO>
cd wine-quality-classification
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# coloque a base oficial em data/WineQT.csv (veja data/README.md)
python -m src.run_all          # EDA + modelagem + sensibilidade + relatório (~7-10 min em máquina de 1 CPU)
jupyter lab notebooks/         # notebooks 01, 02 e 03 (usam os mesmos módulos de src/)
python tools/build_deck.py     # (opcional) regera docs/apresentacao_executiva.pptx — requer Node + pptxgenjs
```

Variável opcional `WINE_DATA=caminho/para/outro.csv` força outra base. O código imprime qual base foi usada.

## 12. Estrutura do repositório

```
wine-quality-classification/
├── data/                  # WineQT.csv (oficial) — veja data/README.md
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_preprocessamento.ipynb
│   ├── 03_modelagem.ipynb
│   └── _arquivo_original/ # versões originais do grupo (histórico, não executar)
├── src/                   # config, preprocessing, eda, train, evaluate, report, run_all
├── results/               # metrics*.csv, figures/, confusion_matrices.png, feature_importance.png
├── docs/                  # apresentacao_executiva.pptx/.pdf, roteiros (slides e vídeo), auditoria
├── tools/                 # build_notebooks.py, build_deck.py/.js (opcionais)
├── requirements.txt
└── README.md
```

## 13. Integrantes

- Vinícius — Tópico 2 (pré-processamento) *(único nome confirmado nos arquivos)*
- `[preencher: demais integrantes e responsabilidades]`

## 14. Referências

- Cortez, P.; Cerdeira, A.; Almeida, F.; Matos, T.; Reis, J. *Modeling wine preferences by data mining from
  physicochemical properties.* Decision Support Systems, 47(4), 547–553, 2009.
- UCI Machine Learning Repository — *Wine Quality*.
- Kaggle — *Wine Quality Dataset* (`yasserh/wine-quality-dataset`).
- Documentação do scikit-learn: Pipeline, GridSearchCV, PowerTransformer, métricas de classificação.
