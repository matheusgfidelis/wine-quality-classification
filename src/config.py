"""Configuração central do projeto: caminhos relativos e parâmetros fixos.

Nenhum caminho absoluto é usado: tudo é derivado da localização deste arquivo,
então o projeto funciona em qualquer clone do repositório.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
FIG_DIR = RESULTS_DIR / "figures"
DOCS_DIR = ROOT / "docs"

# Reprodutibilidade
RANDOM_STATE = 42
TEST_SIZE = 0.20
CUTOFF = 7  # quality >= 7 -> alta qualidade

# Decisão metodológica: a base oficial do projeto é a WineQT.csv.
# A winequality-red.csv só é usada como alternativa de ENSAIO (o código avisa).
OFFICIAL_DATASET = "WineQT.csv"
FALLBACK_DATASET = "winequality-red.csv"

# Decisão metodológica: remover linhas 100% idênticas ANTES do split.
# A análise de sensibilidade (com x sem duplicatas) é gerada em results/.
REMOVE_DUPLICATES = True


def ensure_dirs() -> None:
    for d in (DATA_DIR, RESULTS_DIR, FIG_DIR):
        d.mkdir(parents=True, exist_ok=True)


def resolve_data_path() -> Path:
    """Escolhe o CSV a usar.

    Ordem: variável de ambiente WINE_DATA > WineQT.csv > winequality-red.csv.
    """
    env = os.environ.get("WINE_DATA")
    if env:
        p = Path(env)
        if not p.is_absolute():
            p = ROOT / p
        if not p.exists():
            raise FileNotFoundError(f"WINE_DATA aponta para um arquivo inexistente: {p}")
        return p
    for nome in (OFFICIAL_DATASET, FALLBACK_DATASET):
        p = DATA_DIR / nome
        if p.exists():
            return p
    raise FileNotFoundError(
        f"Nenhuma base encontrada em {DATA_DIR}. Coloque {OFFICIAL_DATASET} "
        f"(Kaggle: yasserh/wine-quality-dataset) em data/. Veja data/README.md."
    )


def is_official(path: Path) -> bool:
    return path.name == OFFICIAL_DATASET
