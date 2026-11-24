using UnityEngine.InputSystem;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using UnityEngine;

public class AudioBenchmarkRunner : MonoBehaviour
{
    [Header("Configuracao de Audio (Arquitetura A)")]
    public AudioSource audioSource;

    [Header("Parametros do Experimento")]
    public bool cenarioEstresseGC = false;
    public int iteracoesWarmup = 50;
    public int iteracoesValidas = 1000;
    public int alocacaoGCBytesPorFrame = 65536; // 64 KB por quadro no Cenario 2

    [DllImport("NativeAudioBenchmark", CallingConvention = CallingConvention.Cdecl)]
    private static extern int InitNativeAudioEngine(float sampleRate);

    [DllImport("NativeAudioBenchmark", CallingConvention = CallingConvention.Cdecl)]
    private static extern int TriggerNativeAudioEvent(int eventId, float amplitude, float frequencyHz);

    [DllImport("NativeAudioBenchmark", CallingConvention = CallingConvention.Cdecl)]
    private static extern void ShutdownNativeAudioEngine();

    private bool executando = false;
    private bool nativeInicializado = false;

    void Start()
    {
        int status = InitNativeAudioEngine(AudioSettings.outputSampleRate);
        nativeInicializado = (status == 0);
        if (!nativeInicializado)
        {
            UnityEngine.Debug.LogError("Falha ao inicializar NativeAudioBenchmark.dll.");
        }
    }

    void Update()
         {
            if (Keyboard.current != null && Keyboard.current.spaceKey.wasPressedThisFrame && !executando && nativeInicializado)
            {
                StartCoroutine(ExecutarExperimentoCompleto());
            }
    }

    void OnDestroy()
    {
        if (nativeInicializado)
        {
            ShutdownNativeAudioEngine();
            nativeInicializado = false;
        }
    }

    private IEnumerator ExecutarExperimentoCompleto()
    {
        executando = true;
        int totalIteracoes = iteracoesWarmup + iteracoesValidas;
        double ticksParaMs = 1000.0 / Stopwatch.Frequency;

        List<double> amostrasArqA = new List<double>(iteracoesValidas);
        List<double> amostrasArqB = new List<double>(iteracoesValidas);

        UnityEngine.Debug.Log($"Iniciando Benchmark (Estresse GC: {cenarioEstresseGC})...");

        // --- Limpeza inicial de heap antes da Bateria A ---
        GC.Collect();
        GC.WaitForPendingFinalizers();
        yield return new WaitForSeconds(0.5f);

        // --- BATERIA 1: Arquitetura A (Gerenciada - C# AudioSource) ---
        for (int i = 0; i < totalIteracoes; i++)
        {
            if (cenarioEstresseGC)
            {
                SimularPressaoDeMemoria();
            }

            long tIni = Stopwatch.GetTimestamp();
            audioSource.Play();
            long tFim = Stopwatch.GetTimestamp();

            if (i >= iteracoesWarmup)
            {
                amostrasArqA.Add((tFim - tIni) * ticksParaMs);
            }

            yield return null;
        }

        // --- Limpeza inicial de heap antes da Bateria B ---
        audioSource.Stop();
        GC.Collect();
        GC.WaitForPendingFinalizers();
        yield return new WaitForSeconds(0.5f);

        // --- BATERIA 2: Arquitetura B (Plugin Nativo - C++ DLL via P/Invoke) ---
        for (int i = 0; i < totalIteracoes; i++)
        {
            if (cenarioEstresseGC)
            {
                SimularPressaoDeMemoria();
            }

            long tIni = Stopwatch.GetTimestamp();
            TriggerNativeAudioEvent(i, 0.5f, 440.0f);
            long tFim = Stopwatch.GetTimestamp();

            if (i >= iteracoesWarmup)
            {
                amostrasArqB.Add((tFim - tIni) * ticksParaMs);
            }

            yield return null;
        }

        SalvarCSV(amostrasArqA, amostrasArqB);
        executando = false;
    }

    private void SimularPressaoDeMemoria()
    {
        // Gera alocacoes temporarias na heap gerenciada para acionar varreduras do GC
        byte[] blocoTemporario = new byte[alocacaoGCBytesPorFrame];
        blocoTemporario[0] = 1;
        blocoTemporario[blocoTemporario.Length - 1] = 2;
    }

    private void SalvarCSV(List<double> arqA, List<double> arqB)
    {
        string nomeCenario = cenarioEstresseGC ? "Cenario2_GC" : "Cenario1_Nominal";
        string caminho = Path.Combine(Application.dataPath, $"Benchmark_{nomeCenario}.csv");

        using (StreamWriter sw = new StreamWriter(caminho))
        {
            sw.WriteLine("Iteracao,ArqA_ms,ArqB_ms");
            for (int i = 0; i < arqA.Count; i++)
            {
                string valA = arqA[i].ToString("F6", CultureInfo.InvariantCulture);
                string valB = arqB[i].ToString("F6", CultureInfo.InvariantCulture);
                sw.WriteLine($"{i + 1},{valA},{valB}");
            }
        }

        UnityEngine.Debug.Log($"Coleta finalizada! Arquivo salvo em: {caminho}");
    }
}