# pyrefly: ignore [missing-import]
import torch

# Patch torch.load globally before importing rvc_python or other libraries
# to bypass weights_only restrictions on newer PyTorch versions.
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    try:
        return _original_torch_load(*args, **kwargs)
    except TypeError:
        kwargs.pop('weights_only', None)
        return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

import os
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import soundfile as sf
# pyrefly: ignore [missing-import]
from kokoro import KPipeline
# pyrefly: ignore [missing-import]
from rvc_python.infer import RVCInference

# ==========================================
# CONFIGURAÇÕES DO PROJETO
# ==========================================

TEXTO = """
E você já parou para pensar na diferença entre como Deus criou todo o universo... e como Ele criou você?

Para formar as estrelas, os oceanos e galáxias infinitas, bastou uma única palavra. Ele apenas ordenou, e tudo passou a existir.

Mas com o ser humano... o Criador fez algo completamente diferente.

Deus não usou apenas a voz. Ele Se inclinou sobre a terra, esculpiu cada detalhe do nosso ser com as Suas próprias mãos e soprou diretamente em nós o Seu próprio fôlego de vida.

Você não é um fruto do acaso; você carrega o sopro e o amor de Deus dentro de você.
"""

VOZ_KOKORO = 'pm_alex'  # Voz masculina em Português como guia (melhor para converter para Isaac Bardavid)
MODELO_PTH = r"C:\Users\Usuario\tts-rvc\Voice Models\ISAAC BARDAVID - Weights Model\isaac_bardavid_model.pth"

# ==========================================
# CONFIGURAÇÃO DE DESTINO DO ÁUDIO
# ==========================================
BASE_DIR = r"D:\Documents\YT Viva o Secreto"
PASTA_NUMERO = "02"  # Altere para "02", "03", etc. a cada nova geração
NOME_ARQUIVO = "narracao_.wav"

TEMP_AUDIO_TTS = "temp_guia.wav"

PASTA_DESTINO = os.path.join(BASE_DIR, PASTA_NUMERO)
ARQUIVO_FINAL = os.path.join(PASTA_DESTINO, NOME_ARQUIVO)


def gerar_tts():
    """Gera o áudio base (guia) usando Kokoro TTS em Português."""
    print("⏳ 1/2: Gerando áudio guia com Kokoro (Português)...")
    pipeline = KPipeline(lang_code='p')
    
    # Processa o texto em partes (quebras de linha/parágrafos)
    generator = pipeline(
        TEXTO, 
        voice=VOZ_KOKORO, 
        speed=1.0,
        split_pattern=r'\n+'
    )
    
    audio_acumulado = []
    for graphemes, phonemes, audio in generator:
        audio_acumulado.append(audio)
        
    # Concatena e salva em WAV (24000 Hz)
    audio_final = np.concatenate(audio_acumulado)
    sf.write(TEMP_AUDIO_TTS, audio_final, 24000)
    print(f"✅ Áudio guia gerado com sucesso: {TEMP_AUDIO_TTS}")


def aplicar_rvc():
    """Aplica o modelo do Isaac Bardavid via RVC."""
    print("🧠 2/2: Convertendo a voz com RVC (Isaac Bardavid)...")
    
    out_path = ARQUIVO_FINAL
    try:
        os.makedirs(PASTA_DESTINO, exist_ok=True)
    except Exception as e:
        print(f"⚠️ Não foi possível criar {PASTA_DESTINO}: {e}. Salvando na pasta atual.")
        out_path = "narracao_isaac_bardavid.wav"

    # Verifica se há suporte a GPU Nvidia (CUDA)
    device = "cuda:0" if os.system("nvidia-smi") == 0 else "cpu"
    print(f"🖥️ Usando dispositivo: {device}")
    
    rvc = RVCInference(device=device)
    
    # Carrega o modelo (RVC detecta automaticamente o arquivo .index no mesmo diretório)
    rvc.load_model(MODELO_PTH)
    
    # Executa a conversão
    rvc.infer_file(
        input_path=TEMP_AUDIO_TTS,
        output_path=out_path
    )
    
    # Se gerou na pasta de destino, também salva uma cópia local por conveniência
    if out_path != "narracao_isaac_bardavid.wav":
        try:
            import shutil
            shutil.copy(out_path, "narracao_isaac_bardavid.wav")
        except Exception:
            pass

    # Remove arquivo guia temporário
    if os.path.exists(TEMP_AUDIO_TTS):
        os.remove(TEMP_AUDIO_TTS)
        
    print(f"\n✨ SUCESSO! A narração final foi salva em: {os.path.abspath(out_path)}")


if __name__ == "__main__":
    gerar_tts()
    aplicar_rvc()
