class MandreNotification:
    @staticmethod
    def show_simple(title: str, text: str, channel_id: str = "mandrelib_notifications"):
        """Показывает простое уведомление."""
        try:
            context = ApplicationLoader.applicationContext
            if not context:
                return
            
            # Создаем канал для Android 8.0+
            if Build.VERSION.SDK_INT >= 26:
                notification_manager = context.getSystemService(Context.NOTIFICATION_SERVICE)
                if notification_manager.getNotificationChannel(channel_id) is None:
                    channel = NotificationChannel(channel_id, "MandreLib Notifications", NotificationManager.IMPORTANCE_DEFAULT)
                    notification_manager.createNotificationChannel(channel)
            
            # Создаем уведомление
            builder = NotificationCompat.Builder(context, channel_id)
            builder.setSmallIcon(R.drawable.msg_notifications_solar)
            builder.setContentTitle(title)
            builder.setContentText(text)
            builder.setColor(Theme.getColor(Theme.key_actionBarDefault))
            builder.setAutoCancel(True)
            builder.setPriority(0) # NotificationCompat.PRIORITY_DEFAULT
            builder.setDefaults(-1) # NotificationCompat.DEFAULT_ALL
            
            # Показываем уведомление
            notification_manager_compat = NotificationManagerCompat.from_(context)
            notification_id = int(time.time()) % 10000
            notification_manager_compat.notify(notification_id, builder.build())
            
            log(f"[MandreLib Notification] Показано простое уведомление: {title}")
            
        except Exception as e:
            log(f"[MandreLib Notification] Ошибка показа простого уведомления: {e}")
    
    @staticmethod
    def show_dialog(sender_name: str, message: str, avatar_url: str = None, channel_id: str = "mandrelib_dialog_notifications"):
        """Показывает уведомление в стиле диалога с аватаром."""
        try:
            context = ApplicationLoader.applicationContext
            if not context:
                return
            
            # Создаем канал для Android 8.0+
            if Build.VERSION.SDK_INT >= 26:
                notification_manager = context.getSystemService(Context.NOTIFICATION_SERVICE)
                if notification_manager.getNotificationChannel(channel_id) is None:
                    channel = NotificationChannel(channel_id, "MandreLib Dialog Notifications", NotificationManager.IMPORTANCE_DEFAULT)
                    notification_manager.createNotificationChannel(channel)
            
            # Загружаем и обрабатываем аватар
            avatar_bitmap = None
            if avatar_url:
                try:
                    import requests
                    response = requests.get(avatar_url, timeout=5)
                    if response.status_code == 200:
                        image_bytes = response.content
                        decoded_bitmap = BitmapFactory.decodeByteArray(image_bytes, 0, len(image_bytes))
                        avatar_bitmap = MandreNotification._get_circular_bitmap(decoded_bitmap)
                except:
                    pass
            
            # Создаем Person для отправителя
            sender_builder = Person.Builder().setName(sender_name)
            if avatar_bitmap:
                icon = IconCompat.createWithBitmap(avatar_bitmap)
                sender_builder.setIcon(icon)
            sender = sender_builder.build()
            
            # Создаем Person для получателя
            user = Person.Builder().setName("You").build()
            
            # Создаем MessagingStyle
            messaging_style = NotificationCompat.MessagingStyle(user)
            messaging_style.setGroupConversation(False)
            
            timestamp = int(time.time() * 1000)
            msg = NotificationCompat.MessagingStyle.Message(message, timestamp, sender)
            messaging_style.addMessage(msg)
            
            # Создаем уведомление
            builder = NotificationCompat.Builder(context, channel_id)
            builder.setStyle(messaging_style)
            builder.setSmallIcon(R.drawable.msg_notifications_solar)
            builder.setColor(Theme.getColor(Theme.key_actionBarDefault))
            builder.setAutoCancel(True)
            builder.setPriority(0) # NotificationCompat.PRIORITY_DEFAULT
            builder.setDefaults(-1) # NotificationCompat.DEFAULT_ALL
            
            # Показываем уведомление
            notification_manager_compat = NotificationManagerCompat.from_(context)
            notification_id = int(time.time()) % 10000
            notification_manager_compat.notify(notification_id, builder.build())
            
            log(f"[MandreLib Notification] Показано диалог уведомление от {sender_name}")
            
        except Exception as e:
            log(f"[MandreLib Notification] Ошибка показа диалог уведомления: {e}")
    
    @staticmethod
    def _get_circular_bitmap(bitmap):
        """Обрезает Bitmap в круг."""
        if bitmap is None:
            return None
        
        width = bitmap.getWidth()
        height = bitmap.getHeight()
        
        output = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        canvas = Canvas(output)
        
        paint = Paint()
        rect = Rect(0, 0, width, height)
        rect_f = RectF(rect)
        
        paint.setAntiAlias(True)
        canvas.drawARGB(0, 0, 0, 0)
        paint.setARGB(255, 255, 255, 255)
        canvas.drawOval(rect_f, paint)
        
        paint.setXfermode(PorterDuffXfermode(PorterDuff.Mode.SRC_IN))
        canvas.drawBitmap(bitmap, rect, rect, paint)
        
        return output