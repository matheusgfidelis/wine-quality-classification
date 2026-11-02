"""Compara WineQT.csv com winequality-red.csv (precisa dos dois em data/).

    python -m src.compare_datasets

Responde: WineQT é subconjunto da winequality-red? Quantas duplicatas cada uma
tem? Como diferem as distribuições de nota? Resultado em results/comparacao_bases.md.
"""
from __future__ import annotations

import pandas as pd

from . import config
from .preprocessing import carregar_dados


def main():
    a, b = config.DATA_DIR / config.OFFICIAL_DATASET, config.DATA_DIR / config.FALLBACK_DATASET
    faltam = [p.name for p in (a, b) if not p.exists()]
    if faltam:
        raise SystemExit(f"Arquivo(s) ausente(s) em data/: {faltam}. Coloque os dois e rode de novo.")
    qt, red = carregar_dados(a), carregar_dados(b)
    cols = [c for c in red.columns if c in qt.columns]
    key = lambda d: d[cols].round(6).apply(tuple, axis=1)
    k_red = set(key(red))
    em_red = key(qt).isin(k_red)
    q = pd.DataFrame({"WineQT": qt.quality.value_counts().sort_index(),
                      "red": red.quality.value_counts().sort_index()})
    q["WineQT_<=_red"] = q["WineQT"] <= q["red"]
    linhas = [
        "# Comparação entre bases", "",
        f"- WineQT: {qt.shape[0]} linhas, {qt.shape[1]} colunas (sem Id); duplicatas exatas: {int(qt.duplicated().sum())}",
        f"- winequality-red: {red.shape[0]} linhas, {red.shape[1]} colunas; duplicatas exatas: {int(red.duplicated().sum())}",
        f"- Linhas da WineQT que existem na red (comparando todas as colunas): {int(em_red.sum())} de {len(qt)}",
        f"- Subconjunto? {'SIM, todas as linhas da WineQT existem na red' if em_red.all() else 'NÃO totalmente'}", "",
        "## Contagem por nota", q.to_string()]
    config.ensure_dirs()
    (config.RESULTS_DIR / "comparacao_bases.md").write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))


if __name__ == "__main__":
    main()
