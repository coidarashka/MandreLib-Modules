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
        Log.i(TAG, "DEX Loaded successfully");
        try {
            // Список полей FAB из ExteraGram
            String[] fields = {"floatingButtonContainer", "floatingButton2Container", "floatingButton"};
            
            hookActivity("org.telegram.ui.DialogsActivity", fields);
            hookActivity("org.telegram.ui.ChatActivity", fields);
        } catch (Exception e) {
            Log.e(TAG, "Start error: " + e.getMessage());
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

                root.postDelayed(() -> {
                    for (String fName : fields) {
                        try {
                            Field f = fragment.getClass().getDeclaredField(fName);
                            f.setAccessible(true);
                            View fab = (View) f.get(fragment);
                            if (fab != null) {
                                Log.i(TAG, "Applying effect to: " + fName);
                                applyGlass(fab);
                            }
                        } catch (Exception ignored) {}
                    }
                }, 1000);
            }
        });
    }

    private void applyGlass(View v) {
        v.setBackground(new AppleGlass());
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
    }

    static class AppleGlass extends Drawable {
        private final Paint g = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint b = new Paint(Paint.ANTI_ALIAS_FLAG);
        public AppleGlass() {
            g.setColor(0x82FFFFFF); // 50% белый
            b.setStyle(Paint.Style.STROKE);
            b.setStrokeWidth(3f);
            b.setColor(0xB4FFFFFF); // Блик
        }
        @Override
        public void draw(Canvas c) {
            RectF r = new RectF(getBounds());
            float rad = Math.min(r.width(), r.height()) / 2f;
            c.drawRoundRect(r, rad, rad, g);
            c.drawRoundRect(r, rad, rad, b);
        }
        @Override public void setAlpha(int a) {}
        @Override public void setColorFilter(ColorFilter cf) {}
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    }
}
