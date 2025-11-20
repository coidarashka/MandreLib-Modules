from typing import Dict, Any
from android.os import Build
from org.telegram.messenger import ApplicationLoader
from android_utils import log
import time
import os

class MandreDevice:
    @staticmethod
    def get_device_info() -> Dict[str, Any]:
        """Получает подробную информацию об устройстве."""
        try:
            context = ApplicationLoader.applicationContext
            if not context:
                return {"error": "Не удалось получить контекст приложения"}
            
            device_info = {}
            
            # Базовая информация об устройстве
            device_info["manufacturer"] = Build.MANUFACTURER or "Unknown"
            device_info["model"] = Build.MODEL or "Unknown"
            device_info["brand"] = Build.BRAND or "Unknown"
            device_info["product"] = Build.PRODUCT or "Unknown"
            device_info["device"] = Build.DEVICE or "Unknown"
            device_info["board"] = Build.BOARD or "Unknown"
            device_info["hardware"] = Build.HARDWARE or "Unknown"
            
            # Информация об Android
            device_info["android_version"] = Build.VERSION.RELEASE or "Unknown"
            device_info["api_level"] = Build.VERSION.SDK_INT
            device_info["codename"] = Build.VERSION.CODENAME or "Unknown"
            device_info["incremental"] = Build.VERSION.INCREMENTAL or "Unknown"
            
            # Информация о сборке
            device_info["build_id"] = Build.ID or "Unknown"
            device_info["build_type"] = Build.TYPE or "Unknown"
            device_info["build_tags"] = Build.TAGS or "Unknown"
            device_info["build_time"] = Build.TIME
            device_info["build_user"] = Build.USER or "Unknown"
            device_info["build_host"] = Build.HOST or "Unknown"
            device_info["build_fingerprint"] = Build.FINGERPRINT or "Unknown"
            
            # Информация о дисплее
            try:
                from android.util import DisplayMetrics
                from android.view import WindowManager
                
                wm = context.getSystemService("window")
                if wm:
                    display = wm.getDefaultDisplay()
                    if display:
                        metrics = DisplayMetrics()
                        display.getMetrics(metrics)
                        
                        device_info["screen_width"] = metrics.widthPixels
                        device_info["screen_height"] = metrics.heightPixels
                        device_info["screen_density"] = metrics.density
                        device_info["screen_density_dpi"] = metrics.densityDpi
                        device_info["screen_xdpi"] = metrics.xdpi
                        device_info["screen_ydpi"] = metrics.ydpi
            except Exception as e:
                device_info["screen_error"] = str(e)
            
            # Информация о памяти
            try:
                from android.app import ActivityManager
                
                am = context.getSystemService("activity")
                if am:
                    memory_info = am.getMemoryInfo()
                    if memory_info:
                        device_info["total_memory_mb"] = memory_info.totalMem // (1024 * 1024)
                        device_info["available_memory_mb"] = memory_info.availMem // (1024 * 1024)
            except Exception as e:
                device_info["memory_error"] = str(e)
            
            # Информация о процессоре
            device_info["cpu_abi"] = Build.CPU_ABI or "Unknown"
            device_info["cpu_abi2"] = Build.CPU_ABI2 or "Unknown"
            device_info["supported_abis"] = list(Build.SUPPORTED_ABIS) if hasattr(Build, 'SUPPORTED_ABIS') else []
            
            # Информация о телефоне (если доступно)
            try:
                tm = context.getSystemService("phone")
                if tm:
                    device_info["phone_type"] = tm.getPhoneType()
                    device_info["network_operator"] = tm.getNetworkOperator() or "Unknown"
                    device_info["network_operator_name"] = tm.getNetworkOperatorName() or "Unknown"
                    device_info["sim_operator"] = tm.getSimOperator() or "Unknown"
                    device_info["sim_operator_name"] = tm.getSimOperatorName() or "Unknown"
                    device_info["sim_country_iso"] = tm.getSimCountryIso() or "Unknown"
                    device_info["sim_serial"] = tm.getSimSerialNumber() or "Unknown"
                    device_info["subscriber_id"] = tm.getSubscriberId() or "Unknown"
            except Exception as e:
                device_info["phone_error"] = str(e)
            
            # Информация о приложении
            try:
                package_info = context.getPackageManager().getPackageInfo(context.getPackageName(), 0)
                device_info["app_version_name"] = package_info.versionName or "Unknown"
                device_info["app_version_code"] = package_info.versionCode
                device_info["app_package"] = context.getPackageName()
            except Exception as e:
                device_info["app_error"] = str(e)
            
            # Дополнительная информация
            device_info["is_emulator"] = MandreDevice._is_emulator()
            device_info["is_rooted"] = MandreDevice._is_rooted()
            device_info["locale"] = str(Locale.getDefault())
            device_info["timezone"] = str(TimeZone.getDefault().getID())
            
            # Время получения информации
            device_info["timestamp"] = int(time.time())
            device_info["timestamp_formatted"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            
            return device_info
            
        except Exception as e:
            log(f"[MandreLib Device] Ошибка получения информации об устройстве: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def _is_emulator() -> bool:
        """Проверяет, запущено ли приложение в эмуляторе."""
        try:
            return (Build.FINGERPRINT and "generic" in Build.FINGERPRINT) or \
                   (Build.MODEL and "google_sdk" in Build.MODEL) or \
                   (Build.MODEL and "Android SDK built for x86" in Build.MODEL) or \
                   (Build.MANUFACTURER and "Genymotion" in Build.MANUFACTURER) or \
                   (Build.HARDWARE and "goldfish" in Build.HARDWARE) or \
                   (Build.PRODUCT and "sdk" in Build.PRODUCT) or \
                   (Build.PRODUCT and "google_sdk" in Build.PRODUCT)
        except:
            return False
    
    @staticmethod
    def _is_rooted() -> bool:
        """Проверяет, есть ли root права на устройстве."""
        try:
            # Проверяем наличие su
            su_paths = ["/system/bin/su", "/system/xbin/su", "/sbin/su", "/system/su", "/system/bin/.ext/.su"]
            for path in su_paths:
                if os.path.exists(path):
                    return True
            
            # Проверяем наличие busybox
            if os.path.exists("/system/bin/busybox") or os.path.exists("/system/xbin/busybox"):
                return True
                
            return False
        except:
            return False
    
    @staticmethod
    def get_simple_info() -> str:
        """Возвращает краткую информацию об устройстве в виде строки."""
        try:
            info = MandreDevice.get_device_info()
            if "error" in info:
                return f"Ошибка: {info['error']}"
            
            return f"{info.get('manufacturer', 'Unknown')} {info.get('model', 'Unknown')} (Android {info.get('android_version', 'Unknown')}, API {info.get('api_level', 'Unknown')})"
        except Exception as e:

            return f"Ошибка получения информации: {e}"
