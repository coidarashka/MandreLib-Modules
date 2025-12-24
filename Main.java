package b.liquidglass;

import android.content.Context;
import android.graphics.*;
import android.graphics.drawable.Drawable;
import android.view.*;
import android.view.animation.OvershootInterpolator;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import java.lang.reflect.Field;

public class Main {
    // Метод для вывода логов в консоль плагинов
    private void xLog(String m) {
        try { XposedBridge.log("[LiquidGlass] " + m); } catch(Throwable ignored) {}
    }

    // Входная точка для Loader
    public void start() {
        xLog("Plugin started. Targeting FAB...");
        try {
            // Поля контейнеров кнопок из Telegram и ExteraGram
            String[] targetFields = {"floatingButtonContainer", "floatingButton2Container", "floatingButton"};
            
            // Хукаем главную страницу (Dialogs) и экран чата (Chat)
            hookActivity("org.telegram.ui.DialogsActivity", targetFields);
            hookActivity("org.telegram.ui.ChatActivity", targetFields);
            
        } catch (Exception e) {
            xLog("Start Error: " + e.toString());
        }
    }

    private void hookActivity(String clsName, String[] fields) throws Exception {
        Class<?> cls = Class.forName(clsName);
        XposedBridge.hookMethod(cls.getDeclaredMethod("createView", Context.class), new XC_MethodHook() {
            @Override
            protected void afterHookedMethod(MethodHookParam p) throws Throwable {
                final Object fragment = p.thisObject;
                final View root = (View) p.getResult();
                if (root == null) return;

                // Небольшая задержка, чтобы UI успел прогрузиться
                root.postDelayed(() -> {
                    for (String fName : fields) {
                        try {
                            Field f = fragment.getClass().getDeclaredField(fName);
                            f.setAccessible(true);
                            View fab = (View) f.get(fragment);
                            if (fab != null) {
                                xLog("Found FAB field: " + fName);
                                applyLiquidGlass(fab);
                            }
                        } catch (Exception ignored) {}
                    }
                }, 800);
            }
        });
    }

    private void applyLiquidGlass(View v) {
        // 1. Устанавливаем матовое стекло
        v.setBackground(new GlassEffect());
        
        // 2. Настоящий Backdrop Blur (Android 12+)
        if (android.os.Build.VERSION.SDK_INT >= 31) {
            try {
                v.setRenderEffect(RenderEffect.createBlurEffect(25f, 25f, Shader.TileMode.CLAMP));
            } catch (Exception ignored) {}
        }

        // 3. Liquid Touch Animation (как на iOS)
        v.setOnTouchListener((v1, ev) -> {
            int action = ev.getAction();
            if (action == MotionEvent.ACTION_DOWN) {
                v1.animate().scaleX(0.88f).scaleY(0.88f).alpha(0.7f).setDuration(120).start();
            } else if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
                v1.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(450)
                    .setInterpolator(new OvershootInterpolator(3.0f)).start();
            }
            return false;
        });
    }

    // Кастомная отрисовка стекла
    static class GlassEffect extends Drawable {
        private final Paint glassPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint specPaint = new Paint(Paint.ANTI_ALIAS_FLAG);

        public GlassEffect() {
            // Основной слой: 50% белый (Frosted Glass)
            glassPaint.setColor(0x82FFFFFF); 
            
            // Тонкая яркая обводка: 70% белый (Specular Edge)
            specPaint.setStyle(Paint.Style.STROKE);
            specPaint.setStrokeWidth(3f);
            specPaint.setColor(0xB4FFFFFF);
        }

        @Override
        public void draw(Canvas c) {
            RectF rf = new RectF(getBounds());
            float radius = Math.min(rf.width(), rf.height()) / 2f;
            
            // Рисуем тело и блик
            c.drawRoundRect(rf, radius, radius, glassPaint);
            c.drawRoundRect(rf, radius, radius, specPaint);
        }

        @Override public void setAlpha(int a) {}
        @Override public void setColorFilter(ColorFilter cf) {}
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    }
}
