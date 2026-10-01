#!/usr/bin/env python3
"""Installs the Kar home-screen widget into the generated Capacitor android/ project.
Idempotent: safe to run on every build. Run from the repo root after `npx cap add android`."""
import glob, os, re, sys

FILES = {
    'java/KarWidgetPlugin.java': r'''package com.example.karfarma;

import android.appwidget.AppWidgetManager;
import android.content.ComponentName;
import android.content.Context;
import android.os.Build;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "KarWidget")
public class KarWidgetPlugin extends Plugin {
    @PluginMethod
    public void update(PluginCall call) {
        Context c = getContext();
        c.getSharedPreferences("kar_widget", Context.MODE_PRIVATE).edit().putString("json", call.getString("json", "{}")).apply();
        KarWidgetProvider.refresh(c);
        call.resolve();
    }

    @PluginMethod
    public void pin(PluginCall call) {
        Context c = getContext();
        boolean ok = false;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            AppWidgetManager m = AppWidgetManager.getInstance(c);
            ok = m != null && m.isRequestPinAppWidgetSupported();
            if (ok) m.requestPinAppWidget(new ComponentName(c, KarWidgetProvider.class), null, null);
        }
        JSObject r = new JSObject();
        r.put("supported", ok);
        call.resolve(r);
    }
}
''',
    'java/KarWidgetProvider.java': r'''package com.example.karfarma;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.View;
import android.widget.RemoteViews;
import androidx.core.content.ContextCompat;
import org.json.JSONArray;
import org.json.JSONObject;
import com.example.karfarma.R;

public class KarWidgetProvider extends AppWidgetProvider {
    static final int[] ROW = {R.id.kw_r1, R.id.kw_r2, R.id.kw_r3}, ACC = {R.id.kw_acc1, R.id.kw_acc2, R.id.kw_acc3}, RING = {R.id.kw_ring1, R.id.kw_ring2, R.id.kw_ring3}, AV = {R.id.kw_av1, R.id.kw_av2, R.id.kw_av3}, NAME = {R.id.kw_name1, R.id.kw_name2, R.id.kw_name3};
    static final int[] BD = {R.id.kw_bd1, R.id.kw_bd2, R.id.kw_bd3}, JOB = {R.id.kw_job1, R.id.kw_job2, R.id.kw_job3}, REM = {R.id.kw_rem1, R.id.kw_rem2, R.id.kw_rem3}, META = {R.id.kw_meta1, R.id.kw_meta2, R.id.kw_meta3}, BAR = {R.id.kw_bar1, R.id.kw_bar2, R.id.kw_bar3};
    static final int[] SV = {R.id.kw_sv1, R.id.kw_sv2, R.id.kw_sv3}, SL = {R.id.kw_sl1, R.id.kw_sl2, R.id.kw_sl3};

    static void refresh(Context c) {
        AppWidgetManager m = AppWidgetManager.getInstance(c);
        for (int id : m.getAppWidgetIds(new ComponentName(c, KarWidgetProvider.class))) m.updateAppWidget(id, build(c, m, id));
    }

    @Override
    public void onUpdate(Context c, AppWidgetManager m, int[] ids) {
        for (int id : ids) m.updateAppWidget(id, build(c, m, id));
    }

    @Override
    public void onAppWidgetOptionsChanged(Context c, AppWidgetManager m, int id, Bundle o) {
        m.updateAppWidget(id, build(c, m, id));
    }

    static int clr(Context c, int res) { return ContextCompat.getColor(c, res); }

    static int parse(String s, int def) {
        try { return Color.parseColor(s); } catch (Exception e) { return def; }
    }

    static RemoteViews build(Context c, AppWidgetManager m, int wid) {
        RemoteViews v = new RemoteViews(c.getPackageName(), R.layout.kar_widget);
        Intent open = c.getPackageManager().getLaunchIntentForPackage(c.getPackageName());
        if (open != null) v.setOnClickPendingIntent(R.id.kw_root, PendingIntent.getActivity(c, 0, open, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT));

        float d = c.getResources().getDisplayMetrics().density;
        int wDp = 0, hDp = 0;
        try {
            Bundle op = m.getAppWidgetOptions(wid);
            wDp = op.getInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH, 0);
            hDp = op.getInt(AppWidgetManager.OPTION_APPWIDGET_MAX_HEIGHT, 0);
        } catch (Exception ignored) { }
        if (wDp < 120) wDp = 300;
        if (hDp < 80) hDp = 230;
        boolean showStats = hDp >= 190;
        int rowsMax = Math.max(1, Math.min(3, (int) ((hDp - 56 - 14 - (showStats ? 50 : 0)) / 98f)));

        int track = clr(c, R.color.kw_track), txt = clr(c, R.color.kw_text);
        try {
            JSONObject o = new JSONObject(c.getSharedPreferences("kar_widget", Context.MODE_PRIVATE).getString("json", "{}"));
            JSONArray a = o.optJSONArray("rows"), st = o.optJSONArray("stats");
            int n = a == null ? 0 : Math.min(a.length(), rowsMax);

            String title = o.optString("title", "");
            v.setTextViewText(R.id.kw_title, title.isEmpty() ? "ویجت پیشرفت کار جاری" : title);
            String sub = o.optString("sub", "");
            v.setTextViewText(R.id.kw_sub, sub.isEmpty() ? "کار جاری ندارید" : sub);
            String pill = o.optString("pill", "");
            v.setViewVisibility(R.id.kw_pill, pill.isEmpty() ? View.GONE : View.VISIBLE);
            if (!pill.isEmpty()) {
                v.setTextViewText(R.id.kw_pill, pill);
                v.setTextColor(R.id.kw_pill, parse(o.optString("pillColor", "#6D28D9"), 0xFF6D28D9));
            }

            v.setViewVisibility(R.id.kw_empty, n == 0 ? View.VISIBLE : View.GONE);
            int ringPx = (int) (54 * d), avPx = (int) (22 * d), barH = Math.max(6, (int) (6 * d));
            int barW = Math.max((int) (100 * d), (int) ((wDp - 56) * d));

            for (int k = 0; k < 3; k++) {
                boolean has = k < n;
                v.setViewVisibility(ROW[k], has ? View.VISIBLE : View.GONE);
                if (!has) continue;
                JSONObject r = a.getJSONObject(k);
                String key = r.optString("key", "ok");
                int col = parse(r.optString("color", "#10b981"), 0xFF10B981);
                int pct = r.optInt("pct");

                v.setImageViewBitmap(RING[k], ring(ringPx, pct, col, r.optString("ptxt", pct + "٪"), track, txt));
                v.setImageViewBitmap(BAR[k], bar(barW, barH, pct, col, track));
                v.setInt(ACC[k], "setBackgroundColor", col);

                String name = r.optString("name", "");
                v.setTextViewText(NAME[k], name.isEmpty() ? "وضعیت کار جاری" : name);
                if (!name.isEmpty()) {
                    v.setImageViewBitmap(AV[k], avatar(avPx, r.optString("ini", "؟"), parse(r.optString("g0", "#6366f1"), 0xFF6366F1), parse(r.optString("g1", "#8b5cf6"), 0xFF8B5CF6)));
                    v.setViewVisibility(AV[k], View.VISIBLE);
                } else v.setViewVisibility(AV[k], View.GONE);

                int bdRes, bdFg; String bdTx;
                switch (key) {
                    case "idle":   bdRes = R.drawable.kar_badge_idle;   bdFg = R.color.kw_bd_idle_fg;   bdTx = "بدون کار جاری"; break;
                    case "warn":   bdRes = R.drawable.kar_badge_warn;   bdFg = R.color.kw_bd_warn_fg;   bdTx = "در حال کار"; break;
                    case "urgent": bdRes = R.drawable.kar_badge_urgent; bdFg = R.color.kw_bd_urgent_fg; bdTx = "نزدیک موعد"; break;
                    case "late":   bdRes = R.drawable.kar_badge_late;   bdFg = R.color.kw_bd_late_fg;   bdTx = "دارای تاخیر"; break;
                    default:       bdRes = R.drawable.kar_badge_ok;     bdFg = R.color.kw_bd_ok_fg;     bdTx = "در حال کار";
                }
                v.setInt(BD[k], "setBackgroundResource", bdRes);
                v.setTextColor(BD[k], clr(c, bdFg));
                v.setTextViewText(BD[k], bdTx);

                v.setTextViewText(JOB[k], r.optString("job", ""));
                v.setTextViewText(REM[k], r.optString("rem", ""));
                v.setTextColor(REM[k], clr(c, r.optBoolean("over") ? R.color.kw_bd_late_fg : R.color.kw_text_sub));
                v.setTextViewText(META[k], r.optString("meta", ""));
            }

            boolean sv = showStats && st != null && st.length() >= 3;
            v.setViewVisibility(R.id.kw_st, sv ? View.VISIBLE : View.GONE);
            if (sv) for (int k = 0; k < 3; k++) {
                JSONObject s = st.getJSONObject(k);
                v.setTextViewText(SV[k], s.optString("v", "—"));
                v.setTextViewText(SL[k], s.optString("l", ""));
            }
        } catch (Exception ignored) { }
        return v;
    }

    static Bitmap ring(int s, int pct, int col, String txt, int track, int tcol) {
        Bitmap b = Bitmap.createBitmap(s, s, Bitmap.Config.ARGB_8888);
        Canvas cv = new Canvas(b);
        float sw = s * 0.095f, pad = sw / 2f + s * 0.06f;
        RectF rf = new RectF(pad, pad, s - pad, s - pad);
        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(sw);
        p.setColor(track);
        cv.drawOval(rf, p);
        float ratio = Math.max(0f, Math.min(1f, pct / 100f));
        if (ratio > 0f) {
            p.setColor(col);
            p.setStrokeCap(Paint.Cap.ROUND);
            p.setShadowLayer(s * 0.05f, 0, 0, (col & 0x00FFFFFF) | 0x80000000);
            cv.drawArc(rf, -90f, 360f * ratio, false, p);
        }
        Paint t = new Paint(Paint.ANTI_ALIAS_FLAG);
        t.setColor(tcol);
        t.setTextAlign(Paint.Align.CENTER);
        t.setTypeface(Typeface.DEFAULT_BOLD);
        t.setTextSize(s * 0.25f);
        cv.drawText(txt, s / 2f, s / 2f - (t.ascent() + t.descent()) / 2f, t);
        return b;
    }

    static Bitmap bar(int w, int h, int pct, int col, int track) {
        Bitmap b = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        Canvas cv = new Canvas(b);
        float r = h / 2f;
        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        p.setColor(track);
        cv.drawRoundRect(new RectF(0, 0, w, h), r, r, p);
        if (pct > 0) {
            float fw = Math.max(h, w * Math.min(100, pct) / 100f), left = w - fw;
            RectF f = new RectF(left, 0, w, h);
            p.setColor(col);
            cv.drawRoundRect(f, r, r, p);
            p.setShader(new LinearGradient(left + fw * 0.1f, 0, left + fw * 0.55f, 0, new int[]{0x00FFFFFF, 0x66FFFFFF, 0x00FFFFFF}, null, Shader.TileMode.CLAMP));
            cv.drawRoundRect(f, r, r, p);
        }
        return b;
    }

    static Bitmap avatar(int s, String ini, int g0, int g1) {
        Bitmap b = Bitmap.createBitmap(s, s, Bitmap.Config.ARGB_8888);
        Canvas cv = new Canvas(b);
        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        p.setShader(new LinearGradient(0, 0, s, s, g0, g1, Shader.TileMode.CLAMP));
        cv.drawRoundRect(new RectF(0, 0, s, s), s * 0.3f, s * 0.3f, p);
        Paint t = new Paint(Paint.ANTI_ALIAS_FLAG);
        t.setColor(Color.WHITE);
        t.setTextAlign(Paint.Align.CENTER);
        t.setTypeface(Typeface.DEFAULT_BOLD);
        t.setTextSize(s * 0.4f);
        cv.drawText(ini, s / 2f, s / 2f - (t.ascent() + t.descent()) / 2f, t);
        return b;
    }
}
''',
    'res/layout/kar_widget.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/kw_root"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="@drawable/kar_widget_bg"
    android:layoutDirection="rtl"
    android:orientation="vertical">

    <LinearLayout
        android:id="@+id/kw_head"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:background="@drawable/kar_widget_head"
        android:gravity="center_vertical"
        android:orientation="horizontal"
        android:paddingStart="14dp"
        android:paddingTop="10dp"
        android:paddingEnd="14dp"
        android:paddingBottom="10dp">

        <TextView
            android:layout_width="32dp"
            android:layout_height="32dp"
            android:background="@drawable/kar_widget_ico"
            android:gravity="center"
            android:text="⏱"
            android:textColor="#FFFFFF"
            android:textSize="16sp" />

        <LinearLayout
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_marginStart="10dp"
            android:layout_weight="1"
            android:orientation="vertical">

            <TextView
                android:id="@+id/kw_title"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:ellipsize="end"
                android:maxLines="1"
                android:text="ویجت پیشرفت کار جاری"
                android:textColor="#FFFFFF"
                android:textDirection="rtl"
                android:textSize="13sp"
                android:textStyle="bold" />

            <TextView
                android:id="@+id/kw_sub"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:ellipsize="end"
                android:maxLines="1"
                android:text="کار جاری ندارید"
                android:textColor="@color/kw_head_sub"
                android:textDirection="rtl"
                android:textSize="10.5sp" />
        </LinearLayout>

        <TextView
            android:id="@+id/kw_pill"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_marginStart="8dp"
            android:background="@drawable/kar_widget_pill"
            android:paddingStart="11dp"
            android:paddingTop="4dp"
            android:paddingEnd="11dp"
            android:paddingBottom="4dp"
            android:maxLines="1"
            android:textColor="#6D28D9"
            android:textDirection="rtl"
            android:textSize="11sp"
            android:textStyle="bold"
            android:visibility="gone" />
    </LinearLayout>

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_weight="1"
        android:orientation="vertical"
        android:paddingStart="10dp"
        android:paddingTop="2dp"
        android:paddingEnd="10dp"
        android:paddingBottom="10dp">

    <LinearLayout
        android:id="@+id/kw_r1"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="6dp"
        android:background="@drawable/kar_widget_card"
        android:orientation="horizontal"
        android:padding="10dp"
        android:visibility="gone">

        <ImageView
            android:id="@+id/kw_acc1"
            android:layout_width="3dp"
            android:layout_height="match_parent"
            android:layout_marginTop="2dp"
            android:layout_marginBottom="2dp"
            android:layout_marginEnd="8dp" />

        <LinearLayout
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:orientation="vertical">

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:gravity="center_vertical"
                android:orientation="horizontal">

                <ImageView
                    android:id="@+id/kw_ring1"
                    android:layout_width="54dp"
                    android:layout_height="54dp"
                    android:layout_marginEnd="10dp"
                    android:scaleType="fitCenter" />

                <LinearLayout
                    android:layout_width="0dp"
                    android:layout_height="wrap_content"
                    android:layout_weight="1"
                    android:orientation="vertical">

                    <LinearLayout
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:gravity="center_vertical"
                        android:orientation="horizontal">

                        <ImageView
                            android:id="@+id/kw_av1"
                            android:layout_width="22dp"
                            android:layout_height="22dp"
                            android:layout_marginEnd="6dp"
                            android:scaleType="fitCenter"
                            android:visibility="gone" />

                        <TextView
                            android:id="@+id/kw_name1"
                            android:layout_width="0dp"
                            android:layout_height="wrap_content"
                            android:layout_weight="1"
                            android:ellipsize="end"
                            android:maxLines="1"
                            android:textColor="@color/kw_text"
                            android:textDirection="rtl"
                            android:textSize="13sp"
                            android:textStyle="bold" />

                        <TextView
                            android:id="@+id/kw_bd1"
                            android:layout_width="wrap_content"
                            android:layout_height="wrap_content"
                            android:layout_marginStart="6dp"
                            android:background="@drawable/kar_badge_ok"
                            android:paddingStart="8dp"
                            android:paddingTop="2dp"
                            android:paddingEnd="8dp"
                            android:paddingBottom="2dp"
                            android:maxLines="1"
                            android:textDirection="rtl"
                            android:textSize="9.5sp"
                            android:textStyle="bold" />
                    </LinearLayout>

                    <TextView
                        android:id="@+id/kw_job1"
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:layout_marginTop="2dp"
                        android:ellipsize="end"
                        android:maxLines="1"
                        android:textColor="@color/kw_text"
                        android:textDirection="rtl"
                        android:textSize="11.5sp"
                        android:textStyle="bold" />

                    <TextView
                        android:id="@+id/kw_rem1"
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:layout_marginTop="1dp"
                        android:ellipsize="end"
                        android:maxLines="1"
                        android:textColor="@color/kw_text_sub"
                        android:textDirection="rtl"
                        android:textSize="11sp" />

                    <TextView
                        android:id="@+id/kw_meta1"
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:layout_marginTop="1dp"
                        android:ellipsize="end"
                        android:maxLines="1"
                        android:textColor="@color/kw_text_meta"
                        android:textDirection="rtl"
                        android:textSize="9.5sp" />
                </LinearLayout>
            </LinearLayout>

            <ImageView
                android:id="@+id/kw_bar1"
                android:layout_width="match_parent"
                android:layout_height="6dp"
                android:layout_marginTop="8dp"
                android:scaleType="fitXY" />
        </LinearLayout>
    </LinearLayout>

    <LinearLayout
        android:id="@+id/kw_r2"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="6dp"
        android:background="@drawable/kar_widget_card"
        android:orientation="horizontal"
        android:padding="10dp"
        android:visibility="gone">

        <ImageView
            android:id="@+id/kw_acc2"
            android:layout_width="3dp"
            android:layout_height="match_parent"
            android:layout_marginTop="2dp"
            android:layout_marginBottom="2dp"
            android:layout_marginEnd="8dp" />

        <LinearLayout
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:orientation="vertical">

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:gravity="center_vertical"
                android:orientation="horizontal">

                <ImageView
                    android:id="@+id/kw_ring2"
                    android:layout_width="54dp"
                    android:layout_height="54dp"
                    android:layout_marginEnd="10dp"
                    android:scaleType="fitCenter" />

                <LinearLayout
                    android:layout_width="0dp"
                    android:layout_height="wrap_content"
                    android:layout_weight="1"
                    android:orientation="vertical">

                    <LinearLayout
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:gravity="center_vertical"
                        android:orientation="horizontal">

                        <ImageView
                            android:id="@+id/kw_av2"
                            android:layout_width="22dp"
                            android:layout_height="22dp"
                            android:layout_marginEnd="6dp"
                            android:scaleType="fitCenter"
                            android:visibility="gone" />

                        <TextView
                            android:id="@+id/kw_name2"
                            android:layout_width="0dp"
                            android:layout_height="wrap_content"
                            android:layout_weight="1"
                            android:ellipsize="end"
                            android:maxLines="1"
                            android:textColor="@color/kw_text"
                            android:textDirection="rtl"
                            android:textSize="13sp"
                            android:textStyle="bold" />

                        <TextView
                            android:id="@+id/kw_bd2"
                            android:layout_width="wrap_content"
                            android:layout_height="wrap_content"
                            android:layout_marginStart="6dp"
                            android:background="@drawable/kar_badge_ok"
                            android:paddingStart="8dp"
                            android:paddingTop="2dp"
                            android:paddingEnd="8dp"
                            android:paddingBottom="2dp"
                            android:maxLines="1"
                            android:textDirection="rtl"
                            android:textSize="9.5sp"
                            android:textStyle="bold" />
                    </LinearLayout>

                    <TextView
                        android:id="@+id/kw_job2"
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:layout_marginTop="2dp"
                        android:ellipsize="end"
                        android:maxLines="1"
                        android:textColor="@color/kw_text"
                        android:textDirection="rtl"
                        android:textSize="11.5sp"
                        android:textStyle="bold" />

                    <TextView
                        android:id="@+id/kw_rem2"
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:layout_marginTop="1dp"
                        android:ellipsize="end"
                        android:maxLines="1"
                        android:textColor="@color/kw_text_sub"
                        android:textDirection="rtl"
                        android:textSize="11sp" />

                    <TextView
                        android:id="@+id/kw_meta2"
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:layout_marginTop="1dp"
                        android:ellipsize="end"
                        android:maxLines="1"
                        android:textColor="@color/kw_text_meta"
                        android:textDirection="rtl"
                        android:textSize="9.5sp" />
                </LinearLayout>
            </LinearLayout>

            <ImageView
                android:id="@+id/kw_bar2"
                android:layout_width="match_parent"
                android:layout_height="6dp"
                android:layout_marginTop="8dp"
                android:scaleType="fitXY" />
        </LinearLayout>
    </LinearLayout>

    <LinearLayout
        android:id="@+id/kw_r3"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="6dp"
        android:background="@drawable/kar_widget_card"
        android:orientation="horizontal"
        android:padding="10dp"
        android:visibility="gone">

        <ImageView
            android:id="@+id/kw_acc3"
            android:layout_width="3dp"
            android:layout_height="match_parent"
            android:layout_marginTop="2dp"
            android:layout_marginBottom="2dp"
            android:layout_marginEnd="8dp" />

        <LinearLayout
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:orientation="vertical">

            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:gravity="center_vertical"
                android:orientation="horizontal">

                <ImageView
                    android:id="@+id/kw_ring3"
                    android:layout_width="54dp"
                    android:layout_height="54dp"
                    android:layout_marginEnd="10dp"
                    android:scaleType="fitCenter" />

                <LinearLayout
                    android:layout_width="0dp"
                    android:layout_height="wrap_content"
                    android:layout_weight="1"
                    android:orientation="vertical">

                    <LinearLayout
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:gravity="center_vertical"
                        android:orientation="horizontal">

                        <ImageView
                            android:id="@+id/kw_av3"
                            android:layout_width="22dp"
                            android:layout_height="22dp"
                            android:layout_marginEnd="6dp"
                            android:scaleType="fitCenter"
                            android:visibility="gone" />

                        <TextView
                            android:id="@+id/kw_name3"
                            android:layout_width="0dp"
                            android:layout_height="wrap_content"
                            android:layout_weight="1"
                            android:ellipsize="end"
                            android:maxLines="1"
                            android:textColor="@color/kw_text"
                            android:textDirection="rtl"
                            android:textSize="13sp"
                            android:textStyle="bold" />

                        <TextView
                            android:id="@+id/kw_bd3"
                            android:layout_width="wrap_content"
                            android:layout_height="wrap_content"
                            android:layout_marginStart="6dp"
                            android:background="@drawable/kar_badge_ok"
                            android:paddingStart="8dp"
                            android:paddingTop="2dp"
                            android:paddingEnd="8dp"
                            android:paddingBottom="2dp"
                            android:maxLines="1"
                            android:textDirection="rtl"
                            android:textSize="9.5sp"
                            android:textStyle="bold" />
                    </LinearLayout>

                    <TextView
                        android:id="@+id/kw_job3"
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:layout_marginTop="2dp"
                        android:ellipsize="end"
                        android:maxLines="1"
                        android:textColor="@color/kw_text"
                        android:textDirection="rtl"
                        android:textSize="11.5sp"
                        android:textStyle="bold" />

                    <TextView
                        android:id="@+id/kw_rem3"
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:layout_marginTop="1dp"
                        android:ellipsize="end"
                        android:maxLines="1"
                        android:textColor="@color/kw_text_sub"
                        android:textDirection="rtl"
                        android:textSize="11sp" />

                    <TextView
                        android:id="@+id/kw_meta3"
                        android:layout_width="match_parent"
                        android:layout_height="wrap_content"
                        android:layout_marginTop="1dp"
                        android:ellipsize="end"
                        android:maxLines="1"
                        android:textColor="@color/kw_text_meta"
                        android:textDirection="rtl"
                        android:textSize="9.5sp" />
                </LinearLayout>
            </LinearLayout>

            <ImageView
                android:id="@+id/kw_bar3"
                android:layout_width="match_parent"
                android:layout_height="6dp"
                android:layout_marginTop="8dp"
                android:scaleType="fitXY" />
        </LinearLayout>
    </LinearLayout>

    <TextView
        android:id="@+id/kw_empty"
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_weight="1"
        android:gravity="center"
        android:text="☕  کار جاری ندارید"
        android:textColor="@color/kw_text_meta"
        android:textDirection="rtl"
        android:textSize="12.5sp" />

    <LinearLayout
        android:id="@+id/kw_st"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="6dp"
        android:orientation="horizontal"
        android:visibility="gone">

    <LinearLayout
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_weight="1"
        android:background="@drawable/kar_widget_stat"
        android:gravity="center"
        android:orientation="vertical"
        android:paddingTop="5dp"
        android:paddingBottom="5dp">

        <TextView
            android:id="@+id/kw_sv1"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:textColor="@color/kw_text"
            android:textDirection="rtl"
            android:textSize="13sp"
            android:textStyle="bold" />

        <TextView
            android:id="@+id/kw_sl1"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:textColor="@color/kw_text_sub"
            android:textDirection="rtl"
            android:textSize="10sp" />
    </LinearLayout>

    <LinearLayout
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_weight="1"
        android:layout_marginStart="6dp"
        android:background="@drawable/kar_widget_stat"
        android:gravity="center"
        android:orientation="vertical"
        android:paddingTop="5dp"
        android:paddingBottom="5dp">

        <TextView
            android:id="@+id/kw_sv2"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:textColor="@color/kw_text"
            android:textDirection="rtl"
            android:textSize="13sp"
            android:textStyle="bold" />

        <TextView
            android:id="@+id/kw_sl2"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:textColor="@color/kw_text_sub"
            android:textDirection="rtl"
            android:textSize="10sp" />
    </LinearLayout>

    <LinearLayout
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_weight="1"
        android:layout_marginStart="6dp"
        android:background="@drawable/kar_widget_stat"
        android:gravity="center"
        android:orientation="vertical"
        android:paddingTop="5dp"
        android:paddingBottom="5dp">

        <TextView
            android:id="@+id/kw_sv3"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:textColor="@color/kw_text"
            android:textDirection="rtl"
            android:textSize="13sp"
            android:textStyle="bold" />

        <TextView
            android:id="@+id/kw_sl3"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:textColor="@color/kw_text_sub"
            android:textDirection="rtl"
            android:textSize="10sp" />
    </LinearLayout>
    </LinearLayout>
    </LinearLayout>
</LinearLayout>
''',
    'res/values/kar_widget_colors.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="kw_bg">#FFFFFF</color>
    <color name="kw_stroke">#CBD5E1</color>
    <color name="kw_text">#1E293B</color>
    <color name="kw_text_sub">#64748B</color>
    <color name="kw_text_meta">#94A3B8</color>
    <color name="kw_track">#E2E8F0</color>
    <color name="kw_fill">#10B981</color>
    <color name="kw_card_bg">#F8FAFC</color>
    <color name="kw_card_stroke">#E2E8F0</color>
    <color name="kw_stat_bg">#F1F5F9</color>
    <color name="kw_head_sub">#E6FFFFFF</color>
    <color name="kw_bd_ok_bg">#D1FAE5</color>
    <color name="kw_bd_ok_fg">#047857</color>
    <color name="kw_bd_warn_bg">#FEF3C7</color>
    <color name="kw_bd_warn_fg">#B45309</color>
    <color name="kw_bd_urgent_bg">#FFEDD5</color>
    <color name="kw_bd_urgent_fg">#C2410C</color>
    <color name="kw_bd_late_bg">#FFE4E6</color>
    <color name="kw_bd_late_fg">#BE123C</color>
    <color name="kw_bd_idle_bg">#E2E8F0</color>
    <color name="kw_bd_idle_fg">#475569</color>
</resources>
''',
    'res/values-night/kar_widget_colors.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="kw_bg">#0F172A</color>
    <color name="kw_stroke">#475569</color>
    <color name="kw_text">#F1F5F9</color>
    <color name="kw_text_sub">#94A3B8</color>
    <color name="kw_text_meta">#94A3B8</color>
    <color name="kw_track">#334155</color>
    <color name="kw_fill">#10B981</color>
    <color name="kw_card_bg">#1E293B</color>
    <color name="kw_card_stroke">#334155</color>
    <color name="kw_stat_bg">#8C334155</color>
    <color name="kw_head_sub">#E6FFFFFF</color>
    <color name="kw_bd_ok_bg">#2910B981</color>
    <color name="kw_bd_ok_fg">#6EE7B7</color>
    <color name="kw_bd_warn_bg">#29F59E0B</color>
    <color name="kw_bd_warn_fg">#FCD34D</color>
    <color name="kw_bd_urgent_bg">#29F97316</color>
    <color name="kw_bd_urgent_fg">#FDBA74</color>
    <color name="kw_bd_late_bg">#2EE11D48</color>
    <color name="kw_bd_late_fg">#FDA4AF</color>
    <color name="kw_bd_idle_bg">#2994A3B8</color>
    <color name="kw_bd_idle_fg">#CBD5E1</color>
</resources>
''',
    'res/drawable/kar_widget_bg.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="@color/kw_bg" />
    <stroke android:width="1dp" android:color="@color/kw_stroke" />
    <corners android:radius="20dp" />
</shape>
''',
    'res/drawable/kar_widget_card.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="@color/kw_card_bg" />
    <stroke android:width="1dp" android:color="@color/kw_card_stroke" />
    <corners android:radius="14dp" />
</shape>
''',
    'res/drawable/kar_widget_stat.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="@color/kw_stat_bg" />
    <corners android:radius="10dp" />
</shape>
''',
    'res/drawable/kar_widget_pill.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#FFFFFF" />
    <corners android:radius="14dp" />
</shape>
''',
    'res/drawable/kar_widget_ico.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="#33FFFFFF" />
    <stroke android:width="1dp" android:color="#4DFFFFFF" />
    <corners android:radius="10dp" />
</shape>
''',
    'res/drawable/kar_widget_head.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <gradient android:angle="315" android:startColor="#4F46E5" android:centerColor="#7C3AED" android:endColor="#A855F7" />
    <corners android:topLeftRadius="19dp" android:topRightRadius="19dp" />
</shape>
''',
    'res/xml/kar_widget_info.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:minWidth="250dp"
    android:minHeight="180dp"
    android:minResizeWidth="180dp"
    android:minResizeHeight="110dp"
    android:targetCellWidth="4"
    android:targetCellHeight="3"
    android:updatePeriodMillis="1800000"
    android:initialLayout="@layout/kar_widget"
    android:resizeMode="horizontal|vertical"
    android:widgetCategory="home_screen" />
''',
    'res/drawable/kar_badge_ok.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="@color/kw_bd_ok_bg" />
    <corners android:radius="12dp" />
</shape>
''',
    'res/drawable/kar_badge_warn.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="@color/kw_bd_warn_bg" />
    <corners android:radius="12dp" />
</shape>
''',
    'res/drawable/kar_badge_urgent.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="@color/kw_bd_urgent_bg" />
    <corners android:radius="12dp" />
</shape>
''',
    'res/drawable/kar_badge_late.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="@color/kw_bd_late_bg" />
    <corners android:radius="12dp" />
</shape>
''',
    'res/drawable/kar_badge_idle.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="@color/kw_bd_idle_bg" />
    <corners android:radius="12dp" />
</shape>
''',
}

STALE = ['res/drawable/kar_widget_progress.xml']

ANDROID = 'android'
MAIN = os.path.join(ANDROID, 'app', 'src', 'main')

def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()

def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)

# ---- 1. find MainActivity and package ----
mains = glob.glob(os.path.join(MAIN, 'java', '**', 'MainActivity.java'), recursive=True)
if not mains:
    sys.exit('ERROR: MainActivity.java not found under ' + MAIN)
main_path = mains[0]
main_src = read(main_path)
pkg = re.search(r'^package\s+([\w.]+)\s*;', main_src, re.M).group(1)

ns = pkg
for g in ('app/build.gradle', 'app/build.gradle.kts'):
    gp = os.path.join(ANDROID, g)
    if os.path.exists(gp):
        m = re.search(r'namespace\s*=?\s*["\']([\w.]+)["\']', read(gp))
        if m:
            ns = m.group(1)
            break
print('package =', pkg, '| R namespace =', ns)

# ---- 2. copy java + res ----
java_dir = os.path.dirname(main_path)
for rel, content in FILES.items():
    if rel.startswith('java/'):
        content = re.sub(r'^package\s+[\w.]+\s*;', 'package ' + pkg + ';', content, count=1, flags=re.M)
        content = re.sub(r'^import\s+[\w.]+\.R;', 'import ' + ns + '.R;', content, flags=re.M)
        write(os.path.join(java_dir, os.path.basename(rel)), content)
    else:
        write(os.path.join(MAIN, rel), content)
for rel in STALE:
    sp = os.path.join(MAIN, rel)
    if os.path.exists(sp):
        os.remove(sp)
print('widget files copied')

# ---- 3. AndroidManifest: add receiver ----
mf_path = os.path.join(MAIN, 'AndroidManifest.xml')
mf = read(mf_path)
if 'KarWidgetProvider' not in mf:
    receiver = (
        '\n        <receiver android:name="' + pkg + '.KarWidgetProvider" android:exported="false">\n'
        '            <intent-filter>\n'
        '                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />\n'
        '            </intent-filter>\n'
        '            <meta-data android:name="android.appwidget.provider" android:resource="@xml/kar_widget_info" />\n'
        '        </receiver>\n'
    )
    if '</application>' not in mf:
        sys.exit('ERROR: </application> not found in AndroidManifest.xml')
    mf = mf.replace('</application>', receiver + '    </application>', 1)
    write(mf_path, mf)
    print('receiver added to manifest')
else:
    print('manifest already has receiver')

# ---- 4. MainActivity: register plugin ----
if 'registerPlugin(KarWidgetPlugin.class)' in main_src:
    print('plugin already registered')
else:
    if 'import android.os.Bundle;' not in main_src:
        main_src = re.sub(r'(^package\s+[\w.]+\s*;[ \t]*\n)', r'\1\nimport android.os.Bundle;\n', main_src, count=1, flags=re.M)
    if re.search(r'super\.onCreate\(', main_src):
        main_src = re.sub(r'([ \t]*)super\.onCreate\(', r'\1registerPlugin(KarWidgetPlugin.class);\n\1super.onCreate(', main_src, count=1)
    elif re.search(r'extends\s+BridgeActivity\s*\{\s*\}', main_src):
        main_src = re.sub(
            r'(extends\s+BridgeActivity\s*)\{\s*\}',
            r'\1{\n    @Override\n    public void onCreate(Bundle savedInstanceState) {\n        registerPlugin(KarWidgetPlugin.class);\n        super.onCreate(savedInstanceState);\n    }\n}',
            main_src, count=1)
    else:
        sys.exit('ERROR: could not patch MainActivity.java automatically')
    write(main_path, main_src)
    print('plugin registered in MainActivity')
