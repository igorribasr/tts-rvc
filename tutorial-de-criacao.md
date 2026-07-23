# Tutorial de Criação: Pipeline de Narração com IA (TTS + RVC)

Este tutorial ensina como construir do zero um sistema automatizado de narração de áudio que une duas tecnologias de Inteligência Artificial:
1. **TTS (Text-To-Speech):** Transforma texto escrito em fala usando um modelo leve e rápido (voz guia).
2. **RVC (Retrieval-based Voice Conversion):** Transforma o timbre da voz guia no timbre de uma voz alvo personalizada de sua escolha.

---

## 📋 Pré-requisitos e Arquivos Necessários

Para que a conversão de voz funcione, você precisa obter ou treinar um **Modelo de Voz RVC** personalizado. Esse modelo geralmente consiste em dois arquivos:

1. **Arquivo do Modelo (`.pth`):** Contém os pesos da rede neural treinada com a voz que você quer imitar.
2. **Arquivo de Índice (`.index`):** Contém o mapeamento de características da voz alvo. É responsável por ajustar o sotaque, a fidelidade e manter a entonação correta.
3. **Organização Recomendada:** Salve ambos os arquivos na mesma pasta e com o **mesmo nome** para que a biblioteca detecte o índice automaticamente. Exemplo:
   * `C:\Modelos\modelo_voz.pth`
   * `C:\Modelos\modelo_voz.index`

---

## 🛠️ Configurando o Ambiente

Instale o Python (recomenda-se a versão 3.10) e execute o comando abaixo no terminal para instalar todas as bibliotecas necessárias:

```powershell
pip install kokoro soundfile numpy scipy rvc-python torch
```

---

## ✍️ Escrevendo o Script Principal

Crie um arquivo chamado `gerar_narracao.py` e monte o código dividindo-o em 4 blocos principais:

### Bloco 1: Patch de Segurança (PyTorch)
As versões recentes do PyTorch bloqueiam por padrão o carregamento de alguns modelos mais antigos (como o HuBERT usado pelo RVC). Adicione este patch no topo do arquivo para evitar erros de `UnpicklingError`:

```python
import torch

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
```

### Bloco 2: Importações e Configurações
Importe as bibliotecas de manipulação de áudio e configure os caminhos do seu modelo de voz e pastas de destino:

```python
import os
import numpy as np
import soundfile as sf
from kokoro import KPipeline
from rvc_python.infer import RVCInference

# O texto que será narrado
TEXTO = """Seu texto de narração aqui..."""

# Voz guia do TTS (Voz masculina em Português)
VOZ_TTS = 'pm_alex'

# Caminho para o seu modelo RVC (.pth)
MODELO_RVC_PATH = r"C:\Caminho\Para\Seu\modelo_voz.pth"

# Pastas de destino
BASE_DIR = r"D:\Documents\Meus Projetos"
PASTA_NUMERO = "01"
NOME_ARQUIVO = "narracao.wav"

TEMP_AUDIO_TTS = "temp_guia.wav"
PASTA_DESTINO = os.path.join(BASE_DIR, PASTA_NUMERO)
ARQUIVO_FINAL = os.path.join(PASTA_DESTINO, NOME_ARQUIVO)
```

### Bloco 3: Função do TTS (Geração da Voz Guia)
Esta função inicializa o modelo de síntese de fala e gera o áudio base limpo:

```python
def gerar_tts_guia():
    print("⏳ 1/2: Gerando áudio guia com Kokoro TTS...")
    # 'p' representa Português do Brasil
    pipeline = KPipeline(lang_code='p')
    
    generator = pipeline(
        TEXTO, 
        voice=VOZ_TTS, 
        speed=1.0,
        split_pattern=r'\n+'
    )
    
    audio_acumulado = []
    for _, _, audio in generator:
        audio_acumulado.append(audio)
        
    audio_final = np.concatenate(audio_acumulado)
    sf.write(TEMP_AUDIO_TTS, audio_final, 24000)
    print("✅ Áudio guia criado com sucesso.")
```

### Bloco 4: Função de Conversão (RVC)
Esta função carrega o timbre personalizado, cria a pasta de destino automaticamente e realiza a conversão de voz:

```python
def aplicar_conversão_rvc():
    print("🧠 2/2: Aplicando conversão de voz (RVC)...")
    os.makedirs(PASTA_DESTINO, exist_ok=True)
    
    # Executa em GPU Nvidia (CUDA) se disponível, caso contrário em CPU
    device = "cuda:0" if os.system("nvidia-smi") == 0 else "cpu"
    rvc = RVCInference(device=device)
    
    # Carrega os pesos e faz a inferência
    rvc.load_model(MODELO_RVC_PATH)
    rvc.infer_file(
        input_path=TEMP_AUDIO_TTS,
        output_path=ARQUIVO_FINAL
    )
    
    # Limpa o arquivo temporário de voz guia
    if os.path.exists(TEMP_AUDIO_TTS):
        os.remove(TEMP_AUDIO_TTS)
        
    print(f"✨ Sucesso! Áudio salvo em: {ARQUIVO_FINAL}")
```

### Executando o Pipeline
Adicione a cláusula principal no final do arquivo:

```python
if __name__ == "__main__":
    gerar_tts_guia()
    aplicar_conversão_rvc()
```

---

## 🏃 Como Utilizar

1. Salve o script.
2. Abra o terminal na mesma pasta do script.
3. Execute o comando:
   ```bash
   python gerar_narracao.py
   ```
4. O áudio final com a voz clonada será salvo no local configurado em `ARQUIVO_FINAL`.
