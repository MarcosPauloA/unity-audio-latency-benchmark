# analisar_resultados.py
import os
import sys
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

# Configuracao grafica para padrao cientifico ACM (fontes vetoriais TrueType)
plt.rcParams.update({
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "font.family": "serif",
    "font.size": 9,
    "axes.titlesize": 9.5,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "axes.linewidth": 0.8,
})

CSV_C1 = "Benchmark_Cenario1_Nominal.csv"
CSV_C2 = "Benchmark_Cenario2_GC.csv"


def fmt_br(valor: float, casas: int = 3) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def cliffs_delta(x: np.ndarray, y: np.ndarray) -> tuple[float, str]:
    """Calcula exatamente o Delta de Cliff conforme Romano et al. (2006)."""
    diff = x[:, None] - y[None, :]
    maior = np.sum(diff > 0)
    menor = np.sum(diff < 0)
    delta = (maior - menor) / (len(x) * len(y))

    abs_d = abs(delta)
    if abs_d < 0.147:
        mag = "Desprezível"
    elif abs_d < 0.33:
        mag = "Pequeno"
    elif abs_d < 0.474:
        mag = "Médio"
    else:
        mag = "Grande"
    return float(delta), mag


def calcular_descritivas(serie: np.ndarray) -> dict:
    q1, mediana, q3 = np.percentile(serie, [25, 50, 75])
    return {
        "media": float(np.mean(serie)),
        "mediana": float(mediana),
        "iqr": float(q3 - q1),
        "jitter": float(np.std(serie, ddof=1)),
        "p99": float(np.percentile(serie, 99)),
        "max": float(np.max(serie)),
    }


def gerar_grafico_boxplot(a_c1, b_c1, a_c2, b_c2, saida="fig_boxplot_latencia.pdf"):
    fig, ax = plt.subplots(figsize=(4.6, 3.2))

    dados = [a_c1, b_c1, a_c2, b_c2]
    rotulos = [
        "Arq. A\n(Nominal)",
        "Arq. B\n(Nominal)",
        "Arq. A\n(Estresse GC)",
        "Arq. B\n(Estresse GC)",
    ]

    bp = ax.boxplot(
        dados,
        labels=rotulos,
        patch_artist=True,
        showfliers=True,
        widths=0.48,
        flierprops=dict(marker="o", markersize=2.5, alpha=0.45, markerfacecolor="#555555", markeredgecolor="none"),
        medianprops=dict(color="#111111", linewidth=1.4),
        whiskerprops=dict(color="#333333", linewidth=0.9),
        capprops=dict(color="#333333", linewidth=0.9),
    )

    cores = ["#4C72B0", "#55A868", "#C44E52", "#8172B3"]
    for patch, cor in zip(bp["boxes"], cores):
        patch.set_facecolor(cor)
        patch.set_alpha(0.75)
        patch.set_edgecolor("#222222")
        patch.set_linewidth(0.8)

    ax.set_yscale("log")
    ax.set_ylabel("Latência de Despacho (ms)\n[Escala Logarítmica]")
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.55)
    ax.set_axisbelow(True)
    ax.axvline(x=2.5, color="#666666", linestyle=":", linewidth=0.9)

    fig.savefig(saida, format="pdf", bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print(f"[OK] Gráfico salvo: {saida}")


def gerar_grafico_serie_temporal(iteracoes, a_c2, b_c2, saida="fig_serietemporal_gc.pdf"):
    fig, ax = plt.subplots(figsize=(4.6, 3.1))

    ax.plot(iteracoes, a_c2, label="Arq. A: Gerenciada (C#)", color="#C44E52", linewidth=0.75, alpha=0.9)
    ax.plot(iteracoes, b_c2, label="Arq. B: Plugin Nativo (C++)", color="#2B6CB0", linewidth=0.85, alpha=0.95)

    ax.set_xlabel("Iteração Experimental")
    ax.set_ylabel("Latência de Despacho (ms)")
    ax.set_xlim(1, len(iteracoes))
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", frameon=True, framealpha=0.92)

    fig.savefig(saida, format="pdf", bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print(f"[OK] Gráfico salvo: {saida}")

def main():
    for arq in (CSV_C1, CSV_C2):
        if not os.path.exists(arq):
            print(f"[ERRO] Arquivo não encontrado: {arq}")
            sys.exit(1)

    df_c1 = pd.read_csv(CSV_C1)
    df_c2 = pd.read_csv(CSV_C2)

    a_c1 = df_c1["ArqA_ms"].to_numpy(dtype=float)
    b_c1 = df_c1["ArqB_ms"].to_numpy(dtype=float)
    a_c2 = df_c2["ArqA_ms"].to_numpy(dtype=float)
    b_c2 = df_c2["ArqB_ms"].to_numpy(dtype=float)

    grupos = [
        ("Arq. A: Gerenciada (C# AudioSource)", "Cenário 1: Nominal", a_c1),
        ("Arq. B: Híbrida (C++ P/Invoke DLL)", "Cenário 1: Nominal", b_c1),
        ("Arq. A: Gerenciada (C# AudioSource)", "Cenário 2: Estresse GC", a_c2),
        ("Arq. B: Híbrida (C++ P/Invoke DLL)", "Cenário 2: Estresse GC", b_c2),
    ]

    print("\n================ 1. ESTATISTICAS DESCRITIVAS (TABELA 3 - LATEX) ================")
    for nome, cen, dados in grupos:
        d = calcular_descritivas(dados)
        w_stat, p_norm = stats.shapiro(dados)
        print(
            f"{nome} & {cen} & {fmt_br(d['media'])} & {fmt_br(d['mediana'])} & "
            f"{fmt_br(d['iqr'])} & {fmt_br(d['jitter'])} & {fmt_br(d['p99'])} & {fmt_br(d['max'])} \\\\"
        )
        print(f"   -> Shapiro-Wilk: W = {w_stat:.4f}, p = {p_norm:.3e}")

    # Reducoes percentuais para o Abstract e Secao 5
    d_a1, d_b1 = calcular_descritivas(a_c1), calcular_descritivas(b_c1)
    d_a2 = calcular_descritivas(a_c2)
    red_media_c1 = (1 - d_b1["media"] / d_a1["media"]) * 100
    red_mediana_c1 = (1 - d_b1["mediana"] / d_a1["mediana"]) * 100
    red_jitter_c1 = (1 - d_b1["jitter"] / d_a1["jitter"]) * 100
    aum_jitter_a = ((d_a2["jitter"] / d_a1["jitter"]) - 1) * 100

    print("\n================ 2. VARIACOES PERCENTUAIS (PARA O TEXTO) ================")
    print(f"Redução média (C1, B vs A):   {fmt_br(red_media_c1, 1)}%")
    print(f"Redução mediana (C1, B vs A): {fmt_br(red_mediana_c1, 1)}%")
    print(f"Redução jitter (C1, B vs A):  {fmt_br(red_jitter_c1, 1)}%")
    print(f"Aumento jitter Arq. A (C2 vs C1): {fmt_br(aum_jitter_a, 1)}%")

    print("\n================ 3. MANN-WHITNEY U E CLIFF'S DELTA (TABELA 4 - LATEX) ================")
    comparacoes = [
        ("Cenário 1 (A vs. B)", a_c1, b_c1),
        ("Cenário 2 (A vs. B)", a_c2, b_c2),
        ("Arq. A (C1 vs. C2)", a_c1, a_c2),
        ("Arq. B (C1 vs. C2)", b_c1, b_c2),
    ]

    for rotulo, g1, g2 in comparacoes:
        u_stat, p_val = stats.mannwhitneyu(g1, g2, alternative="two-sided")
        delta, mag = cliffs_delta(g1, g2)
        p_str = "$< 0,001$" if p_val < 0.001 else fmt_br(p_val, 4)
        print(f"{rotulo} & {u_stat:.0f} & {p_str} & {fmt_br(delta, 3)} & {mag} \\\\")

    print("\n================ 4. GERACAO DE GRAFICOS VETORIAIS (PDF) ================")
    gerar_grafico_boxplot(a_c1, b_c1, a_c2, b_c2)
    gerar_grafico_serie_temporal(df_c2["Iteracao"].to_numpy(), a_c2, b_c2)


if __name__ == "__main__":
    main()