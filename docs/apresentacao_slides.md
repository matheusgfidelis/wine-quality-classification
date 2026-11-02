# Apresentação executiva — 11 slides para 5 minutos



**Regras (conforme o enunciado do Tech Challenge):** linguagem executiva, **sem termos técnicos**, uma mensagem por
slide, só números de `results/`, nenhuma promessa de impacto não medido. A **fala** de cada slide é também a
nota do apresentador no `.pptx` e o texto do vídeo (`docs/roteiro_video.md`) — uma única fonte, sem divergência.
Base: `WineQT.csv`.

| Slide | Tema | Tempo-alvo |
|---|---|---|
| 1–2 | Contexto e problema | 0:00 – 0:30 |
| 3–4 | Dados e definição de qualidade | 0:30 – 1:15 |
| 5–6 | Achados da análise exploratória | 1:15 – 2:15 |
| 7–8 | Como testamos e resultado | 2:15 – 3:30 |
| 9–10 | Variáveis-chave e implicações | 3:30 – 4:20 |
| 11 | Limites e próximos passos | 4:20 – 5:00 |

---

## Slide 1 — Contexto e oportunidade
- **Mensagem principal:** Medidas de laboratório são baratas e rotineiras; a degustação é cara e subjetiva.
- **Conteúdo:** Título-pergunta + símbolo "≥ 7" (nota que define um vinho de alta qualidade).
- **Visual:** capa escura com o círculo "≥ 7".
- **Fala:** "Saber se um vinho é excelente depende de degustação: é caro, demorado e subjetivo. E se medidas simples de laboratório ajudassem a antecipar essa nota?"
- **Insight executivo:** Existe um dado barato e já disponível que pode apoiar uma decisão cara.
- **Transição:** "Veja qual é, exatamente, o objetivo."

## Slide 2 — Problema de negócio
- **Mensagem principal:** O objetivo é priorizar a análise, não substituir o enólogo.
- **Conteúdo:** Fluxo de 4 etapas: medidas de laboratório → estimativa da chance de nota alta → lista de lotes priorizada → enólogo decide.
- **Visual:** 4 cartões com setas.
- **Fala:** "Este projeto testa isso. A ideia é apoiar o enólogo, não substituí-lo: gerar uma lista que ajude a decidir por onde começar a análise. A decisão final continua humana."
- **Insight executivo:** O valor está em priorizar, não em decidir sozinho.
- **Transição:** "Vamos aos dados."

## Slide 3 — Dados utilizados
- **Mensagem principal:** 1.143 vinhos, 11 medidas químicas e uma nota de provadores.
- **Conteúdo:** 4 números: vinhos analisados · medidas por vinho · valores faltantes (0) · linhas repetidas (125, 10,9%).
- **Visual:** 4 cartões de destaque.
- **Fala:** "Usamos 1.143 vinhos tintos, com 11 medidas químicas e a nota de provadores. Não havia dados faltantes. Retiramos 125 linhas repetidas para o método não ‘decorar’ respostas que já viu."
- **Insight executivo:** A base é pequena — isso pede cautela nas conclusões.
- **Transição:** "Como transformamos a nota em uma decisão?"

## Slide 4 — Como a qualidade foi definida e quantos vinhos são de alta qualidade
- **Mensagem principal:** Alta qualidade = nota 7 ou mais — e só 13,9% dos vinhos chegam lá.
- **Conteúdo:** Gráfico de vinhos por nota (7 e 8 destacados) · 159 de 1.143 · "chutar sempre ‘não é de alta qualidade’ acertaria 86,1%".
- **Visual:** gráfico de barras nativo + 2 números em destaque.
- **Fala:** "Definimos alta qualidade como nota 7 ou mais — só 13,9% dos vinhos. Quem dissesse sempre ‘não é de alta qualidade’ acertaria 86,1% das vezes e não acharia nenhum vinho bom. Por isso, não julgamos só pelo percentual de acertos."
- **Insight executivo:** O corte é uma escolha de negócio, e o simples "percentual de acertos" engana quando o grupo de interesse é raro.
- **Transição:** "O que os dados mostram sobre esses vinhos?"

## Slide 5 — Achado: o que separa os vinhos de alta qualidade
- **Mensagem principal:** álcool, acidez volátil e sulfatos separam melhor os bons vinhos — como **associação**, não causa.
- **Conteúdo:** 3 gráficos comparando vinhos de alta e de baixa/média qualidade.
- **Visual:** `results/figures/06_top3_boxplots.png`.
- **Fala:** "Algumas medidas separam os grupos: álcool, acidez volátil e sulfatos. Os vinhos bem avaliados tendem a ter outro perfil químico — mas isso mostra que as medidas andam juntas, não que uma causa a outra."
- **Insight executivo:** Há sinal nos dados, mas ele sozinho não prova causa.
- **Transição:** "Mas essas medidas também se influenciam entre si."

## Slide 6 — Achado: muitas medidas andam juntas
- **Mensagem principal:** Relações fortes entre medidas têm explicação química e pedem cautela.
- **Conteúdo:** Gráfico da associação de cada medida com a nota · 2 pares fortes com a explicação (tabela completa em `results/correlacoes_justificadas.csv`).
- **Visual:** gráfico de barras nativo + 2 cartões.
- **Fala:** "Várias medidas também variam juntas por razões químicas: o dióxido de enxofre total inclui o livre, e mais acidez significa pH menor. Por isso o peso de cada medida pode se dividir entre medidas parecidas."
- **Insight executivo:** Medidas parecidas dividem a importância; interpretar com cautela.
- **Transição:** "Como transformamos isso em uma previsão confiável?"

## Slide 7 — Como testamos
- **Mensagem principal:** Três métodos comparados de forma justa, sem "colar" na prova final.
- **Conteúdo:** 5 etapas: retirar repetidos → separar a prova final (20%) → treinar e comparar → escolher → provar uma única vez.
- **Visual:** linha de 5 etapas numeradas.
- **Fala:** "Para testar com justiça, guardamos 20% dos vinhos como prova final, que ninguém viu no treino, e comparamos três métodos. Escolhemos antes de olhar a prova final, para o resultado não ficar otimista."
- **Insight executivo:** O processo foi desenhado para evitar resultados otimistas.
- **Transição:** "Veja como ficou o resultado."

## Slide 8 — Resultado
- **Mensagem principal:** O método escolhido encontra 81% dos bons vinhos — com alarmes falsos.
- **Conteúdo:** Gráfico: para cada método, bons vinhos encontrados × indicações certas · método adotado · margem de incerteza.
- **Visual:** gráfico de barras agrupadas nativo + 2 cartões.
- **Fala:** "O método escolhido foi um método estatístico clássico, simples e fácil de explicar. Ele encontrou cerca de 81% dos vinhos realmente bons, e cerca de 39% das suas indicações estavam certas. É um equilíbrio: achar mais vinhos bons significa aceitar mais alarmes falsos — uma decisão de negócio. Como a prova final tem só 27 vinhos bons, a incerteza é grande."
- **Insight executivo:** Achar mais vinhos bons e evitar alarmes falsos puxam em direções opostas; o ponto de equilíbrio é decisão de negócio.
- **Transição:** "E o que mais pesa nas previsões?"

## Slide 9 — Medidas mais influentes
- **Mensagem principal:** álcool, sulfatos e acidez volátil pesam mais nas previsões.
- **Conteúdo:** Ranking das 6 medidas · o que se observa nos dados · "peso na previsão não é causa".
- **Visual:** gráfico de barras horizontais nativo + 2 cartões.
- **Fala:** "As medidas que mais pesam nas previsões são álcool, sulfatos e acidez volátil. Isso mostra o que o método usa para prever — não o que faz um vinho ficar melhor."
- **Insight executivo:** Esses indicadores são bons candidatos a monitoramento — e a testes controlados.
- **Transição:** "O que isso significa para a operação?"

## Slide 10 — Implicações para o negócio
- **Mensagem principal:** Usar o método como triagem e as medidas-chave como alerta — como hipóteses a validar.
- **Conteúdo:** 3 ações: priorizar a fila de degustação · monitorar as medidas-chave · investigar lotes fora do perfil.
- **Visual:** 3 cartões numerados.
- **Fala:** "Na prática: ordenar a fila de degustação, acompanhar essas medidas de perto e investigar lotes fora do perfil. São hipóteses a testar de forma controlada antes de mudar qualquer processo, e o ganho financeiro ainda não foi medido."
- **Insight executivo:** Valor de priorização, ainda não medido financeiramente.
- **Transição:** "Também é preciso ser claro sobre os limites."

## Slide 11 — Limites e próximos passos
- **Mensagem principal:** Promissor, mas ainda não pronto para decidir sozinho: o próximo passo é um piloto com revisão humana.
- **Conteúdo:** Esquerda — o que ainda não sabemos (4 itens). Direita — 4 próximos passos.
- **Visual:** slide escuro de fechamento, duas colunas.
- **Fala:** "Os limites: base pequena, de uma só origem, e a nota é opinião humana. Recomendamos um piloto: usar o método como triagem, comparar com o julgamento dos enólogos em novos lotes, definir o equilíbrio entre bons vinhos achados e alarmes falsos pelo custo, e validar com outras safras. Obrigado."
- **Insight executivo:** O próximo passo é aprender com dados novos, não escalar.
- **Transição:** (fim) "Ficamos à disposição para perguntas."

---

### Notas técnicas — NÃO apresentar (para responder a perguntas dos professores)
- Método escolhido: **Regressão Logística** — maior PR-AUC média na CV aninhada (0,570 ± 0,119).
- Medidas no teste (limiar padrão 0,5): recall da classe alta 0,81 (IC95% [0,667; 0,957]), precision 0,39, F1 0,52, ROC-AUC 0,90, PR-AUC 0,49.
- Limiar ajustado (0,70): recall 0,63, precision 0,49, F1 0,55 (IC95% do recall [0,450; 0,818]).
> **Atenção — teste × validação cruzada.** No teste, Random Forest teve PR-AUC 0,69 contra 0,49 de Regressão Logística. A escolha do modelo foi feita **antes** de olhar o teste, só com a validação cruzada (que usa muito mais exemplos da classe alta); o teste tem apenas 27 positivos e seus intervalos de confiança são largos. Por isso a escolha **não foi alterada** pelo resultado do teste — trocar de modelo ao ver o teste seria selecionar com os dados de avaliação. Esta divergência é um ponto a declarar e a validar com mais dados.
- Sensibilidade a duplicatas (`results/sensibilidade_duplicatas.csv`): diferença (com − sem duplicatas) na **PR-AUC da validação cruzada**: Regressão Logística −0,012; Decision Tree +0,018; Random Forest +0,089. Na **ROC-AUC do teste** (uma única partição pequena): Regressão Logística −0,065; Decision Tree −0,024; Random Forest −0,012. O maior ganho aparente com duplicatas está em **Random Forest** (+0,089); ganhos assim sugerem memorização de linhas repetidas, e não melhor generalização.
- Tabelas completas: `results/RESULTADOS.md` · métricas: `results/metrics.csv`.
