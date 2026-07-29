// JavaScript Client Controller for TTS-RVC Studio

document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const narrationText = document.getElementById('narration-text');
    const charCount = document.getElementById('char-count');
    const btnRestoreDefault = document.getElementById('btn-restore-default');
    
    const voiceSettingsToggle = document.getElementById('voice-settings-toggle');
    const voiceSettingsContent = document.getElementById('voice-settings-content');
    const voiceChevron = document.getElementById('voice-chevron');
    const selectedModelBadge = document.getElementById('selected-model-badge');
    
    const modelSelect = document.getElementById('model-select');
    const kokoroLangFilter = document.getElementById('kokoro-lang-filter');
    const ttsVoiceSelect = document.getElementById('tts-voice-select');
    const voicesCountBadge = document.getElementById('voices-count-badge');
    
    const btnGenerate = document.getElementById('btn-generate');
    const btnTextContent = document.getElementById('btn-text-content');
    const btnSpinner = document.getElementById('btn-spinner');
    const processStatusText = document.getElementById('process-status-text');
    
    const terminalLogs = document.getElementById('terminal-logs');
    const btnClearTerminal = document.getElementById('btn-clear-terminal');
    
    const resultCard = document.getElementById('result-card');
    const btnDownloadAudio = document.getElementById('btn-download-audio');
    
    const nativeAudio = document.getElementById('native-audio-element');
    const playBtn = document.getElementById('play-btn');
    const playIcon = document.getElementById('play-icon');
    const audioTimeCurrent = document.getElementById('audio-time-current');
    const audioTimeDuration = document.getElementById('audio-time-duration');
    const audioProgressBarContainer = document.getElementById('audio-progress-bar-container');
    const audioProgressBar = document.getElementById('audio-progress-bar');
    const muteBtn = document.getElementById('mute-btn');
    const volumeIcon = document.getElementById('volume-icon');
    const volumeSlider = document.getElementById('volume-slider');

    let defaultScriptText = "";
    let allKokoroVoices = [];

    // 1. Initial Setup
    init();

    async function init() {
        setupEventListeners();
        await loadDefaults();
        await loadKokoroVoices();
        await loadModels();
    }

    // 2. Load Defaults from Server
    async function loadDefaults() {
        try {
            const res = await fetch('/api/defaults');
            if (res.ok) {
                const data = await res.json();
                if (data.default_text) {
                    defaultScriptText = data.default_text;
                    if (!narrationText.value.trim()) {
                        narrationText.value = defaultScriptText;
                    }
                }
            }
        } catch (e) {
            console.warn("Não foi possível carregar valores padrão:", e);
        }
        updateCharCount();
    }

    // 3. Load Kokoro Voices Catalog (54 voices)
    async function loadKokoroVoices() {
        try {
            const res = await fetch('/api/kokoro_voices');
            if (res.ok) {
                allKokoroVoices = await res.json();
                renderKokoroVoices();
                log(`Carregadas 54 vozes oficiais do Kokoro TTS.`, "info");
            }
        } catch (e) {
            console.warn("Erro ao buscar vozes Kokoro:", e);
        }
    }

    function renderKokoroVoices() {
        const selectedLang = kokoroLangFilter.value;
        ttsVoiceSelect.innerHTML = '';

        let filtered = allKokoroVoices;
        if (selectedLang !== 'all') {
            filtered = allKokoroVoices.filter(v => v.lang === selectedLang);
        }

        voicesCountBadge.textContent = `${filtered.length} vozes`;

        filtered.forEach((v) => {
            const opt = document.createElement('option');
            opt.value = v.id;
            opt.textContent = `${v.name} [${v.langLabel}]`;
            
            // Preselect 'pm_santa' as default for Portuguese
            if (v.id === 'pm_santa') {
                opt.selected = true;
            }
            ttsVoiceSelect.appendChild(opt);
        });

        if (ttsVoiceSelect.options.length > 0 && !ttsVoiceSelect.value) {
            ttsVoiceSelect.selectedIndex = 0;
        }
    }

    // 4. Load RVC Models
    async function loadModels() {
        try {
            const res = await fetch('/api/models');
            if (!res.ok) throw new Error("Erro ao buscar modelos.");
            const models = await res.json();
            
            modelSelect.innerHTML = '';
            if (models.length === 0) {
                modelSelect.innerHTML = '<option value="" disabled selected>Nenhum modelo RVC encontrado em "Voice Models"</option>';
                log("Aviso: Nenhum modelo RVC foi detectado na pasta Voice Models.", "warn");
                return;
            }

            models.forEach((m, idx) => {
                const opt = document.createElement('option');
                opt.value = m.name;
                opt.textContent = m.name;
                if (idx === 0) {
                    opt.selected = true;
                    selectedModelBadge.textContent = m.name;
                }
                modelSelect.appendChild(opt);
            });

            if (models.length > 0) {
                selectedModelBadge.textContent = modelSelect.value;
            }

            log(`Detectados ${models.length} modelos de voz RVC.`, "info");
        } catch (e) {
            log(`Erro ao carregar modelos: ${e.message}`, "error");
        }
    }

    // 5. Event Listeners
    function setupEventListeners() {
        // Textarea input
        narrationText.addEventListener('input', updateCharCount);

        // Restore default text
        btnRestoreDefault.addEventListener('click', () => {
            if (defaultScriptText) {
                narrationText.value = defaultScriptText;
                updateCharCount();
                log("Texto padrão do roteiro carregado.", "info");
            }
        });

        // Kokoro Language Filter change
        kokoroLangFilter.addEventListener('change', () => {
            renderKokoroVoices();
            const langName = kokoroLangFilter.options[kokoroLangFilter.selectedIndex].text;
            log(`Filtro por idioma alterado para: ${langName}`, "info");
        });

        // Voice Settings Toggle
        let settingsOpen = false;
        voiceSettingsToggle.addEventListener('click', () => {
            settingsOpen = !settingsOpen;
            if (settingsOpen) {
                voiceSettingsContent.classList.remove('hidden');
                voiceChevron.style.transform = 'rotate(180deg)';
            } else {
                voiceSettingsContent.classList.add('hidden');
                voiceChevron.style.transform = 'rotate(0deg)';
            }
        });

        modelSelect.addEventListener('change', () => {
            selectedModelBadge.textContent = modelSelect.value;
        });

        // Terminal Clear
        btnClearTerminal.addEventListener('click', () => {
            terminalLogs.innerHTML = '<div class="text-slate-500">[PRONTO] Terminal limpo.</div>';
        });

        // Generate Audio Button
        btnGenerate.addEventListener('click', generateNarration);

        // Audio Player Controls
        setupPlayerControls();
    }

    function updateCharCount() {
        charCount.textContent = narrationText.value.length;
    }

    function log(message, level = 'info') {
        const time = new Date().toLocaleTimeString();
        const div = document.createElement('div');
        
        let colorClass = 'text-slate-300';
        if (level === 'success') colorClass = 'text-emerald-400 font-semibold';
        if (level === 'error') colorClass = 'text-red-400 font-semibold';
        if (level === 'warn') colorClass = 'text-amber-400';
        if (level === 'info') colorClass = 'text-cyan-300';

        div.className = `${colorClass}`;
        div.textContent = `[${time}] ${message}`;
        terminalLogs.appendChild(div);
        terminalLogs.scrollTop = terminalLogs.scrollHeight;
    }

    // 6. Perform Audio Generation
    async function generateNarration() {
        const text = narrationText.value.trim();
        if (!text) {
            alert("Por favor, insira o texto que deseja narrar.");
            log("Erro: Texto da narração vazio.", "error");
            return;
        }

        const modelName = modelSelect.value;
        if (!modelName) {
            alert("Nenhum modelo RVC selecionado.");
            log("Erro: Nenhum modelo RVC selecionado.", "error");
            return;
        }

        const selectedVoice = ttsVoiceSelect.value || "pm_santa";

        // Set Loading State
        btnGenerate.disabled = true;
        btnTextContent.classList.add('hidden');
        btnSpinner.classList.remove('hidden');
        processStatusText.textContent = `1/2: Gerando guia Kokoro (${selectedVoice})...`;

        log("Iniciando geração de narração...", "info");
        log(`Modelo RVC selecionado: ${modelName}`, "info");
        log(`Voz Guia Kokoro: ${selectedVoice}`, "info");
        log(`Texto: "${text.substring(0, 45)}..." (${text.length} caracteres)`, "info");

        const payload = {
            text: text,
            tts_engine: "kokoro",
            tts_voice: selectedVoice,
            tts_speed: 0.9,
            model_name: modelName
        };

        try {
            setTimeout(() => {
                if (btnGenerate.disabled) {
                    processStatusText.textContent = `2/2: Convertendo voz com modelo (${modelName})...`;
                    log("Áudio guia OK. Aplicando conversão RVC...", "info");
                }
            }, 3000);

            const res = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.error || "Erro no servidor ao processar o áudio.");
            }

            const data = await res.json();

            log("PROCESSO CONCLUÍDO COM SUCESSO! ✨", "success");
            log(`Áudio gerado disponível para escuta e download.`, "success");

            nativeAudio.src = `/audio/${data.filename}`;
            nativeAudio.load();

            btnDownloadAudio.href = `/audio/${data.filename}`;
            btnDownloadAudio.download = `narracao_${modelName.toLowerCase().replace(/\s+/g, '_')}.wav`;

            resultCard.classList.remove('hidden');
            resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        } catch (e) {
            console.error(e);
            log(`ERRO: ${e.message}`, "error");
            alert(`Falha na geração: ${e.message}`);
        } finally {
            btnGenerate.disabled = false;
            btnTextContent.classList.remove('hidden');
            btnSpinner.classList.add('hidden');
        }
    }

    // 7. Audio Player Logic
    function setupPlayerControls() {
        playBtn.addEventListener('click', () => {
            if (nativeAudio.paused) {
                nativeAudio.play();
                playIcon.setAttribute('data-lucide', 'pause');
            } else {
                nativeAudio.pause();
                playIcon.setAttribute('data-lucide', 'play');
            }
            lucide.createIcons();
        });

        nativeAudio.addEventListener('timeupdate', () => {
            const cur = nativeAudio.currentTime || 0;
            const dur = nativeAudio.duration || 0;
            audioTimeCurrent.textContent = formatTime(cur);
            audioTimeDuration.textContent = formatTime(dur);
            const pct = dur > 0 ? (cur / dur) * 100 : 0;
            audioProgressBar.style.width = `${pct}%`;
        });

        nativeAudio.addEventListener('ended', () => {
            playIcon.setAttribute('data-lucide', 'play');
            lucide.createIcons();
            audioProgressBar.style.width = '0%';
            audioTimeCurrent.textContent = '0:00';
        });

        audioProgressBarContainer.addEventListener('click', (e) => {
            const rect = audioProgressBarContainer.getBoundingClientRect();
            const pos = (e.clientX - rect.left) / rect.width;
            if (nativeAudio.duration) {
                nativeAudio.currentTime = pos * nativeAudio.duration;
            }
        });

        muteBtn.addEventListener('click', () => {
            nativeAudio.muted = !nativeAudio.muted;
            volumeIcon.setAttribute('data-lucide', nativeAudio.muted ? 'volume-x' : 'volume-2');
            lucide.createIcons();
        });

        volumeSlider.addEventListener('input', () => {
            nativeAudio.volume = volumeSlider.value;
        });
    }

    function formatTime(sec) {
        const m = Math.floor(sec / 60);
        const s = Math.floor(sec % 60);
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    }
});
