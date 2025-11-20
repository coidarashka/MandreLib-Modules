from typing import Callable
from android.app import Activity, KeyguardManager
from android.content import Intent
from java.lang import Integer as JInteger
from base_plugin import MethodHook
from mandre_lib import Mandre # Для доступа к hook_method
from client_utils import get_last_fragment
from android_utils import run_on_ui_thread, log
from ui.bulletin import BulletinHelper
import traceback

_AUTH_REQUEST_CODE = 1337
_auth_hook = None
_auth_success_cb = None
_auth_failure_cb = None

class _AuthActivityResultHook(MethodHook):
    def before_hooked_method(self, param):
        global _auth_hook, _auth_success_cb, _auth_failure_cb
        try:
            request_code, result_code = param.args[0], param.args[1]
            if request_code == _AUTH_REQUEST_CODE:
                param.setResult(None) # Предотвращаем дальнейшую обработку
                if result_code == Activity.RESULT_OK:
                    if callable(_auth_success_cb): run_on_ui_thread(_auth_success_cb)
                else:
                    if callable(_auth_failure_cb): run_on_ui_thread(_auth_failure_cb)
        except Exception: log(f"[MandreLib Auth] Ошибка в хуке результата: {traceback.format_exc()}")
        finally:
            if _auth_hook: _mandrelib_instance.unhook_method(_auth_hook); _auth_hook = None
            _auth_success_cb = None; _auth_failure_cb = None

class MandreAuth:
    @staticmethod
    def request(on_success: Callable, on_failure: Callable, title: str = "Подтверждение личности", description: str = "Это необходимо для доступа."):
        """Запрашивает аутентификацию через экран блокировки устройства."""
        global _auth_hook, _auth_success_cb, _auth_failure_cb
        
        def runner():
            global _auth_hook, _auth_success_cb, _auth_failure_cb
            try:
                fragment = get_last_fragment()
                activity = fragment.getParentActivity() if fragment else None
                if not activity:
                    BulletinHelper.show_error("Не удалось получить доступ к текущему экрану."); run_on_ui_thread(on_failure); return

                keyguard = activity.getSystemService("keyguard")
                if not keyguard or not keyguard.isKeyguardSecure():
                    BulletinHelper.show_info("Экран блокировки не настроен. Доступ разрешен."); run_on_ui_thread(on_success); return

                _auth_success_cb, _auth_failure_cb = on_success, on_failure
                intent = keyguard.createConfirmDeviceCredentialIntent(title, description)
                if not intent:
                    BulletinHelper.show_error("Не удалось создать запрос аутентификации."); run_on_ui_thread(on_failure); return

                if _auth_hook: _mandrelib_instance.unhook_method(_auth_hook)
                
                method = activity.getClass().getDeclaredMethod("onActivityResult", JInteger.TYPE, JInteger.TYPE, Intent)
                _auth_hook = _mandrelib_instance.hook_method(method, _AuthActivityResultHook())
                
                activity.startActivityForResult(intent, _AUTH_REQUEST_CODE)
            except Exception:
                log(f"[MandreLib Auth] Ошибка при вызове экрана блокировки: {traceback.format_exc()}")
                BulletinHelper.show_error("Ошибка аутентификации."); run_on_ui_thread(on_failure)
        
        run_on_ui_thread(runner)