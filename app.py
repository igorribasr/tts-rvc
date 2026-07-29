# Python Backend Server for TTS-RVC Studio
# Handles API endpoints and serves static files using standard library HTTP server.

import os
import sys
import json
import urllib.parse
import http.server
import socketserver
import threading
import asyncio
import shutil
import uuid

# Patch torch.load globally to bypass weights_only restrictions on newer PyTorch versions.
try:
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
    print("[INFO] PyTorch patched successfully for RVC weight loading.")
except Exception as e:
    print(f"[WARN] Warning: Could not patch PyTorch load: {e}")

# Imports for speech/voice conversion
import soundfile as sf
import numpy as np
import edge_tts
from kokoro import KPipeline
from rvc_python.infer import RVCInference

# Configuration
PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
MODELS_DIR = os.path.join(BASE_DIR, "Voice Models")

DEFAULT_BASE_DESTINATION = r"D:\Documents\YT Viva o Secreto"
DEFAULT_FOLDER_NUM = "08"

# Catalog of all 54 official Kokoro voices grouped by language
KOKORO_VOICES = [
    # Português
    {"id": "pm_santa", "name": "pm_santa (Santa - Masculino)", "lang": "p", "langLabel": "Português (BR)"},
    {"id": "pm_alex", "name": "pm_alex (Alex - Masculino)", "lang": "p", "langLabel": "Português (BR)"},
    {"id": "pf_dora", "name": "pf_dora (Dora - Feminino)", "lang": "p", "langLabel": "Português (BR)"},
    {"id": "pf_sara", "name": "pf_sara (Sara - Feminino)", "lang": "p", "langLabel": "Português (BR)"},

    # Inglês US
    {"id": "af_heart", "name": "af_heart (Heart - Feminino Star)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "af_alloy", "name": "af_alloy (Alloy - Feminino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "af_aoede", "name": "af_aoede (Aoede - Feminino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "af_bella", "name": "af_bella (Bella - Feminino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "af_jessica", "name": "af_jessica (Jessica - Feminino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "af_kore", "name": "af_kore (Kore - Feminino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "af_nicole", "name": "af_nicole (Nicole - Feminino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "af_nova", "name": "af_nova (Nova - Feminino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "af_river", "name": "af_river (River - Feminino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "af_sarah", "name": "af_sarah (Sarah - Feminino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "af_sky", "name": "af_sky (Sky - Feminino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "am_adam", "name": "am_adam (Adam - Masculino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "am_echo", "name": "am_echo (Echo - Masculino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "am_eric", "name": "am_eric (Eric - Masculino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "am_fenrir", "name": "am_fenrir (Fenrir - Masculino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "am_liam", "name": "am_liam (Liam - Masculino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "am_michael", "name": "am_michael (Michael - Masculino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "am_onyx", "name": "am_onyx (Onyx - Masculino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "am_puck", "name": "am_puck (Puck - Masculino)", "lang": "a", "langLabel": "Inglês (US)"},
    {"id": "am_santa", "name": "am_santa (Santa - Masculino)", "lang": "a", "langLabel": "Inglês (US)"},

    # Inglês UK
    {"id": "bf_alice", "name": "bf_alice (Alice - Feminino)", "lang": "b", "langLabel": "Inglês (UK)"},
    {"id": "bf_emma", "name": "bf_emma (Emma - Feminino)", "lang": "b", "langLabel": "Inglês (UK)"},
    {"id": "bf_isabella", "name": "bf_isabella (Isabella - Feminino)", "lang": "b", "langLabel": "Inglês (UK)"},
    {"id": "bf_lily", "name": "bf_lily (Lily - Feminino)", "lang": "b", "langLabel": "Inglês (UK)"},
    {"id": "bm_daniel", "name": "bm_daniel (Daniel - Masculino)", "lang": "b", "langLabel": "Inglês (UK)"},
    {"id": "bm_fable", "name": "bm_fable (Fable - Masculino)", "lang": "b", "langLabel": "Inglês (UK)"},
    {"id": "bm_george", "name": "bm_george (George - Masculino)", "lang": "b", "langLabel": "Inglês (UK)"},
    {"id": "bm_lewis", "name": "bm_lewis (Lewis - Masculino)", "lang": "b", "langLabel": "Inglês (UK)"},

    # Espanhol
    {"id": "ef_dora", "name": "ef_dora (Dora - Feminino)", "lang": "e", "langLabel": "Espanhol"},
    {"id": "em_alex", "name": "em_alex (Alex - Masculino)", "lang": "e", "langLabel": "Espanhol"},
    {"id": "em_santa", "name": "em_santa (Santa - Masculino)", "lang": "e", "langLabel": "Espanhol"},

    # Francês
    {"id": "ff_siwis", "name": "ff_siwis (Siwis - Feminino)", "lang": "f", "langLabel": "Francês"},

    # Italiano
    {"id": "if_sara", "name": "if_sara (Sara - Feminino)", "lang": "i", "langLabel": "Italiano"},
    {"id": "im_nicola", "name": "im_nicola (Nicola - Masculino)", "lang": "i", "langLabel": "Italiano"},

    # Hindi
    {"id": "hf_alpha", "name": "hf_alpha (Alpha - Feminino)", "lang": "h", "langLabel": "Hindi"},
    {"id": "hf_beta", "name": "hf_beta (Beta - Feminino)", "lang": "h", "langLabel": "Hindi"},
    {"id": "hm_omega", "name": "hm_omega (Omega - Masculino)", "lang": "h", "langLabel": "Hindi"},
    {"id": "hm_psi", "name": "hm_psi (Psi - Masculino)", "lang": "h", "langLabel": "Hindi"},

    # Japonês
    {"id": "jf_alpha", "name": "jf_alpha (Alpha - Feminino)", "lang": "j", "langLabel": "Japonês"},
    {"id": "jf_gongitsune", "name": "jf_gongitsune (Gongitsune - Feminino)", "lang": "j", "langLabel": "Japonês"},
    {"id": "jf_nezumi", "name": "jf_nezumi (Nezumi - Feminino)", "lang": "j", "langLabel": "Japonês"},
    {"id": "jf_tebukuro", "name": "jf_tebukuro (Tebukuro - Feminino)", "lang": "j", "langLabel": "Japonês"},
    {"id": "jm_kumo", "name": "jm_kumo (Kumo - Masculino)", "lang": "j", "langLabel": "Japonês"},

    # Mandarim
    {"id": "zf_xiaobei", "name": "zf_xiaobei (Xiaobei - Feminino)", "lang": "z", "langLabel": "Mandarim"},
    {"id": "zf_xiaoni", "name": "zf_xiaoni (Xiaoni - Feminino)", "lang": "z", "langLabel": "Mandarim"},
    {"id": "zf_xiaoxiao", "name": "zf_xiaoxiao (Xiaoxiao - Feminino)", "lang": "z", "langLabel": "Mandarim"},
    {"id": "zf_xiaoyi", "name": "zf_xiaoyi (Xiaoyi - Feminino)", "lang": "z", "langLabel": "Mandarim"},
    {"id": "zm_yunjian", "name": "zm_yunjian (Yunjian - Masculino)", "lang": "z", "langLabel": "Mandarim"},
    {"id": "zm_yunxi", "name": "zm_yunxi (Yunxi - Masculino)", "lang": "z", "langLabel": "Mandarim"},
    {"id": "zm_yunxia", "name": "zm_yunxia (Yunxia - Masculino)", "lang": "z", "langLabel": "Mandarim"},
    {"id": "zm_yunyang", "name": "zm_yunyang (Yunyang - Masculino)", "lang": "z", "langLabel": "Mandarim"}
]

# Create output folder if it doesn't exist
os.makedirs(OUTPUTS_DIR, exist_ok=True)

def find_voice_models():
    """Scans the Voice Models directory to find models dynamically."""
    models_list = []
    if not os.path.isdir(MODELS_DIR):
        print(f"[WARN] Voice Models directory not found at: {MODELS_DIR}")
        return models_list
        
    for item in os.listdir(MODELS_DIR):
        item_path = os.path.join(MODELS_DIR, item)
        if os.path.isdir(item_path):
            pth_file = None
            index_file = None
            for file in os.listdir(item_path):
                if file.endswith(".pth"):
                    pth_file = os.path.join(item_path, file)
                elif file.endswith(".index"):
                    index_file = os.path.join(item_path, file)
            
            if pth_file:
                models_list.append({
                    "name": item,
                    "pth": pth_file,
                    "index": index_file or ""
                })
    return models_list

class TTS_RVC_RequestHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urllib.parse.urlparse(path)
        path = parsed.path
        if path == "/":
            return os.path.join(WEB_DIR, "index.html")
        elif path.startswith("/api/") or path.startswith("/audio/"):
            return path
        else:
            clean_path = path.lstrip('/')
            return os.path.join(WEB_DIR, clean_path)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # Endpoint: GET /api/models
        if path == "/api/models":
            try:
                models_found = find_voice_models()
                response_data = json.dumps(models_found).encode('utf-8')
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data)
            except Exception as e:
                self.send_error_json(500, str(e))
            return

        # Endpoint: GET /api/kokoro_voices
        elif path == "/api/kokoro_voices":
            try:
                response_data = json.dumps(KOKORO_VOICES).encode('utf-8')
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data)
            except Exception as e:
                self.send_error_json(500, str(e))
            return

        # Endpoint: GET /api/defaults
        elif path == "/api/defaults":
            try:
                default_text = ""
                isaac_script = os.path.join(BASE_DIR, "gerar_narracao_isaac.py")
                if os.path.exists(isaac_script):
                    try:
                        with open(isaac_script, "r", encoding="utf-8") as f:
                            code = f.read()
                            if 'TEXTO = """' in code:
                                default_text = code.split('TEXTO = """')[1].split('"""')[0].strip()
                    except Exception:
                        pass

                data = {
                    "base_destination": DEFAULT_BASE_DESTINATION,
                    "folder_num": DEFAULT_FOLDER_NUM,
                    "default_text": default_text
                }
                response_data = json.dumps(data).encode('utf-8')
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data)
            except Exception as e:
                self.send_error_json(500, str(e))
            return

        # Endpoint: GET /audio/<filename>
        elif path.startswith("/audio/"):
            filename = os.path.basename(path)
            file_path = os.path.join(OUTPUTS_DIR, filename)
            
            if os.path.exists(file_path):
                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Content-Length", str(os.path.getsize(file_path)))
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                with open(file_path, 'rb') as f:
                    shutil.copyfileobj(f, self.wfile)
            else:
                self.send_error(404, "Arquivo de audio nao encontrado.")
            return

        super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/api/generate":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                params = json.loads(post_data.decode('utf-8'))
                result = self.process_generation(params)
                
                response_data = json.dumps(result).encode('utf-8')
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data)
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_error_json(500, str(e))
            return

        self.send_error(404, "Rota nao encontrada.")

    def send_error_json(self, status_code, message):
        response_data = json.dumps({"error": message}).encode('utf-8')
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_data)))
        self.end_headers()
        self.wfile.write(response_data)

    def process_generation(self, params):
        text = params.get("text", "")
        tts_engine = params.get("tts_engine", "kokoro")
        tts_voice = params.get("tts_voice", "pm_santa")
        tts_speed = params.get("tts_speed", 0.9)
        model_name = params.get("model_name", "")

        target_folder = params.get("target_folder", "").strip()
        custom_filename = params.get("custom_filename", "narracao.wav").strip() or "narracao.wav"
        
        f0_up_key = params.get("f0_up_key", 0)
        f0_method = params.get("f0_method", "rmvpe")
        index_rate = params.get("index_rate", 0.55)
        protect = params.get("protect", 0.33)
        rms_mix_rate = params.get("rms_mix_rate", 0.25)
        filter_radius = params.get("filter_radius", 3)

        if not text:
            raise ValueError("O texto da narração é obrigatório.")

        models_found = find_voice_models()
        if not model_name and len(models_found) > 0:
            isaac_m = next((m for m in models_found if "ISAAC" in m["name"].upper()), None)
            selected_model = isaac_m or models_found[0]
            model_name = selected_model["name"]
        else:
            selected_model = next((m for m in models_found if m["name"] == model_name), None)
            
        if not selected_model:
            raise ValueError(f"Modelo de voz '{model_name}' não encontrado.")

        job_id = str(uuid.uuid4())[:8]
        temp_guide = os.path.join(OUTPUTS_DIR, f"temp_{job_id}.wav")
        web_output_filename = f"narracao_{job_id}.wav"
        web_output_path = os.path.join(OUTPUTS_DIR, web_output_filename)

        saved_local_path = ""

        try:
            print(f"[{job_id}] [INFO] Gerando áudio guia com {tts_engine} (voz: {tts_voice})...")
            
            if tts_engine == "edge":
                rate_pct = int((tts_speed - 1.0) * 100)
                rate_str = f"{rate_pct:+d}%"
                
                async def run_edge_tts():
                    communicate = edge_tts.Communicate(text, tts_voice, rate=rate_str)
                    await communicate.save(temp_guide)
                
                asyncio.run(run_edge_tts())
                
            elif tts_engine == "kokoro":
                # Detect language code dynamically from voice prefix (p, a, b, e, f, i, h, j, z)
                first_char = tts_voice[0].lower() if len(tts_voice) > 0 else 'p'
                lang_code = first_char if first_char in 'abpefijzh' else 'p'
                
                print(f"[{job_id}] [INFO] Inicializando KPipeline com lang_code='{lang_code}' para a voz '{tts_voice}'...")
                pipeline = KPipeline(lang_code=lang_code)
                
                generator = pipeline(
                    text, 
                    voice=tts_voice, 
                    speed=tts_speed,
                    split_pattern=r'\n+'
                )
                
                audio_acumulado = []
                for _, _, audio in generator:
                    audio_acumulado.append(audio)
                    
                if not audio_acumulado:
                    raise RuntimeError(f"Nenhum áudio foi gerado pela engine Kokoro TTS para a voz '{tts_voice}'.")
                    
                audio_final = np.concatenate(audio_acumulado)
                sf.write(temp_guide, audio_final, 24000)
                
            else:
                raise ValueError(f"Engine TTS desconhecida: {tts_engine}")

            print(f"[{job_id}] [OK] Áudio guia gerado em: {temp_guide}")

            print(f"[{job_id}] [INFO] Iniciando conversão RVC com modelo: {selected_model['name']}")
            device = "cuda:0" if os.system("nvidia-smi") == 0 else "cpu"
            
            rvc = RVCInference(device=device)
            rvc.load_model(selected_model["pth"], index_path=selected_model["index"])
            
            rvc.f0up_key = f0_up_key
            rvc.f0method = f0_method
            rvc.index_rate = index_rate
            rvc.protect = protect
            rvc.rms_mix_rate = rms_mix_rate
            rvc.filter_radius = filter_radius
            
            rvc.infer_file(temp_guide, web_output_path)
            print(f"[{job_id}] [OK] RVC completo! Salvo no servidor em: {web_output_path}")

            if target_folder:
                try:
                    os.makedirs(target_folder, exist_ok=True)
                    dest_file_path = os.path.join(target_folder, custom_filename)
                    shutil.copy(web_output_path, dest_file_path)
                    saved_local_path = os.path.abspath(dest_file_path)
                    print(f"[{job_id}] [OK] Cópia salva na pasta de destino: {saved_local_path}")
                except Exception as e:
                    print(f"[{job_id}] [WARN] Não foi possível salvar na pasta '{target_folder}': {e}")

        finally:
            if os.path.exists(temp_guide):
                try:
                    os.remove(temp_guide)
                except Exception as e:
                    print(f"[WARN] Erro ao remover guia temporário: {e}")

        return {
            "success": True,
            "filename": web_output_filename,
            "filepath": saved_local_path or os.path.abspath(web_output_path),
            "local_saved": bool(saved_local_path)
        }

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

def start_server():
    server_address = ('', PORT)
    httpd = ThreadingHTTPServer(server_address, TTS_RVC_RequestHandler)
    print(f"[INFO] Servidor rodando em http://localhost:{PORT}")
    print(f"[INFO] Servindo frontend de: {WEB_DIR}")
    print(f"[INFO] Salvando áudios gerados em: {OUTPUTS_DIR}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Parando o servidor...")
        httpd.server_close()
        sys.exit(0)

if __name__ == '__main__':
    start_server()
