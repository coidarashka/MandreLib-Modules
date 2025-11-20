from typing import List, Any, Optional
from mandre_lib import Mandre  # Чтобы был доступ к Mandre.sql_get_database
from org.telegram.tgnet import TLRPC
from android_utils import log

class MandreMessages:
    @staticmethod
    def get_local(dialog_id: int, limit: int = 100) -> List[Any]:
        """
        Мгновенно получает сообщения из локальной базы данных (кэша).
        Не делает запросов в сеть. Возвращает список объектов TLRPC.Message.
        Usage: msgs = Mandre.Messages.get_local(dialog_id, 50)
        """
        messages = []
        db = Mandre.sql_get_database()
        if not db: return messages
        
        # Читаем сырой BLOB (data), ID сообщения (mid) и дату для точной сортировки
        query = f"SELECT data, mid, date FROM messages_v2 WHERE uid = {int(dialog_id)} ORDER BY date DESC LIMIT {int(limit)}"
        cursor = db.queryFinalized(query)
        
        try:
            while cursor.next():
                data = cursor.byteBufferValue(0) # NativeByteBuffer
                if data:
                    # Десериализация TL-объекта из байтов
                    msg = TLRPC.Message.TLdeserialize(data, data.readInt32(False), False)
                    if msg:
                        # Восстанавливаем критичные поля из колонок БД (быстрее и надежнее)
                        msg.id = cursor.intValue(1)
                        msg.date = cursor.intValue(2)
                        msg.dialog_id = int(dialog_id)
                        messages.append(msg)
                    data.reuse() # Обязательно освобождаем память NativeByteBuffer
        except Exception as e:
            log(f"[MandreMessages] SQL Error: {e}")
        finally:
            cursor.dispose() # Закрываем курсор
            

        return messages
