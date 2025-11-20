from android.speech.tts import TextToSpeech
from org.telegram.messenger import ApplicationLoader
from android_utils import run_on_ui_thread, log
from ui.bulletin import BulletinHelper
from java import dynamic_proxy
from java.util import Locale
import android.text.TextUtils as TextUtils # <--- ПРОВЕРЬ ЭТОТ ИМПОРТ

# Внутренний класс состояния (должен быть внутри модуля)
class _TTSState:
    def __init__(self):
        self.tts = None
        self.init_ok = False
        self.engine = None
        self.deferred = False

_TTS_STATE = _TTSState()
GOOGLE_TTS_PKG = "com.google.android.tts"

def _internal_ensure_tts():
    ctx = ApplicationLoader.applicationContext
    if not ctx: return False
    if _TTS_STATE.tts and _TTS_STATE.init_ok: return True
    if _TTS_STATE.deferred: return False
    _TTS_STATE.deferred = True

    def init_on_ui():
        try:
            class _OnInit(dynamic_proxy(TextToSpeech.OnInitListener)):
                def onInit(self, status):
                    _TTS_STATE.init_ok = (status == TextToSpeech.SUCCESS)
                    if _TTS_STATE.init_ok:
                        try: _TTS_STATE.tts.setLanguage(Locale.getDefault())
                        except: pass
                    else: log(f"[MandreLib TTS] init failed: status={status}")

            listener = _OnInit()
            try: _TTS_STATE.tts = TextToSpeech(ctx, listener, GOOGLE_TTS_PKG); _TTS_STATE.engine = GOOGLE_TTS_PKG
            except: _TTS_STATE.tts = TextToSpeech(ctx, listener); _TTS_STATE.engine = None
        except Exception as e: log(f"[MandreLib TTS] init error: {e}")
        finally: _TTS_STATE.deferred = False
    
    run_on_ui_thread(init_on_ui)
    return False

def _internal_shutdown_tts():
    try:
        if _TTS_STATE.tts:
            try: _TTS_STATE.tts.stop()
            except: pass
            try: _TTS_STATE.tts.shutdown()
            except: pass
            _TTS_STATE.tts = None
            _TTS_STATE.init_ok = False
            log("[MandreLib TTS] движок остановлен.")
    except Exception as e: log(f"[MandreLib TTS] shutdown error: {e}")

class MandreTTS:
    @staticmethod
    def speak(text: str):
        try:
            if not text: return # Простая проверка на пустоту
            if not (_TTS_STATE.tts and _TTS_STATE.init_ok):
                if not _internal_ensure_tts():
                    log("[MandreLib TTS] Инициализация... Попробуйте через секунду.")
                    BulletinHelper.show_info("Инициализация синтезатора...")
                    return

            def speak_on_ui():
                try: _TTS_STATE.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None, "mandre_tts")
                except: _TTS_STATE.tts.speak(text, TextToSpeech.QUEUE_FLUSH, None)
            
            run_on_ui_thread(speak_on_ui)
        except Exception as e: log(f"[MandreLib TTS] speak error: {e}")

    @staticmethod
    def shutdown():
        _internal_shutdown_tts()
