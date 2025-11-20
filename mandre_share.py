from typing import Optional
from android.content import Intent
from android.net import Uri
from androidx.core.content import FileProvider
from org.telegram.messenger import ApplicationLoader
from client_utils import get_last_fragment
from android_utils import run_on_ui_thread, log
from ui.bulletin import BulletinHelper
import os
import time
import threading
import shutil
from java.io import File

class MandreShare:
    @staticmethod
    def share_text(text: str, title: str = "Поделиться"):
        """Открывает системный диалог 'Поделиться' с текстом."""
        try:
            if not text or not text.strip():
                BulletinHelper.show_error("Текст для отправки пуст.")
                return
                
            def share_runner():
                try:
                    fragment = get_last_fragment()
                    if not fragment:
                        BulletinHelper.show_error("Не удалось получить доступ к текущему экрану.")
                        return
                        
                    context = fragment.getParentActivity()
                    if not context:
                        BulletinHelper.show_error("Не удалось получить контекст приложения.")
                        return
                    
                    intent = Intent(Intent.ACTION_SEND)
                    intent.setType("text/plain")
                    intent.putExtra(Intent.EXTRA_TEXT, text)
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    
                    chooser = Intent.createChooser(intent, title)
                    chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    
                    context.startActivity(chooser)
                    log(f"[MandreLib Share] Открыт диалог 'Поделиться' с текстом: {text[:50]}...")
                    
                except Exception as e:
                    log(f"[MandreLib Share] Ошибка при открытии диалога 'Поделиться': {e}")
                    BulletinHelper.show_error(f"Ошибка при открытии диалога: {str(e)}")
            
            run_on_ui_thread(share_runner)
            
        except Exception as e:
            log(f"[MandreLib Share] Критическая ошибка: {e}")
            BulletinHelper.show_error("Критическая ошибка при открытии диалога 'Поделиться'.")
    
    @staticmethod
    def share_file(file_path: str, title: str = "Поделиться файлом", mime_type: str = None):
        """Открывает системный диалог 'Поделиться' с файлом."""
        try:
            if not file_path or not file_path.strip():
                BulletinHelper.show_error("Путь к файлу не указан.")
                return
                
            if not os.path.exists(file_path):
                BulletinHelper.show_error("Файл не найден.")
                return
                
            if not os.path.isfile(file_path):
                BulletinHelper.show_error("Указанный путь не является файлом.")
                return
                
            def share_runner():
                try:
                    fragment = get_last_fragment()
                    if not fragment:
                        BulletinHelper.show_error("Не удалось получить доступ к текущему экрану.")
                        return
                        
                    context = fragment.getParentActivity()
                    if not context:
                        BulletinHelper.show_error("Не удалось получить контекст приложения.")
                        return
                    
                    # Определяем MIME-тип если не указан
                    current_mime_type = mime_type
                    if not current_mime_type:
                        current_mime_type = MandreShare._get_file_mime_type(file_path)
                    
                    # Копируем файл в Downloads/exteraGram
                    import shutil
                    from android.os import Environment
                    
                    source_file = File(file_path)
                    filename = source_file.getName()
                    
                    download_dir = Environment.getExternalStoragePublicDirectory(
                        Environment.DIRECTORY_DOWNLOADS
                    )
                    exteragram_dir = File(download_dir, "exteraGram")
                    
                    if not exteragram_dir.exists():
                        exteragram_dir.mkdirs()
                    
                    dest_file = File(exteragram_dir, filename)
                    
                    # Копируем файл
                    shutil.copy2(file_path, dest_file.getAbsolutePath())
                    log(f"[MandreLib Share] Файл скопирован в: {dest_file.getAbsolutePath()}")
                    
                    # Создаем URI для файла
                    authority = ApplicationLoader.getApplicationId() + ".provider"
                    uri = FileProvider.getUriForFile(context, authority, dest_file)
                    
                    # Создаем Intent для отправки файла
                    intent = Intent(Intent.ACTION_SEND)
                    intent.setType(current_mime_type)
                    intent.putExtra(Intent.EXTRA_STREAM, uri)
                    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                    
                    chooser = Intent.createChooser(intent, title)
                    context.startActivity(chooser)
                    
                    success_msg = f"Файл готов к отправке: {filename}"
                    BulletinHelper.show_success(success_msg)
                    log(f"[MandreLib Share] Открыт диалог 'Поделиться' с файлом: {filename}")
                    
                    # Очищаем временный файл через 5 минут
                    threading.Thread(
                        target=lambda: MandreShare._cleanup_temp_file(dest_file.getAbsolutePath(), 300),
                        daemon=True
                    ).start()
                    
                except Exception as e:
                    log(f"[MandreLib Share] Ошибка при открытии диалога 'Поделиться' с файлом: {e}")
                    BulletinHelper.show_error(f"Ошибка при открытии диалога: {str(e)}")
            
            run_on_ui_thread(share_runner)
            
        except Exception as e:
            log(f"[MandreLib Share] Критическая ошибка при отправке файла: {e}")
            BulletinHelper.show_error("Критическая ошибка при отправке файла.")
    
    @staticmethod
    def _get_file_mime_type(file_path: str) -> str:
        """Определяет MIME-тип файла по его расширению."""
        try:
            ext = file_path.lower().split('.')[-1] if '.' in file_path else ''
            mime_types = {
                # Изображения
                'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 
                'gif': 'image/gif', 'webp': 'image/webp', 'bmp': 'image/bmp',
                'svg': 'image/svg+xml', 'ico': 'image/x-icon',
                
                # Видео
                'mp4': 'video/mp4', 'webm': 'video/webm', 'mov': 'video/quicktime',
                'avi': 'video/x-msvideo', 'mkv': 'video/x-matroska',
                
                # Аудио
                'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'ogg': 'audio/ogg',
                'm4a': 'audio/mp4', 'aac': 'audio/aac', 'flac': 'audio/flac',
                
                # Документы
                'pdf': 'application/pdf', 'doc': 'application/msword',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'xls': 'application/vnd.ms-excel',
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'ppt': 'application/vnd.ms-powerpoint',
                'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'txt': 'text/plain', 'rtf': 'application/rtf',
                
                # Архивы
                'zip': 'application/zip', 'rar': 'application/x-rar-compressed',
                '7z': 'application/x-7z-compressed', 'tar': 'application/x-tar',
                'gz': 'application/gzip',
                
                # JSON/XML
                'json': 'application/json', 'xml': 'application/xml',
                'html': 'text/html', 'css': 'text/css', 'js': 'application/javascript',
                
                # Telegram специфичные
                'tgs': 'application/x-tgsticker'
            }
            return mime_types.get(ext, 'application/octet-stream')
        except Exception:
            return 'application/octet-stream'
    
    @staticmethod
    def _cleanup_temp_file(file_path: str, delay_seconds: int):
        """Удаляет временный файл через указанное время."""
        try:
            time.sleep(delay_seconds)
            if os.path.exists(file_path):
                os.remove(file_path)
                log(f"[MandreLib Share] Временный файл удален: {file_path}")
        except Exception as e:
            log(f"[MandreLib Share] Ошибка удаления временного файла: {e}")