from typing import Dict, Any, List, Optional, Callable, Union
# Правильный импорт TLRPC для работы с кнопками
from org.telegram.tgnet import TLRPC 
from urllib.parse import urlencode
# Убрал лишний ArrayList, он не используется
import json
import base64
import zlib
import re
from android_utils import log

# --- Вспомогательные функции ---
def _tl_object(cls, **kwargs):
    obj = cls()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj

class MandreInline:
    # Хранилище обработчиков: { "plugin_id": { "method_name": callback } }
    _handlers: Dict[str, Dict[str, Callable]] = {}
    
    # Кэш маркупа для сообщений
    _msg_markups: Dict[int, Dict[int, TLRPC.TL_replyInlineMarkup]] = {}

    @staticmethod
    def CallbackData(plugin_id: str, method: str, **kwargs) -> str:
        """Генерирует data для callback кнопки: mandre://plugin_id/method?args"""
        return f"mandre://{plugin_id}/{method}?{urlencode(kwargs)}"

    @staticmethod
    def Button(text: str, url: str = None, callback_data: str = None, **kwargs) -> TLRPC.KeyboardButton:
        """Создает объект кнопки"""
        if url:
            return _tl_object(TLRPC.TL_keyboardButtonUrl, text=text, url=url)
        
        if callback_data:
            return _tl_object(
                TLRPC.TL_keyboardButtonCallback, 
                text=text, 
                data=callback_data.encode("utf-8"),
                requires_password=False
            )
            
        # Упрощенный конструктор для плагинов MandreLib
        if "method" in kwargs and "plugin_id" in kwargs:
            cdata = MandreInline.CallbackData(kwargs["plugin_id"], kwargs["method"], **kwargs.get("args", {}))
            return _tl_object(
                TLRPC.TL_keyboardButtonCallback, 
                text=text, 
                data=cdata.encode("utf-8"),
                requires_password=False
            )

        return _tl_object(TLRPC.TL_keyboardButtonCallback, text=text, data=b"noop")

    class Markup:
        def __init__(self):
            self._markup = TLRPC.TL_replyInlineMarkup()

        def add_row(self, *buttons):
            row = TLRPC.TL_keyboardButtonRow()
            for btn in buttons:
                if isinstance(btn, dict): # Поддержка словарей
                    btn = MandreInline.Button(**btn)
                row.buttons.add(btn)
            self._markup.rows.add(row)
            return self
            
        @property
        def tl(self):
            return self._markup

    @staticmethod
    def on_click(method: str):
        """Декоратор для регистрации обработчика"""
        def decorator(func):
            func.__is_inline_handler__ = True
            func.__inline_method__ = method
            return func
        return decorator

    @staticmethod
    def register_handler(plugin_instance, method: str, callback: Callable):
        pid = plugin_instance.id
        if pid not in MandreInline._handlers:
            MandreInline._handlers[pid] = {}
        MandreInline._handlers[pid][method] = callback
        log(f"[MandreInline] Registered handler: {pid}/{method}")
