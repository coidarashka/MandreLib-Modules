from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import json
import re
from urllib.parse import urlencode, parse_qs, urlparse
from android_utils import log
from org.telegram.tgnet import TLRPC
from java.util import ArrayList
from client_utils import get_send_messages_helper, get_messages_controller, get_last_fragment

class MandreInline:
    # Хранилище маркапов: dialog_id -> {msg_id: markup}
    msg_markups: Dict[int, Dict[int, Any]] = {}
    # Очередь на отправку: dialog_id -> [data]
    need_markups: Dict[int, List[Dict[str, Any]]] = {}
    
    callbacks: Dict[str, Callable] = {} # plugin_id -> {method: func}

    @staticmethod
    def CallbackData(plugin_id, method: str, **kwargs):
        return f"mandre://{plugin_id}/{method}?{urlencode(kwargs)}"

    @staticmethod
    def Button(text: str, callback_data: str = None, url: str = None):
        if url:
            btn = TLRPC.TL_keyboardButtonUrl()
            btn.text = text
            btn.url = url
            return btn
        elif callback_data:
            btn = TLRPC.TL_keyboardButtonCallback()
            btn.text = text
            btn.data = callback_data.encode("utf-8")
            btn.requires_password = False
            return btn
        return None

    class Markup:
        def __init__(self):
            self._markup = TLRPC.TL_replyInlineMarkup()
            self.rows = []

        def add_row(self, *btns):
            row = TLRPC.TL_keyboardButtonRow()
            for btn in btns:
                if btn: row.buttons.add(btn)
            self._markup.rows.add(row)
            return self
        
        def get(self):
            return self._markup

    @dataclass
    class CallbackParams:
        message: Any # MessageObject
        button: Any  # KeyboardButton
        
        def answer(self, text: str, alert: bool = False):
            # Тут можно реализовать показ тоста или алерта
            pass

    # Декоратор для регистрации обработчика
    @classmethod
    def on_click(cls, method: str):
        def decorator(func):
            func.__is_inline_callback__ = True
            func.__data__ = method
            return func
        return decorator

    # Метод для регистрации плагина (вызывается из MandreLib)
    @classmethod
    def register_plugin(cls, plugin):
        # Ищем методы с декоратором @on_click
        import inspect
        for name, func in inspect.getmembers(plugin, predicate=inspect.ismethod):
            if getattr(func, "__is_inline_callback__", False):
                method_name = getattr(func, "__data__", name)
                if plugin.id not in cls.callbacks:
                    cls.callbacks[plugin.id] = {}
                cls.callbacks[plugin.id][method_name] = func
                log(f"[MandreInline] Registered callback: {plugin.id}/{method_name}")
