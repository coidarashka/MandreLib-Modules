package b.liquidglass;

import android.content.Context;
import android.graphics.*;
import android.graphics.drawable.Drawable;
import android.view.*;
import android.view.animation.OvershootInterpolator;
import android.util.Log;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import java.lang.reflect.Field;

public class Main {
    private static final String TAG = "LiquidGlass";

    // Метод для безопасного вывода логов в консоль
    private void xLog(String msg) {
        Log.i(TAG, msg);
        try {
            XposedBridge.log("[LG] " + msg);
        } catch (Throwable ignored) {}
    }

    public void start() {
        xLog("DEX Loaded. Targeting ExteraGram FAB...");
        try {
            // Хукаем главную страницу и экран чата
            hookClass("org.telegram.ui.DialogsActivity");
            hookClass("org.telegram.ui.ChatActivity");
        } catch (Exception e) {
            xLog("Start Error: " + e.toString());
        }
    }

    private void hookClass(String className) throws Exception {
        Class<?> clazz = Class.forName(className);
        XposedBridge.hookMethod(clazz.getDeclaredMethod("createView", Context.class), new XC_MethodHook() {
            @Override
            protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                final Object fragment = param.thisObject;
                final View root = (View) param.getResult();
                if (root == null) return;

                // Задержка, чтобы дождаться инициализации FAB в коде Telegram
                root.postDelayed(() -> {
                    String[] containerFields = {"floatingButtonContainer", "floatingButton2Container"};
                    String[] iconFields = {"floatingButton", "floatingButton2"};

                    for (int i = 0; i < containerFields.length; i++) {
                        try {
                            // 1. Ищем контейнер (FrameLayout)
                            Field fCont = fragment.getClass().getDeclaredField(containerFields[i]);
                            fCont.setAccessible(true);
                            View vCont = (View) fCont.get(fragment);

                            if (vCont != null) {
                                // 2. Ищем саму кнопку внутри и убираем стандартную краску/тени
                                try {
                                    Field fIcon = fragment.getClass().getDeclaredField(iconFields[i]);
                                    fIcon.setAccessible(true);
                                    View vIcon = (View) fIcon.get(fragment);
                                    if (vIcon != null) {
                                        vIcon.setBackground(null);
                                        vIcon.setElevation(0);
                                        if (vIcon instanceof android.widget.ImageView) {
                                            ((android.widget.ImageView)vIcon).setColorFilter(null);
                                        }
                                    }
                                } catch (Exception ignored) {}

                                // 3. Применяем эффект стекла на контейнер
                                applyLiquidGlass(vCont);
                                xLog("Effect applied to " + containerFields[i]);
                            }
                        } catch (Exception ignored) {}
                    }
                }, 1100);
            }
        });
    }

    private void applyLiquidGlass(View v) {
        // Устанавливаем Apple Glass Drawable
        v.setBackground(new AppleGlassDrawable());
        v.setElevation(0); // Убираем стандартную черную тень Android

        // Нативное размытие (Backdrop Blur) для Android 12+ (API 31)
        if (android.os.Build.VERSION.SDK_INT >= 31) {
            try {
                v.setRenderEffect(RenderEffect.createBlurEffect(25f, 25f, Shader.TileMode.CLAMP));
            } catch (Exception ignored) {}
        }

        // Liquid Touch Animation (плавное сжатие и "сочный" отскок)
        v.setOnTouchListener((view, ev) -> {
            int action = ev.getAction();
            if (action == MotionEvent.ACTION_DOWN) {
                view.animate().scaleX(0.88f).scaleY(0.88f).alpha(0.7f).setDuration(120).start();
            } else if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
                view.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(450)
                    .setInterpolator(new OvershootInterpolator(3.0f)).start();
            }
            return false;
        });
    }

    // Класс для отрисовки матового стекла
    static class AppleGlassDrawable extends Drawable {
        private final Paint glassPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint borderPaint = new Paint(Paint.ANTI_ALIAS_FLAG);

        public AppleGlassDrawable() {
            // Цвет самого "стекла" (белый с прозрачностью 50%)
            glassPaint.setColor(0x82FFFFFF); 
            
            // Тонкая обводка ( specular блик по краям )
            borderPaint.setStyle(Paint.Style.STROKE);
            borderPaint.setStrokeWidth(3f);
            borderPaint.setColor(0xB4FFFFFF); // Белый с прозрачностью 70%
        }

        @Override
        public void draw(Canvas canvas) {
            RectF rect = new RectF(getBounds());
            float rad = Math.min(rect.width(), rect.height()) / 2f;
            
            // Рисуем стекло и блик
            canvas.drawRoundRect(rect, rad, rad, glassPaint);
            canvas.drawRoundRect(rect, rad, rad, borderPaint);
        }

        @Override public void setAlpha(int alpha) {}
        @Override public void setColorFilter(ColorFilter cf) {}
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    }
}
