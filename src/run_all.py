"""Executa tudo: EDA (figuras), modelagem, sensibilidade e relatório.

    python -m src.run_all
"""
from __future__ import annotations

import time

import matplotlib
matplotlib.use("Agg")  # execução em script: sem janelas

from . import config, eda, report, train
from .preprocessing import carregar_dados


def main():
    config.ensure_dirs()
    caminho = config.resolve_data_path()
    print("=" * 70)
    print(f"BASE USADA: {caminho.name}", "(oficial)" if config.is_official(caminho)
          else f"(ATENÇÃO: não é a base oficial {config.OFFICIAL_DATASET}; execução de ENSAIO)")
    print("=" * 70)
    df = carregar_dados(caminho)
    resumo = eda.resumo_estrutural(df)
    eda.distribuicao_alvo(df); eda.boxplots_por_classe(df); eda.histogramas(df); eda.correlacoes(df)
    t0 = time.time()
    r = train.executar(df, remover_dup=config.REMOVE_DUPLICATES)
    sens = train.sensibilidade_duplicatas(df)
    train.salvar_resultados(r, sens, resumo, caminho)
    report.gerar_tudo()
    print(f"\nConcluído em {time.time() - t0:.0f}s. Veja results/ e docs/.")


if __name__ == "__main__":
    main()
