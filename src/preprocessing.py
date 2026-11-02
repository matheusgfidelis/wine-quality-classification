"""Pré-processamento e engenharia de atributos — Wine Quality.

Base: módulo do Tópico 2 do grupo, com UMA mudança metodológica documentada
(ver `construir_preprocessador`): as features enológicas passam a ser OPT-IN
(antes eram ligadas por padrão no perfil linear), pois o ganho medido foi
desprezível e elas duplicam informação, atrapalhando a interpretação dos
coeficientes.

Regra de ouro anti-vazamento: todo transformador que APRENDE algo dos dados
(Yeo-Johnson, medianas de preenchimento) fica dentro de um Pipeline e é
ajustado somente nos dados de treino de cada dobra.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PowerTransformer

# Colunas candidatas a transformação por forte assimetria à direita.
# Os valores de skew citados no histórico do projeto vêm da winequality-red;
# RECALCULE na base final (notebook 02 faz isso automaticamente).
COLUNAS_ASSIMETRICAS = [
    "chlorides", "residual_sugar", "sulphates",
    "total_sulfur_dioxide", "free_sulfur_dioxide",
]

NOMES_PT = {
    "fixed_acidity": "Acidez fixa",
    "volatile_acidity": "Acidez volátil",
    "citric_acid": "Ácido cítrico",
    "residual_sugar": "Açúcar residual",
    "chlorides": "Cloretos",
    "free_sulfur_dioxide": "SO₂ livre",
    "total_sulfur_dioxide": "SO₂ total",
    "density": "Densidade",
    "ph": "pH",
    "sulphates": "Sulfatos",
    "alcohol": "Álcool",
}


def carregar_dados(caminho) -> pd.DataFrame:
    """Lê o CSV, padroniza nomes de colunas e remove o identificador `Id`.

    Aceita as variações conhecidas: nomes com espaço, coluna `Id` (WineQT) e
    coluna de tipo de vinho (base combinada tinto+branco).
    """
    df = pd.read_csv(caminho)
    df.columns = (df.columns.str.strip().str.lower()
                  .str.replace(" ", "_").str.replace("-", "_"))
    if "id" in df.columns:  # identificador, não é preditor
        df = df.drop(columns="id")
    for col in ("type", "color", "wine_type"):
        if col in df.columns:
            df[col] = (df[col].astype(str).str.lower()
                       .map({"red": 1, "tinto": 1, "white": 0, "branco": 0}))
            df = df.rename(columns={col: "is_tinto"})
            break
    return df


def criar_alvo(df: pd.DataFrame, limiar: int = 7):
    """Retorna (X, y). y=1 -> alta qualidade (quality >= limiar)."""
    if "quality" not in df.columns:
        raise KeyError("coluna 'quality' não encontrada")
    y = (df["quality"] >= limiar).astype(int).rename("alta_qualidade")
    X = df.drop(columns="quality")
    return X, y


def remover_duplicatas(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """Remove linhas idênticas em todas as colunas (rodar ANTES do split)."""
    n0 = len(df)
    out = df.drop_duplicates().reset_index(drop=True)
    if verbose:
        r = n0 - len(out)
        print(f"Duplicatas removidas: {r} de {n0} ({r / n0:.1%}) -> {len(out)} linhas")
    return out


def contar_vazamento_duplicatas(X_train: pd.DataFrame, X_test: pd.DataFrame) -> int:
    """Nº de linhas do teste com cópia exata (nas features) no treino."""
    chave_tr = set(map(tuple, X_train.round(8).to_numpy()))
    return int(sum(tuple(r) in chave_tr for r in X_test.round(8).to_numpy()))


class LogAssimetricas(BaseEstimator, TransformerMixin):
    """log(1+x) nas colunas assimétricas. Mantido só para COMPARAÇÃO.

    Para valores pequenos (ex.: cloretos ~0,08) log(1+x) ≈ x e quase não
    transforma; o Yeo-Johnson estima um expoente por coluna e resolve melhor.
    """

    def __init__(self, colunas=None):
        self.colunas = colunas

    def fit(self, X, y=None):
        alvo = self.colunas if self.colunas is not None else COLUNAS_ASSIMETRICAS
        self.colunas_ = [c for c in alvo if c in X.columns]
        return self

    def transform(self, X):
        X = X.copy()
        for c in self.colunas_:
            X[c] = np.log1p(X[c])
        return X


class FeaturesEnologicas(BaseEstimator, TransformerMixin):
    """Atributos derivados com sentido enológico (opt-in).

    As medianas de preenchimento (para razões com denominador zero) são
    aprendidas no `fit` — recalculá-las no `transform` vazaria o teste.
    """

    def fit(self, X, y=None):
        self.medianas_ = self._criar(X).median(numeric_only=True)
        return self

    def transform(self, X):
        return self._criar(X).fillna(self.medianas_)

    @staticmethod
    def _criar(X):
        X = X.copy()
        c = set(X.columns)
        if {"fixed_acidity", "volatile_acidity"} <= c:
            X["acidez_total"] = X.fixed_acidity + X.volatile_acidity
            X["acidez_razao"] = X.fixed_acidity / X.volatile_acidity.replace(0, np.nan)
        if {"free_sulfur_dioxide", "total_sulfur_dioxide"} <= c:
            X["so2_ligado"] = X.total_sulfur_dioxide - X.free_sulfur_dioxide
            X["so2_razao_livre"] = X.free_sulfur_dioxide / X.total_sulfur_dioxide.replace(0, np.nan)
        if {"alcohol", "density"} <= c:
            X["alcool_densidade"] = X.alcohol / X.density
        if {"residual_sugar", "alcohol"} <= c:
            X["acucar_alcool"] = X.residual_sugar / X.alcohol
        if {"sulphates", "chlorides"} <= c:
            X["sulfatos_cloretos"] = X.sulphates / X.chlorides.replace(0, np.nan)
        return X.replace([np.inf, -np.inf], np.nan)


def construir_preprocessador(perfil: str = "linear", features_novas: bool = False) -> Pipeline:
    """Pipeline de pré-processamento por família de modelo.

    perfil='linear' -> Yeo-Johnson com padronização (LogReg, SVM, KNN)
    perfil='arvore' -> sem transformação (DT, RF, GBM): árvores dividem por
                       limiar, logo transformações monotônicas não mudam os cortes.
    features_novas  -> opt-in (padrão False). Ver docstring do módulo.
    """
    if perfil not in ("linear", "arvore"):
        raise ValueError("perfil deve ser 'linear' ou 'arvore'")
    passos: list = []
    if features_novas:
        passos.append(("features", FeaturesEnologicas()))
    if perfil == "linear":
        passos.append(("potencia", PowerTransformer(method="yeo-johnson", standardize=True)))
    if not passos:
        passos.append(("passa", "passthrough"))
    return Pipeline(passos)
