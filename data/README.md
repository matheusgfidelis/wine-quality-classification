# Dados

| Arquivo | Papel | Situação |
|---|---|---|
| `WineQT.csv` | **Base oficial do projeto** (EDA, modelagem, slides, vídeo) | **Não incluída neste pacote — coloque aqui** |
| `winequality-red.csv` | Base original da UCI (vinho tinto, 1.599 linhas). Apenas apoio/ensaio | Incluída |

## Como obter `WineQT.csv`
Kaggle — *Wine Quality Dataset* (`yasserh/wine-quality-dataset`). Baixe o CSV e salve como `data/WineQT.csv`
(esperado: 1.143 linhas × 13 colunas, com a coluna `Id`; sem valores nulos).
Se o seu grupo recebeu o arquivo do professor/curso, use essa cópia.

## Qual base o código usa?
1. `WINE_DATA` (variável de ambiente), se definida;
2. `data/WineQT.csv`, se existir;
3. `data/winequality-red.csv` (**ensaio**: o código imprime um aviso e `results/` e `README.md` ficam marcados como ensaio).

Para comparar as duas bases (subconjunto? duplicatas? notas?), com ambas em `data/`:
`python -m src.compare_datasets` → `results/comparacao_bases.md`.
