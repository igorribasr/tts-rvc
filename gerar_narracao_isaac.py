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
Porque no mundo espiritual... é assim que os demônios tentam dominar você.


Satanás levou com ele um terço dos anjos... mas a Bíblia nunca disse que eles ficaram sem limites.


Apocalipse revela o dragão arrastando a terça parte das estrelas do céu, e depois mostra Satanás sendo lançado para baixo com os seus anjos.


Esses anjos caídos são os demônios: espíritos rebeldes, em guerra contra Deus, contra a verdade e contra a alma humana.


Primeiro, eles mentem: Jesus chamou Satanás de pai da mentira. Depois, eles tentam: até Cristo foi levado ao deserto para ser provado.


Eles também acusam, confundem, oprimem e cegam o entendimento para que as pessoas não vejam a luz do evangelho.


Paulo ainda alertou sobre espíritos enganadores e doutrinas de demônios. Mas demônios são criaturas: eles são limitados, não sabem tudo e não estão em todos os lugares.


Só Deus é onisciente e onipresente. E a sua maior proteção é revestir-se da armadura de Deus, firmar sua fé na Palavra e resistir ao mal, porque maior é O que está em você.


Qual dessas ações espirituais mais te assustou? Engano, tentação ou opressão? Comente aqui e siga o Viva o Secreto.
"""

VOZ_KOKORO = 'pm_santa'  # Voz masculina em Português como guia (melhor para converter para Isaac Bardavid)
# Caminho dinâmico para o modelo RVC dentro do repositório
BASE_DIR_PROJECT = os.path.dirname(os.path.abspath(__file__))
MODELO_PTH = os.path.join(BASE_DIR_PROJECT, "Voice Models", "ISAAC BARDAVID - Weights Model", "isaac_bardavid_model.pth")

# ==========================================
# CONFIGURAÇÃO DE DESTINO DO ÁUDIO
# ==========================================
BASE_DIR = r"D:\Documents\YT Viva o Secreto"
PASTA_NUMERO = "08"  # Altere para "02", "03", etc. a cada nova geração
NOME_ARQUIVO = "narracao.wav"

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
        speed=0.9,
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
