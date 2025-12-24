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
        // Используем стандартный лог Android, чтобы не было ошибок типов
        Log.i(TAG, "DEX Loaded. Targeting Extera FAB containers...");
        try {
            // Хукаем главную страницу и экран чата
            hookClass("org.telegram.ui.DialogsActivity");
            hookClass("org.telegram.ui.ChatActivity");
        } catch (Exception e) {
            Log.e(TAG, "Hook error: " + e.toString());
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

                // Задержка, чтобы ExteraGram успел инициализировать FAB
                root.postDelayed(() -> {
                    // Поля из твоего custom_fab.plugin.py
                    String[] containers = {"floatingButtonContainer", "floatingButton2Container"};
                    String[] icons = {"floatingButton", "floatingButton2"};

                    for (int i = 0; i < containers.length; i++) {
                        try {
                            // 1. Достаем контейнер (FrameLayout)
                            Field fCont = fragment.getClass().getDeclaredField(containers[i]);
                            fCont.setAccessible(true);
                            View vCont = (View) fCont.get(fragment);

                            if (vCont != null) {
                                // 2. Очищаем фон и тень у иконки внутри (чтобы не мешали стеклу)
                                try {
                                    Field fIcon = fragment.getClass().getDeclaredField(icons[i]);
                                    fIcon.setAccessible(true);
                                    View vIcon = (View) fIcon.get(fragment);
                                    if (vIcon != null) {
                                        vIcon.setBackground(null);
                                        vIcon.setElevation(0);
                                    }
                                } catch (Exception ignored) {}

                                // 3. Накладываем эффект на контейнер
                                applyLiquidGlass(vCont);
                                Log.i(TAG, "Liquid Glass applied to " + containers[i]);
                            }
                        } catch (Exception ignored) {}
                    }
                }, 1200);
            }
        });
    }

    private void applyLiquidGlass(View v) {
        // Устанавливаем Apple Glass фон
        v.setBackground(new AppleGlass());
        v.setElevation(0); 

        // Нативное размытие для Android 12+
        if (android.os.Build.VERSION.SDK_INT >= 31) {
            try {
                v.setRenderEffect(RenderEffect.createBlurEffect(25f, 25f, Shader.TileMode.CLAMP));
            } catch (Exception ignored) {}
        }

        // Apple Liquid анимация (плавное сжатие + Overshoot отскок)
        v.setOnTouchListener((view, ev) -> {
            int action = ev.getAction();
            if (action == MotionEvent.ACTION_DOWN) {
                view.animate().scaleX(0.88f).scaleY(0.88f).alpha(0.7f).setDuration(150).start();
            } else if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
                view.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(450)
                    .setInterpolator(new OvershootInterpolator(3.0f)).start();
            }
            return false;
        });
    }

    // Отрисовка матового стекла
    static class AppleGlass extends Drawable {
        private final Paint g = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint b = new Paint(Paint.ANTI_ALIAS_FLAG);

        public AppleGlass() {
            g.setColor(0x82FFFFFF); // Frosted Body (50% белый)
            b.setStyle(Paint.Style.STROKE);
            b.setStrokeWidth(3f);
            b.setColor(0xB4FFFFFF); // Specular Highlight (70% белый)
        }

        @Override
        public void draw(Canvas canvas) {
            RectF r = new RectF(getBounds());
            float rad = Math.min(r.width(), r.height()) / 2f;
            canvas.drawRoundRect(r, rad, rad, g);
            canvas.drawRoundRect(r, rad, rad, b);
        }

        @Override public void setAlpha(int a) {}
        @Override public void setColorFilter(ColorFilter cf) {}
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    }
}
