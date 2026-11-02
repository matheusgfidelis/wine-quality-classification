# Auditoria do projeto — Tech Challenge Fase 2

Escopo: todos os arquivos recebidos em `techChallenge.zip`. **Não inventei valores**; o que não pôde ser
confirmado está marcado como **"não confirmado"**, com a forma de verificar.

## 0. Estado dos insumos (atualizado após o recebimento do PDF e da WineQT)

| Insumo | Situação |
|---|---|
| Especificação oficial (PDF) | **Lida.** Os requisitos conferem com a transcrição usada na auditoria. Dois pontos novos do PDF: (1) a apresentação executiva deve ser **PPT ou PDF dentro do repositório**; (2) o vídeo deve usar **linguagem executiva, sem termos técnicos**, com pelo menos um integrante apresentando. Ambos foram tratados (deck `.pptx` gerado; roteiro sem jargão) |
| `WineQT.csv` | **Recebido e validado:** 1.143 × 13, 0 nulos, notas 3–8 (6/33/483/462/143/16), 159 de alta qualidade (13,9%) |
| Resultados | Pipeline executado **na WineQT** (script e notebooks 01–03, sem erros); reproduzido em clone limpo |
| Nomes dos integrantes | Só "Vinícius" aparece nos arquivos; demais ficam **a preencher** |

---

## 1. Tabela de auditoria

Legenda de status: ✅ concluído · 🟡 parcial · ❌ ausente. Prioridade: **O** obrigatória · **R** recomendada · **Op** opcional.

| # | Requisito oficial | Arquivo | Evidência encontrada | Status | Inconsistência / risco | Correção | Prio. |
|---|---|---|---|---|---|---|---|
| 1 | Compreensão do problema | `Tech2_DT_RF` (texto inicial, seção 17) | Introdução curta e seção "Insights" respondendo perguntas de negócio. A EDA (`Fase_2_Vinhos_`) só tem o título | 🟡 | Contexto vitivinícola, diferença entre qualidade química × sensorial e uso pretendido não estão escritos. A versão `(1)` do notebook **não tem** a seção 17 | Contexto/objetivo reescritos no README e nos slides; versão `(1)` descartada | O |
| 2 | Definir `quality ≥ 7` como alvo binário | EDA e DT/RF | Presente nos dois (`apply(lambda)` e `(quality>=7).astype(int)`) | ✅ | Duas implementações paralelas (rótulos em texto na EDA; 0/1 no DT/RF) | Fonte única: `criar_alvo()` em `src/preprocessing.py` | R |
| 3 | EDA: dimensões, tipos, nulos | EDA, DT/RF, Prep | `shape`, `info`, `isnull` (1143×13, 0 nulos nas saídas; 1599×12 na red) | ✅ | Bases diferentes entre notebooks (seção 3) | Base única | O |
| 4 | EDA: duplicatas | Prep (red) | Só no Prep: 240 (15,0%) na red. **Não analisadas na WineQT** nos notebooks originais | 🟡 | **Confirmado:** a WineQT tem 125 duplicatas exatas (10,9%); `Id 0` e `Id 4` são idênticos | `eda.resumo_estrutural` e sensibilidade com×sem duplicatas | O |
| 5 | Estatísticas descritivas | EDA | `describe()` executado | ✅ | — | Mantido | — |
| 6 | Distribuição de `quality` e do alvo binário | EDA | Contagens, pizza e barras; tabela de balanceamento (6 notas; 984/159 = 86,09%/13,91%) | ✅ | Gráfico de pizza + barras repetem a mesma informação; texto diz "5 níveis de qualidade" mas os dados têm **6** (3–8) e o próprio código imprime `[5 6 7 4 8 3]` | Painel único (notas coloridas por classe + binária); texto corrigido | R |
| 7 | Distribuições das variáveis | EDA | Não há histogramas por variável nas saídas (há gráficos de linha e barras agrupadas) | 🟡 | Pergunta "como se distribui cada variável?" sem resposta direta | `eda.histogramas` (com assimetria no título) | O |
| 8 | Correlações com justificativa | DT/RF, EDA | Heatmap Pearson (DT/RF e EDA) **sem texto interpretativo**; EDA exclui `Id` mas inclui `quality` | 🟡 | Pearson sob forte assimetria; nenhuma frase distingue correlação de causalidade | Spearman + barras de correlação com `quality`; texto cauteloso | O |
| 9 | Outliers e valores inconsistentes | EDA, Prep | IQR em tabela (EDA e Prep). **Nenhuma checagem de inconsistência física** | 🟡 | A tabela de outliers da EDA inclui a **própria `quality`** (22; 1,92%) — sem sentido | `eda.outliers_iqr` (só features) + `eda.inconsistencias` (SO₂ livre>total, pH, álcool, densidade, negativos) | O |
| 10 | Balanceamento | EDA, DT/RF, Prep | Contagens e proporção; Prep usa `class_weight="balanced"` | ✅ | DT/RF **não** usa `class_weight` | `class_weight="balanced"` em todos | O |
| 11 | Dados faltantes | Todos | Verificado: 0 nulos | ✅ | `dropna()` no DT/RF é inócuo (1143→1143) | Removido do fluxo; registrado "sem imputação" | Op |
| 12 | Normalização/padronização | Prep | Yeo-Johnson/StandardScaler **dentro** do Pipeline; demonstração de vazamento | ✅ | Feito na **red**, não na WineQT. README do Tópico 2 diz vazamento "no máximo 3,5%", mas a saída do notebook mostra **5,01%** (cloretos) | Refeito sobre a base única; números do README agora gerados por código | O |
| 13 | Feature engineering (se relevante) | Prep | 7 razões enológicas testadas (A/B) | ✅ | Ganho ~0 no linear e negativo no RF; **ligada por padrão** no perfil linear | Passa a ser opt-in; reportado como resultado negativo | R |
| 14 | ≥ 2 modelos | DT/RF (WineQT); Prep (red) | DT + RF (WineQT); LogReg + RF (red) | ✅ | Pares de modelos diferentes em **bases diferentes** — não comparáveis | 3 modelos na mesma base (LogReg, DT, RF) | O |
| 15 | Avaliação e comparação | DT/RF | Accuracy, `classification_report`, matriz de confusão, CV só de accuracy | 🟡 | **Seleção de hiperparâmetros por acurácia** (inadequada com 13,9% de positivos). Sem ROC-AUC/PR-AUC, sem desvio da CV | Seleção por PR-AUC; CV aninhada; ROC-AUC, PR-AUC, IC bootstrap | O |
| 16 | Hiperparâmetros sem usar o teste | DT/RF | Selecionados na CV do treino ✅ | ✅ | **Melhor valor na borda da grade** (DT `max_depth=5`; RF `max_depth=5` e `n_estimators=100`) → busca possivelmente incompleta. `random_state=7` aqui × `42` no Tópico 2 | Grades ampliadas (RF `None`/10/6; DT 3–6); `random_state` único = 42 | R |
| 17 | Interpretação das variáveis influentes | DT/RF, EDA | `feature_importances_` da RF (gráfico sem texto); EDA conclui "álcool, SO₂ livre e total" | 🟡 | A conclusão da EDA é **contradita pelos dados da WineQT**: SO₂ livre/total têm associação **fraca** com a nota; acidez volátil e sulfatos são mais associadas. **Confirmado na WineQT:** ρ de Spearman com a nota — álcool 0,50; acidez volátil −0,40; sulfatos 0,39; SO₂ total −0,19; SO₂ livre −0,06 | Permutation importance, impureza, coeficientes + estabilidade; texto gerado dos dados | O |
| 18 | Implicações para o processo produtivo | DT/RF (seção 17) | Texto genérico | 🟡 | "Os resultados foram bem satisfatórios" e "os modelos usaram correlação entre junções de ingredientes" não são sustentados: recall da classe alta foi 0,47 (DT) e 0,41 (RF) | Seção 8 do README; linguagem de hipótese | O |
| 19 | Repositório GitHub organizado | zip | Pastas soltas, cópias duplicadas, ZIP dentro de ZIP | ❌ | Ver seção 3 | Estrutura `wine-quality-classification/` entregue | O |
| 20 | Apresentação executiva | — | Inexistente | ❌ | — | `docs/apresentacao_slides.md` (11 slides) | O |
| 21 | Vídeo ≤ 5 min | — | Inexistente | ❌ | — | `docs/roteiro_video.md` | O |

### Verificação de números já citados (agora **re-executados** na WineQT)

| Afirmação do pedido | Situação |
|---|---|
| WineQT 1.143×13; 0 nulos; Id excluído | **Confirmado** no arquivo recebido |
| 984 baixa/média e 159 alta | **Confirmado** |
| Split 80/20 estratificado (914/229; 32 positivos no teste) | **Confirmado nas saídas antigas.** O fluxo novo **remove duplicatas antes do split** → 814 treino / 204 teste (27 positivos no teste), `random_state=42`; por isso os números não são diretamente comparáveis aos antigos |
| DT: acurácia 0,878; F1 alta 0,52; recall alta 0,47 | **Confirmado nas saídas antigas** (DT sem `class_weight`). No fluxo novo (`class_weight=balanced`, sem duplicatas): acurácia 0,809, recall 0,78, F1 0,52. Acurácia menor e recall maior são consequência esperada do balanceamento |
| RF: acurácia 0,856; F1 alta 0,44; recall alta 0,41 | **Confirmado nas saídas antigas.** Novo: acurácia 0,887, recall 0,70, F1 0,62 (ver `results/metrics.csv`) |
| Duplicatas | **WineQT: 125 (10,9%)** — 1.018 linhas após remover. Red: 240 (15,0%) |
| Red: 77/320 linhas de teste com cópia | Reproduzido na red. Na **WineQT**, o split aleatório com duplicatas deixa **34 de 229** linhas de teste com cópia no treino |

---

## 2. Matriz de conformidade com a especificação

| Requisito da especificação | Antes | Depois (este pacote) |
|---|---|---|
| Compreensão do problema | 🟡 | ✅ README §1–2, slides 1–4 |
| EDA, distribuições | 🟡 | ✅ notebook 01 + `eda.py` |
| Correlações justificadas | 🟡 | ✅ Spearman + cautela causal |
| Outliers e valores inconsistentes | 🟡 | ✅ |
| Balanceamento | ✅ | ✅ + `class_weight` + PR-AUC |
| Dados faltantes | ✅ | ✅ (sem imputação, documentado) |
| Normalização/padronização | ✅ (na red) | ✅ Pipeline, base única |
| Feature engineering | ✅ (na red) | ✅ testada e descartada com evidência |
| ≥ 2 modelos | ✅ (bases diferentes) | ✅ 3 modelos, mesma base |
| Avaliação/comparação | 🟡 | ✅ CV aninhada, 6 métricas, IC |
| Variáveis influentes | 🟡 | ✅ 3 técnicas + estabilidade |
| Implicações produtivas | 🟡 | ✅ (como hipóteses) |
| Repositório | ❌ | ✅ |
| Apresentação | ❌ | ✅ roteiro slide a slide **e** `docs/apresentacao_executiva.pptx` e `.pdf` (11 slides, sem jargão, notas do apresentador) |
| Vídeo ≤ 5 min | ❌ | ✅ roteiro (gravação é com vocês) |

*Pendente em todos os itens:* **rodar na WineQT** e conferir contra o PDF.

---

## 3. Principais inconsistências e riscos

1. **Duas bases diferentes entre notebooks.** EDA e DT/RF usam `WineQT.csv` (1.143); o Prep usa `winequality-red.csv` (1.599). Os resultados do Prep (ROC-AUC 0,88, "240 duplicatas") **não valem** para a WineQT.
2. **Seleção por acurácia** com apenas 13,9% de classe alta: um modelo que nunca prevê "alta" tem ~86% de acurácia. O recall da classe alta nos testes anteriores (0,41–0,47) é fraco, mas o texto do notebook diz que o resultado foi "bem satisfatório".
3. **Grade de hiperparâmetros com melhor valor na borda** (DT e RF) — a busca pode não ter chegado ao ótimo.
4. **Conclusão da EDA contradita pelos dados:** "SO₂ livre e total são os que mais influenciam" foi tirada de gráficos de linha com escalas diferentes. Na WineQT (confirmado), a associação deles com a nota é fraca; álcool, acidez volátil e sulfatos se destacam.
5. **Gráficos de linha da média por nota** sugerem tendência contínua e usam poucas amostras nas notas 3 e 8 (6 e 16 vinhos na WineQT). Substituídos por boxplots por classe.
6. **Ambiente não reprodutível:** `01_eda` e `DT/RF` leem `WineQT.csv` do diretório corrente; o DT/RF salva em `results/` **dependendo de onde o notebook roda** e imprimiu um caminho absoluto de OneDrive; o notebook de EDA tem **todas** as `execution_count` nulas (saídas sem ordem de execução comprovada); `plotly` importado sem uso.
7. **Células duplicadas/vazias:** `pd.read_csv` repetido duas vezes na EDA; célula final vazia.
8. **Arquivos duplicados:** `Tech2_..._(1).ipynb` (sem a seção 17), notebook do Tópico 2 em 2 lugares (o da raiz de `tech2_topic2/` **falharia**: `../data` e `src` não existem a partir dali), `preprocessing.py` em 2 lugares, ZIP dentro do ZIP, e PNGs do Tópico 2 em duas versões **diferentes** (hashes distintos).
9. **Números divergentes entre `README_topico2.md`, docstring de `preprocessing.py` e o notebook** (vazamento "3,5%" × 5,01%; p=0,010 × 0,0083; efeito de features novas ±0,004/0,006 × valores da tabela). Qualquer número copiado à mão pode ficar desatualizado.
10. **Duplicatas:** remover é a decisão mais conservadora, mas não prova que sejam erros (valores arredondados). Exige análise de sensibilidade e declaração explícita.
11. **Teste pequeno:** 32 positivos (WineQT, 20%) → F1/recall com IC95% largos. Diferenças pequenas entre modelos não são conclusivas.
12. **PDF da especificação não lido** (§0).

---

## 4. Decisão sobre a base de dados

**Fatos (confirmados nos arquivos; `results/comparacao_bases.md`):**
- WineQT: 1.143 linhas × 13 colunas (12 + `Id`); 0 nulos; notas 3–8 (6/33/483/462/143/16); alta = 159 (13,91%); **125 duplicatas exatas** (10,9%).
- winequality-red: 1.599 × 12; 0 nulos; notas 3–8 (10/53/681/638/199/18); alta = 217 (13,57%); 240 duplicatas exatas (15,0%).
- **Todas as 1.143 linhas da WineQT existem na red** (comparação linha a linha, todas as colunas) e a contagem por nota da WineQT é ≤ à da red em todas as notas.

**Conclusão (agora verificada):** a WineQT é um **subconjunto** da base de vinho tinto, acrescido da coluna `Id`.

**Decisão:** usar **uma única base — `WineQT.csv`** — em EDA, modelagem, slides e vídeo.
*Por quê:* (1) é a base já usada por 2 dos 3 notebooks e pelo modelo DT/RF; (2) os números do pedido (1.143; 984/159) são dela; (3) evita comparar métricas entre amostras diferentes. A red fica como material de apoio (o Tópico 2 foi explorado nela) e **não entra** em nenhuma tabela final. *Consequência:* os achados do Tópico 2 (ex.: 240 duplicatas, ganhos de Yeo-Johnson) **precisam ser re-medidos na WineQT** — o código novo já faz isso.

*Texto para o README/slide:* "Adotamos uma única base — WineQT.csv — em todas as etapas. A winequality-red.csv, de origem semelhante, foi usada só em uma exploração preliminar e não é comparável: tem outro número de linhas e de duplicatas."

> **Suposição declarada:** que a especificação oficial aceita a WineQT. Não pude confirmar sem o PDF.

---

## 5. Decisão sobre o fluxo metodológico final

1. Carregar base única → criar alvo (`quality ≥ 7`) → remover duplicatas exatas (decisão documentada + sensibilidade com×sem).
2. Split 80/20 estratificado (`random_state=42`); teste intocado.
3. Pipelines por família de modelo (Yeo-Johnson só no linear; árvores sem transformação).
4. `class_weight="balanced"`.
5. CV estratificada **aninhada** + `GridSearchCV` por **PR-AUC**.
6. Escolha do modelo pela regra do 1 desvio-padrão (só com a CV).
7. Limiar 0,5 e limiar F1-ótimo via *out-of-fold* do treino.
8. Teste: métricas, IC bootstrap, matrizes, curvas; importâncias (permutação, impureza, coeficientes).

**Por que PR-AUC e não "o recall"?** Suposição declarada: o objetivo é *priorizar lotes* (encontrar bons vinhos sem encher a fila de falsos alarmes). PR-AUC é independente de limiar e foca na classe rara. O recall é reportado e o limiar fica como decisão de negócio. Se o negócio priorizar não perder nenhum vinho bom, trocar `SELECAO` em `src/train.py` para `recall_alta`.

**Sobre SHAP:** não incluído (opcional); permutação + coeficientes cobrem o requisito sem dependência extra.

**Sobre os slides:** o PDF pede PPT ou PDF **dentro do repositório**. Entregues `docs/apresentacao_executiva.pptx` e `.pdf` (11 slides ≈ 27 s cada, gráficos nativos, sem termos técnicos). A *fala* de cada slide é a nota do apresentador **e** o texto do vídeo (fonte única). Regenerável com `python tools/build_deck.py` (requer Node + pptxgenjs).

---

## 6. Pendências antes de entregar

*(Já concluído: base oficial rodada, PDF conferido, notebooks 01–03 executados, deck gerado, reprodutibilidade testada em clone limpo.)*

1. Preencher os **nomes dos integrantes** (README §13 e roteiro do vídeo).
2. **Abrir o deck no PowerPoint** e ajustar identidade visual/ordem, se desejarem (adicionar nomes na capa).
3. **Gravar o vídeo** (≤ 5:00) com o roteiro; conferir que os números falados batem com `results/RESULTADOS.md`.
4. Subir o repositório no GitHub (o `.gitignore` já exclui caches) e **conferir os dois links** (repositório e vídeo) no envio.
5. Decidir se o `data/winequality-red.csv` fica no repositório (é material de apoio; a base oficial é a WineQT).

## 7. Melhorias recomendadas

- Validar no PDF se há exigência de `GridSearch`/formato de entrega.
- Estimar custo de falso positivo × falso negativo para escolher o limiar.
- Testar `GroupKFold` agrupando linhas idênticas (mantém dados sem vazar).
- SHAP para o modelo escolhido (opcional).
- Calibração de probabilidades (se as probabilidades forem exibidas a gestores).
- `.pptx` final com identidade visual (após números finais).

## 8. Checklist final de entrega

- [x] `data/WineQT.csv` presente e validada (1.143 × 13)
- [x] `python -m src.run_all` roda sem erro e reproduz as métricas dos notebooks (clone limpo)
- [x] README sem aviso de "ensaio"; números gerados por código
- [x] `results/`: `metrics.csv`, `confusion_matrices.png`, `feature_importance.png`, `figures/`
- [x] Notebooks 01–03 executados em ordem e salvos com saídas
- [x] Nenhum caminho absoluto no código
- [x] Apresentação em PPT e PDF dentro do repositório (`docs/apresentacao_executiva.pptx` / `.pdf`)
- [ ] Integrantes preenchidos
- [ ] Vídeo ≤ 5 min gravado (linguagem sem termos técnicos)
- [ ] Links do repositório e do vídeo enviados conforme o PDF
