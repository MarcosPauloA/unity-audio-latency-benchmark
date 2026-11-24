# Impacto Arquitetural no Desempenho de Tempo Real: Benchmark de Latência de Áudio na Unity

Pacote de replicação oficial do artigo **"Impacto Arquitetural no Desempenho de Tempo Real: Um Benchmark de Latência de Áudio entre Código Gerenciado e Plugins Nativos em Motores de Jogos"** (PCC509 -- Engenharia de Software, Universidade Federal de Lavras).

## 1. Descrição do Conteúdo

Este repositório reúne todos os artefatos necessários para auditar e reproduzir o experimento controlado comparando duas arquiteturas de despacho de áudio na **Unity 6 LTS**:
- **Arquitetura A (Gerenciada):** Subsistema nativo padrão em C# (`AudioSource.Play()`).
- **Arquitetura B (Híbrida / Plugin Nativo):** Biblioteca dinâmica compilada em C++17 (`NativeAudioBenchmark.dll`) invocada via *P/Invoke* (`[DllImport]`), utilizando fila circular atômica *lock-free* e *buffer* pré-alocado fora da *heap* gerenciada.

O pacote contém o código-fonte em C++17 e C#, os conjuntos de dados brutos coletados ($N = 1.000$ amostras válidas por bateria, 4.000 medições no total), o *pipeline* em Python para testes estatísticos não paramétricos e geração dos gráficos vetoriais, além da versão final do artigo.

## 2. Utilizado Usando:

### Hardware de Referência (Ambiente Original)
- **CPU:** AMD Ryzen 7 2700 (8 núcleos, 16 *threads*)
- **RAM:** 16 GB DDR4
- **GPU:** AMD Radeon RX 9060 XT (16 GB VRAM)
- **Sistema Operacional:** Windows 11 (64 bits)

### Software
- **Unity Editor:** `6000.3.23f1 LTS` (Template *3D Built-In Render Pipeline* com *Input System* ativo)
- **Compilador C++:** Microsoft Visual Studio 2022 (`MSVC C++17`, x64)
- **Python:** `3.11+` com bibliotecas listadas em `analysis/requirements.txt` (`pandas`, `numpy`, `scipy`, `matplotlib`, `lizard==1.26.1`)


    └── figures/
        ├── fig_boxplot_latencia.pdf       # Figura 3 do artigo (Boxplot em escala logarítmica)
        └── fig_serietemporal_gc.pdf       # Figura 4 do artigo (Série temporal do Cenário 2)
