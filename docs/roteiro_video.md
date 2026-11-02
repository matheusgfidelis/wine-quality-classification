# Roteiro do vídeo executivo (máx. 5 min)



**Requisitos do enunciado:** (1) pelo menos um integrante apresenta; (2) linguagem executiva, para diretores, **sem termos técnicos**; (3) até 5 minutos.

**Fonte única:** o texto de cada trecho abaixo é a *Fala* dos slides (`docs/apresentacao_slides.md`) e também está nas
**notas do apresentador** de `docs/apresentacao_executiva.pptx` — leia direto das notas.
**Duração:** a fala somada tem ~406 palavras ≈ 3:07 em ritmo normal (130 palavras/min) e ≈ 3:52 em ritmo calmo (105 palavras/min). Ambos cabem em 5:00.
**Integrante responsável:** **[definir]** (nenhum nome confirmado além do Vinícius, Tópico 2).

---

## 0:00 – 0:30 · Contexto e problema
- **Slides:** 1 → 2 (≈ 12 s + 18 s)
- **Tela:** capa → fluxo "medidas → lista priorizada → enólogo decide".
- **Fala:**
  "Saber se um vinho é excelente depende de degustação: é caro, demorado e subjetivo. E se medidas simples de laboratório ajudassem a antecipar essa nota? Este projeto testa isso. A ideia é apoiar o enólogo, não substituí-lo: gerar uma lista que ajude a decidir por onde começar a análise. A decisão final continua humana."
- **Responsável:** [definir]

## 0:30 – 1:15 · Dados e objetivo
- **Slides:** 3 → 4 (≈ 20 s + 25 s)
- **Tela:** números da base → gráfico de vinhos por nota com 7 e 8 destacados.
- **Fala:**
  "Usamos 1.143 vinhos tintos, com 11 medidas químicas e a nota de provadores. Não havia dados faltantes. Retiramos 125 linhas repetidas para o método não ‘decorar’ respostas que já viu. Definimos alta qualidade como nota 7 ou mais — só 13,9% dos vinhos. Quem dissesse sempre ‘não é de alta qualidade’ acertaria 86,1% das vezes e não acharia nenhum vinho bom. Por isso, não julgamos só pelo percentual de acertos."
- **Responsável:** [definir]

## 1:15 – 2:15 · Principais achados da análise
- **Slides:** 5 → 6 (≈ 30 s + 30 s)
- **Tela:** três gráficos de comparação entre classes → associação de cada medida com a nota.
- **Fala:**
  "Algumas medidas separam os grupos: álcool, acidez volátil e sulfatos. Os vinhos bem avaliados tendem a ter outro perfil químico — mas isso mostra que as medidas andam juntas, não que uma causa a outra. Várias medidas também variam juntas por razões químicas: o dióxido de enxofre total inclui o livre, e mais acidez significa pH menor. Por isso o peso de cada medida pode se dividir entre medidas parecidas."
- **Responsável:** [definir]

## 2:15 – 3:30 · Como testamos e resultado
- **Slides:** 7 → 8 (≈ 25 s + 50 s)
- **Tela:** etapas do teste → gráfico "bons vinhos encontrados × indicações certas".
- **Fala:**
  "Para testar com justiça, guardamos 20% dos vinhos como prova final, que ninguém viu no treino, e comparamos três métodos. Escolhemos antes de olhar a prova final, para o resultado não ficar otimista. O método escolhido foi um método estatístico clássico, simples e fácil de explicar. Ele encontrou cerca de 81% dos vinhos realmente bons, e cerca de 39% das suas indicações estavam certas. É um equilíbrio: achar mais vinhos bons significa aceitar mais alarmes falsos — uma decisão de negócio. Como a prova final tem só 27 vinhos bons, a incerteza é grande."
- **Responsável:** [definir]

## 3:30 – 4:20 · Medidas-chave e implicações
- **Slides:** 9 → 10 (≈ 25 s + 25 s)
- **Tela:** ranking das medidas → três ações propostas.
- **Fala:**
  "As medidas que mais pesam nas previsões são álcool, sulfatos e acidez volátil. Isso mostra o que o método usa para prever — não o que faz um vinho ficar melhor. Na prática: ordenar a fila de degustação, acompanhar essas medidas de perto e investigar lotes fora do perfil. São hipóteses a testar de forma controlada antes de mudar qualquer processo, e o ganho financeiro ainda não foi medido."
- **Responsável:** [definir]

## 4:20 – 5:00 · Conclusão e recomendação
- **Slide:** 11 (≈ 40 s)
- **Tela:** limites e próximos passos.
- **Fala:**
  "Os limites: base pequena, de uma só origem, e a nota é opinião humana. Recomendamos um piloto: usar o método como triagem, comparar com o julgamento dos enólogos em novos lotes, definir o equilíbrio entre bons vinhos achados e alarmes falsos pelo custo, e validar com outras safras. Obrigado."
- **Responsável:** [definir]

---

**Antes de gravar:** (1) base usada é a `WineQT.csv` (sem aviso de ensaio no topo); (2) os números falados batem com
`results/RESULTADOS.md`; (3) faça uma leitura cronometrada e, se passar de 4:45, corte frases dos slides 6 e 8;
(4) diga "recall" e "precision" **apenas** se alguém perguntar — no vídeo usamos "bons vinhos encontrados" e "indicações certas".
