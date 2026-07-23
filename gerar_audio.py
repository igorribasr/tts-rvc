import numpy as np
import soundfile as sf
from kokoro import KPipeline

# 1. Inicializa o pipeline em Português do Brasil ('b')
# 'a' = Inglês Americano, 'b' = Português BR, 'e' = Espanhol, 'f' = Francês
print(" Carregando modelo Kokoro TTS...")
pipeline = KPipeline(lang_code='b')

# 2. Texto para narração
TEXTO = """
Você já parou para pensar na diferença entre como Deus criou todo o universo... e como Ele criou você?
Para formar as estrelas e galáxias infinitas, bastou uma palavra.
"""

# 3. Escolhe a voz guia:
# 'bm_george' (Masculina) ou 'bf_isabella' (Feminina)
VOZ = 'bm_george'

print(" Gerando áudio com Kokoro...")

# O Kokoro processa o texto em partes (generator)
generator = pipeline(
    TEXTO, 
    voice=VOZ, 
    speed=1.0,           # Velocidade (1.0 = normal)
    split_pattern=r'\n+' # Quebra de linha por parágrafos
)

audio_acumulado = []

for graphemes, phonemes, audio in generator:
    audio_acumulado.append(audio)

# Concatena todos os blocos em um único áudio
audio_final = np.concatenate(audio_acumulado)

# Salva em arquivo .wav (Kokoro gera em 24.000 Hz)
sf.write("guia_kokoro.wav", audio_final, 24000)

print(" Sucesso! Áudio salvo como: guia_kokoro.wav")