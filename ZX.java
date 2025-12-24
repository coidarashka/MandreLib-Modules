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
    private void xLog(String m) {
        XposedBridge.log("[LG] " + m);
    }

    public void start() {
        xLog("DEX Запущен. Цель: Extera FAB");
        try {
            hook("org.telegram.ui.DialogsActivity");
            hook("org.telegram.ui.ChatActivity");
        } catch (Exception e) {
            xLog("Ошибка хука: " + e.toString());
        }
    }

    private void hook(String clsName) throws Exception {
        Class<?> cls = Class.forName(clsName);
        XposedBridge.hookMethod(cls.getDeclaredMethod("createView", Context.class), new XC_MethodHook() {
            @Override
            protected void afterHookedMethod(MethodHookParam p) throws Throwable {
                final Object fragment = p.thisObject;
                final View root = (View) p.getResult();
                if (root == null) return;

                root.postDelayed(() -> {
                    // Список полей из твоего плагина
                    String[] containers = {"floatingButtonContainer", "floatingButton2Container"};
                    String[] icons = {"floatingButton", "floatingButton2"};

                    for (int i = 0; i < containers.length; i++) {
                        try {
                            // 1. Ищем контейнер
                            Field fCont = fragment.getClass().getDeclaredField(containers[i]);
                            fCont.setAccessible(true);
                            View vCont = (View) fCont.get(fragment);

                            if (vCont != null) {
                                xLog("Найден контейнер: " + containers[i]);
                                
                                // 2. Ищем иконку внутри и убираем ей фон
                                try {
                                    Field fIcon = fragment.getClass().getDeclaredField(icons[i]);
                                    fIcon.setAccessible(true);
                                    View vIcon = (View) fIcon.get(fragment);
                                    if (vIcon != null) {
                                        vIcon.setBackground(null);
                                        vIcon.setElevation(0);
                                        xLog("Очищен фон иконки: " + icons[i]);
                                    }
                                } catch(Exception ignored) {}

                                // 3. Красим контейнер в стекло
                                applyAppleEffect(vCont);
                            }
                        } catch (Exception ignored) {}
                    }
                }, 1200);
            }
        });
    }

    private void applyAppleEffect(View v) {
        v.setBackground(new AppleGlassDrawable());
        v.setElevation(0);
        
        if (android.os.Build.VERSION.SDK_INT >= 31) {
            try {
                v.setRenderEffect(RenderEffect.createBlurEffect(25f, 25f, Shader.TileMode.CLAMP));
            } catch (Exception ignored) {}
        }

        v.setOnTouchListener((v1, ev) -> {
            if (ev.getAction() == MotionEvent.ACTION_DOWN) {
                v1.animate().scaleX(0.88f).scaleY(0.88f).alpha(0.7f).setDuration(150).start();
            } else if (ev.getAction() == MotionEvent.ACTION_UP || ev.getAction() == MotionEvent.ACTION_CANCEL) {
                v1.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(450)
                    .setInterpolator(new OvershootInterpolator(3.0f)).start();
            }
            return false;
        });
        xLog("Эффект Liquid Glass применен успешно!");
    }

    static class AppleGlassDrawable extends Drawable {
        private final Paint glass = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint border = new Paint(Paint.ANTI_ALIAS_FLAG);

        public AppleGlassDrawable() {
            glass.setColor(0x99FFFFFF); // 60% белый
            border.setStyle(Paint.Style.STROKE);
            border.setStrokeWidth(3f);
            border.setColor(0xBFFFFFFF); // 75% белый (блик)
        }

        @Override
        public void draw(Canvas c) {
            RectF r = new RectF(getBounds());
            float rad = Math.min(r.width(), r.height()) / 2f;
            c.drawRoundRect(r, rad, rad, glass);
            c.drawRoundRect(r, rad, rad, border);
        }

        @Override public void setAlpha(int a) {}
        @Override public void setColorFilter(ColorFilter cf) {}
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    }
}
