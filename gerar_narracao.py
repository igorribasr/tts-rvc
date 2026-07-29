import asyncio
import os
import edge_tts
# pyrefly: ignore [missing-import]
from rvc_python.infer import RVCInference

# ==========================================
# CONFIGURAÇÕES DO PROJETO
# ==========================================

# 1. Seu texto para narração
TEXTO = """
Você sabia que a serpente do Jardim do Éden não era nada parecida com o réptil que conhecemos hoje?

Registros antigos mesopotâmicos e sumérios revelam que, antes do juízo divino, essa criatura era retratada com asas, quatro patas e uma presença magnífica. Essa forma esplendorosa explica por que existe uma ligação tão direta entre a figura da serpente e a do dragão nos textos bíblicos e na literatura antiga.

Em hebraico, a palavra [Tannin](/tɑːnˈniːn/) é usada para descrever tanto serpentes quanto dragões e grandes répteis marinhos. Embora o livro de Gênesis descreva a serpente como a mais astuta de todas as criaturas do campo, o livro de Apocalipse desvenda o verdadeiro mistério por trás do evento: Satanás utilizou esse ser extraordinário como o veículo perfeito para introduzir a tentação no mundo. O mal usou uma criatura majestosa para mudar para sempre o rumo da humanidade.

Qual desses detalhes mais te surpreendeu? Deixe sua opinião nos comentários e siga o Viva o Secreto para continuar desvendando os maiores mistérios da Bíblia!
"""

# 2. Voz guia do Edge-TTS
VOZ_EDGE = "pt-BR-AntonioNeural"

# 3. Caminhos dinâmicos dos arquivos do Isaac Bardavid dentro do repositório
BASE_DIR_PROJECT = os.path.dirname(os.path.abspath(__file__))
MODELO_PTH = os.path.join(BASE_DIR_PROJECT, "Voice Models", "ISAAC BARDAVID - Weights Model", "isaac_bardavid_model.pth")
ARQUIVO_INDEX = os.path.join(BASE_DIR_PROJECT, "Voice Models", "ISAAC BARDAVID - Weights Model", "isaac_bardavid_model.index")

# 4. Arquivos de saída na pasta C:\Users\Usuario
TEMP_AUDIO_TTS = "temp_guia.mp3"
ARQUIVO_FINAL = "narracao_isaac_bardavid.wav"


async def gerar_tts():
    """Gera o áudio base sem limites de tamanho."""
    print("⏳ 1/2: Gerando áudio guia com Edge-TTS...")
    communicate = edge_tts.Communicate(TEXTO, VOZ_EDGE)
    await communicate.save(TEMP_AUDIO_TTS)


def aplicar_rvc():
    """Aplica o modelo do Isaac Bardavid via RVC."""
    print("🧠 2/2: Aplicando a voz do Isaac Bardavid...")
    device = "cuda:0" if os.system("nvidia-smi") == 0 else "cpu"
    rvc = RVCInference(device=device)

    # Carrega o modelo do drive D:
    rvc.load_model(MODELO_PTH)

    # Executa a conversão de forma direta
    rvc.infer_file(
        input_path=TEMP_AUDIO_TTS,
        output_path=ARQUIVO_FINAL
    )

    # Limpa o arquivo temporário
    if os.path.exists(TEMP_AUDIO_TTS):
        os.remove(TEMP_AUDIO_TTS)

    print(
        f"\n✨ SUCESSO! O áudio final foi salvo em:"
        f" C:\\Users\\Usuario\\{ARQUIVO_FINAL}"
    )


if __name__ == "__main__":
    asyncio.run(gerar_tts())
    aplicar_rvc()