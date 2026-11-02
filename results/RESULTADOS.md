# Resultados (gerado automaticamente por `src/report.py`)



Base: `WineQT.csv` — 1.143 linhas, 125 duplicatas exatas (10,9%).
Classe alta: 159 (13,9%); baixa/média: 984. Proporção 1 : 6,2.
Treino: 814 · Teste: 204 (classe alta no teste: 27).

## Modelo escolhido
**Regressão Logística** — maior PR-AUC média na CV aninhada (0,570 ± 0,119).
Hiperparâmetros selecionados no treino: `{"Regressão Logística": {"C": 0.1}, "Decision Tree": {"max_depth": 5, "min_samples_leaf": 20}, "Random Forest": {"max_depth": null, "min_samples_leaf": 5}}`

## Tabela comparativa final (conjunto de teste + CV aninhada)
| Modelo | Pré-processamento | Decisão | Accuracy | Precision (alta) | Recall (alta) | F1 (alta) | ROC-AUC | PR-AUC | PR-AUC CV (média ± dp) | Conclusão |
|---|---|---|---|---|---|---|---|---|---|---|
| Regressão Logística | Yeo-Johnson + padronização (dentro do Pipeline); class_weight=balanced | limiar 0,5 | 0,804 | 0,386 | 0,815 | 0,524 | 0,897 | 0,493 | 0,570 ± 0,119 | **Modelo escolhido** |
| Regressão Logística | Yeo-Johnson + padronização (dentro do Pipeline); class_weight=balanced | limiar ótimo F1 (OOF treino) | 0,863 | 0,486 | 0,630 | 0,548 | 0,897 | 0,493 | 0,570 ± 0,119 | **Modelo escolhido** |
| Decision Tree | sem transformação; class_weight=balanced | limiar 0,5 | 0,809 | 0,389 | 0,778 | 0,519 | 0,860 | 0,492 | 0,428 ± 0,144 | Inferior na CV (PR-AUC 0,43 vs 0,57) |
| Decision Tree | sem transformação; class_weight=balanced | limiar ótimo F1 (OOF treino) | 0,824 | 0,408 | 0,741 | 0,526 | 0,860 | 0,492 | 0,428 ± 0,144 | Inferior na CV (PR-AUC 0,43 vs 0,57) |
| Random Forest | sem transformação; class_weight=balanced | limiar 0,5 | 0,887 | 0,559 | 0,704 | 0,623 | 0,918 | 0,693 | 0,553 ± 0,147 | Empate técnico com o melhor; não adotado (mais complexo) |
| Random Forest | sem transformação; class_weight=balanced | limiar ótimo F1 (OOF treino) | 0,877 | 0,526 | 0,741 | 0,615 | 0,918 | 0,693 | 0,553 ± 0,147 | Empate técnico com o melhor; não adotado (mais complexo) |

## Validação cruzada aninhada (5 folds externos, treino apenas): média ± desvio-padrão
| Modelo | ROC-AUC | PR-AUC | F1 (alta) | Recall (alta) | Precision (alta) |
|---|---|---|---|---|---|
| Regressão Logística | 0,882 ± 0,041 | 0,570 ± 0,119 | 0,503 ± 0,041 | 0,800 ± 0,094 | 0,367 ± 0,025 |
| Decision Tree | 0,812 ± 0,092 | 0,428 ± 0,144 | 0,468 ± 0,084 | 0,755 ± 0,186 | 0,340 ± 0,050 |
| Random Forest | 0,873 ± 0,050 | 0,553 ± 0,147 | 0,485 ± 0,127 | 0,591 ± 0,255 | 0,430 ± 0,065 |

## Análise de sensibilidade: com × sem duplicatas
| Cenário | Linhas | Teste c/ cópia no treino | Modelo | ROC-AUC teste | PR-AUC teste | F1 alta (teste) | PR-AUC CV |
|---|---|---|---|---|---|---|---|
| com duplicatas (split aleatório) | 1143 | 34 | Regressão Logística | 0,832 | 0,515 | 0,489 | 0,558 |
| com duplicatas (split aleatório) | 1143 | 34 | Decision Tree | 0,836 | 0,505 | 0,471 | 0,446 |
| com duplicatas (split aleatório) | 1143 | 34 | Random Forest | 0,905 | 0,738 | 0,604 | 0,642 |
| sem duplicatas | 1018 | 0 | Regressão Logística | 0,897 | 0,493 | 0,524 | 0,570 |
| sem duplicatas | 1018 | 0 | Decision Tree | 0,860 | 0,492 | 0,519 | 0,428 |
| sem duplicatas | 1018 | 0 | Random Forest | 0,918 | 0,693 | 0,623 | 0,553 |

## Variáveis × classe (associação, não causalidade)
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

## Variáveis mais relevantes para o modelo escolhido
- **Álcool**: importância por permutação 0,125 (± 0,055); a classe alta tem valor tipicamente maior (mediana 11,60 vs 10,00 na baixa/média). Sinal do coeficiente estável em 100% dos bootstraps.
- **Sulfatos**: importância por permutação 0,077 (± 0,038); a classe alta tem valor tipicamente maior (mediana 0,74 vs 0,60 na baixa/média). Sinal do coeficiente estável em 100% dos bootstraps.
- **Acidez volátil**: importância por permutação 0,047 (± 0,029); a classe alta tem valor tipicamente menor (mediana 0,36 vs 0,55 na baixa/média). Sinal do coeficiente estável em 100% dos bootstraps.
- **SO₂ livre**: importância por permutação 0,019 (± 0,016); a classe alta tem valor tipicamente menor (mediana 12,00 vs 14,00 na baixa/média). Sinal do coeficiente estável em 92% dos bootstraps.
- **SO₂ total**: importância por permutação 0,019 (± 0,028); a classe alta tem valor tipicamente menor (mediana 28,00 vs 39,00 na baixa/média). Sinal do coeficiente estável em 100% dos bootstraps.
