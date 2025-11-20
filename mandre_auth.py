from typing import Callable
from android.app import Activity, KeyguardManager
from android.content import Intent
from java.lang import Integer as JInteger
from base_plugin import MethodHook
from client_utils import get_last_fragment
from android_utils import run_on_ui_thread, log
from ui.bulletin import BulletinHelper
import traceback

_AUTH_REQUEST_CODE = 1337
_auth_hook = None
_auth_success_cb = None
_auth_failure_cb = None
_hooked_plugin = None # Храним ссылку на плагин, который поставил хук

class _AuthActivityResultHook(MethodHook):
    def before_hooked_method(self, param):
        global _auth_hook, _auth_success_cb, _auth_failure_cb, _hooked_plugin
        try:
            request_code, result_code = param.args[0], param.args[1]
            if request_code == _AUTH_REQUEST_CODE:
                param.setResult(None)
                if result_code == Activity.RESULT_OK:
                    if callable(_auth_success_cb): run_on_ui_thread(_auth_success_cb)
                else:
                    if callable(_auth_failure_cb): run_on_ui_thread(_auth_failure_cb)
        except Exception: log(f"[MandreLib Auth] Ошибка в хуке результата: {traceback.format_exc()}")
        finally:
            # Снимаем хук, используя сохраненный плагин
            if _auth_hook and _hooked_plugin: 
                _hooked_plugin.unhook_method(_auth_hook)
                _auth_hook = None
                _hooked_plugin = None
            _auth_success_cb = None; _auth_failure_cb = None

class MandreAuth:
    @staticmethod
    def request(plugin_instance, on_success: Callable, on_failure: Callable, title: str = "Подтверждение", description: str = "Доступ"):
        """
        plugin_instance: Ссылка на self плагина, который вызывает auth (нужно для хука).
        """
        global _auth_hook, _auth_success_cb, _auth_failure_cb, _hooked_plugin
        
        def runner():
            global _auth_hook, _auth_success_cb, _auth_failure_cb, _hooked_plugin
            try:
                fragment = get_last_fragment()
                activity = fragment.getParentActivity() if fragment else None
                if not activity:
                    BulletinHelper.show_error("Ошибка контекста."); run_on_ui_thread(on_failure); return

                keyguard = activity.getSystemService("keyguard")
                if not keyguard or not keyguard.isKeyguardSecure():
                    BulletinHelper.show_info("Блокировка не настроена."); run_on_ui_thread(on_success); return

                _auth_success_cb, _auth_failure_cb = on_success, on_failure
                intent = keyguard.createConfirmDeviceCredentialIntent(title, description)
                
                # Снимаем старый хук если был
                if _auth_hook and _hooked_plugin: _hooked_plugin.unhook_method(_auth_hook)
                
                method = activity.getClass().getDeclaredMethod("onActivityResult", JInteger.TYPE, JInteger.TYPE, Intent)
                
                # Используем переданный плагин для хука
                _auth_hook = plugin_instance.hook_method(method, _AuthActivityResultHook())
                _hooked_plugin = plugin_instance
                
                activity.startActivityForResult(intent, _AUTH_REQUEST_CODE)
            except Exception:
                log(f"[MandreLib Auth] Ошибка: {traceback.format_exc()}")
                BulletinHelper.show_error("Ошибка аутентификации."); run_on_ui_thread(on_failure)
        
        run_on_ui_thread(runner)
