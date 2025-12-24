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

    public void start() {
        Log.i(TAG, "DEX Loaded. Targeting ExteraGram FAB fields...");
        try {
            // Эти поля мы берем из присланного тобой плагина customfab (2).plugin.py
            final String[] fabFields = {"floatingButtonContainer", "floatingButton2Container"};
            
            Class<?> dialogsActivity = Class.forName("org.telegram.ui.DialogsActivity");
            
            XposedBridge.hookMethod(dialogsActivity.getDeclaredMethod("createView", Context.class), new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) throws Throwable {
                    final Object fragment = param.thisObject;
                    final View rootView = (View) param.getResult();
                    if (rootView == null) return;

                    // Ждем, пока Телега создаст и раскрасит кнопки своими темами
                    rootView.postDelayed(() -> {
                        for (String fieldName : fabFields) {
                            try {
                                Field f = fragment.getClass().getDeclaredField(fieldName);
                                f.setAccessible(true);
                                View container = (View) f.get(fragment);
                                
                                if (container != null) {
                                    Log.i(TAG, "Targeting container: " + fieldName);
                                    applyAppleGlass(container);
                                }
                            } catch (Exception ignored) {}
                        }
                    }, 1200); // Увеличенная задержка для надежности
                }
            });
        } catch (Exception e) {
            Log.e(TAG, "Critical start error: " + e.getMessage());
        }
    }

    private void applyAppleGlass(View v) {
        // Убираем тени и старый фон, которые мешают стеклу
        v.setElevation(0);
        v.setBackground(new GlassDrawable());
        
        // Включаем Backdrop Blur (Android 12+)
        if (android.os.Build.VERSION.SDK_INT >= 31) {
            try {
                // Размытие фона за кнопкой
                v.setRenderEffect(RenderEffect.createBlurEffect(30f, 30f, Shader.TileMode.CLAMP));
            } catch (Exception ignored) {}
        }

        // Apple Liquid анимация
        v.setOnTouchListener((view, ev) -> {
            int action = ev.getAction();
            if (action == MotionEvent.ACTION_DOWN) {
                view.animate().scaleX(0.85f).scaleY(0.85f).alpha(0.7f).setDuration(120).start();
            } else if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
                view.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(400)
                    .setInterpolator(new OvershootInterpolator(3.0f)).start();
            }
            return false;
        });
    }

    static class GlassDrawable extends Drawable {
        private final Paint glassPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint specPaint = new Paint(Paint.ANTI_ALIAS_FLAG);

        public GlassDrawable() {
            // Матовое тело (rgba 255, 255, 255, 0.4)
            glassPaint.setColor(Color.argb(100, 255, 255, 255));
            
            // Тонкий блик по краю (rgba 255, 255, 255, 0.6)
            specPaint.setStyle(Paint.Style.STROKE);
            specPaint.setStrokeWidth(3f);
            specPaint.setColor(Color.argb(150, 255, 255, 255));
        }

        @Override
        public void draw(Canvas canvas) {
            RectF rect = new RectF(getBounds());
            float rad = Math.min(rect.width(), rect.height()) / 2f;
            canvas.drawRoundRect(rect, rad, rad, glassPaint);
            canvas.drawRoundRect(rect, rad, rad, specPaint);
        }

        @Override public void setAlpha(int alpha) {}
        @Override public void setColorFilter(ColorFilter cf) {}
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    }
}
