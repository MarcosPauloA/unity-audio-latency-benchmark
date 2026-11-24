// NativeAudioBenchmark.cpp
// Compilacao (MSVC x64): cl /O2 /LD /EHsc /std:c++17 NativeAudioBenchmark.cpp /Fe:NativeAudioBenchmark.dll

#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstring>

#if defined(_WIN32)
    #define API_EXPORT extern "C" __declspec(dllexport)
#else
    #define API_EXPORT extern "C" __attribute__((visibility("default")))
#endif

namespace {

constexpr size_t RING_CAPACITY = 1024; // Potencia de 2 para mascara binaria
constexpr size_t RING_MASK = RING_CAPACITY - 1;
constexpr size_t AUDIO_BLOCK_SIZE = 512;
constexpr float TWO_PI = 6.28318530718f;

struct AudioCommand {
    int32_t eventId;
    float amplitude;
    float frequencyHz;
};

class LockFreeCommandQueue {
public:
    LockFreeCommandQueue() : head_(0), tail_(0) {
        std::memset(buffer_, 0, sizeof(buffer_));
    }

    bool push(const AudioCommand& cmd) noexcept {
        const size_t currentTail = tail_.load(std::memory_order_relaxed);
        const size_t nextTail = (currentTail + 1) & RING_MASK;
        if (nextTail == head_.load(std::memory_order_acquire)) {
            return false; // Buffer cheio
        }
        buffer_[currentTail] = cmd;
        tail_.store(nextTail, std::memory_order_release);
        return true;
    }

    bool pop(AudioCommand& outCmd) noexcept {
        const size_t currentHead = head_.load(std::memory_order_relaxed);
        if (currentHead == tail_.load(std::memory_order_acquire)) {
            return false; // Buffer vazio
        }
        outCmd = buffer_[currentHead];
        head_.store((currentHead + 1) & RING_MASK, std::memory_order_release);
        return true;
    }

    void reset() noexcept {
        head_.store(0, std::memory_order_relaxed);
        tail_.store(0, std::memory_order_relaxed);
    }

private:
    AudioCommand buffer_[RING_CAPACITY];
    alignas(64) std::atomic<size_t> head_;
    alignas(64) std::atomic<size_t> tail_;
};

// Estado estatico pre-alocado (zero alocacoes dinamicas no caminho critico)
LockFreeCommandQueue g_commandQueue;
alignas(32) float g_audioBuffer[AUDIO_BLOCK_SIZE];
float g_sampleRate = 48000.0f;
float g_phase = 0.0f;
bool g_initialized = false;

void synthesizeBlock(float amplitude, float frequencyHz) noexcept {
    const float phaseIncrement = (TWO_PI * frequencyHz) / g_sampleRate;
    for (size_t i = 0; i < AUDIO_BLOCK_SIZE; ++i) {
        g_audioBuffer[i] = amplitude * std::sin(g_phase);
        g_phase += phaseIncrement;
        if (g_phase >= TWO_PI) {
            g_phase -= TWO_PI;
        }
    }
}

} // namespace

API_EXPORT int32_t InitNativeAudioEngine(float sampleRate) {
    if (sampleRate <= 0.0f) {
        return -1;
    }
    g_sampleRate = sampleRate;
    g_phase = 0.0f;
    g_commandQueue.reset();
    std::memset(g_audioBuffer, 0, sizeof(g_audioBuffer));
    g_initialized = true;
    return 0;
}

API_EXPORT int32_t TriggerNativeAudioEvent(int32_t eventId, float amplitude, float frequencyHz) {
    if (!g_initialized) {
        return -1;
    }

    AudioCommand cmd{eventId, amplitude, frequencyHz};
    if (!g_commandQueue.push(cmd)) {
        // Esvazia comando antigo caso a fila atinja capacidade maxima
        AudioCommand discarded{};
        g_commandQueue.pop(discarded);
        g_commandQueue.push(cmd);
    }

    AudioCommand activeCmd{};
    if (g_commandQueue.pop(activeCmd)) {
        synthesizeBlock(activeCmd.amplitude, activeCmd.frequencyHz);
        return 1;
    }
    return 0;
}

API_EXPORT void ShutdownNativeAudioEngine() {
    g_commandQueue.reset();
    g_initialized = false;
}