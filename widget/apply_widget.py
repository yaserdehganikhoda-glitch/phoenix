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
import android.graphics.Color;
import android.view.View;
import android.widget.RemoteViews;
import org.json.JSONArray;
import org.json.JSONObject;
import com.example.karfarma.R;

public class KarWidgetProvider extends AppWidgetProvider {
    static void refresh(Context c) {
        AppWidgetManager m = AppWidgetManager.getInstance(c);
        for (int id : m.getAppWidgetIds(new ComponentName(c, KarWidgetProvider.class))) m.updateAppWidget(id, build(c));
    }

    @Override
    public void onUpdate(Context c, AppWidgetManager m, int[] ids) {
        for (int id : ids) m.updateAppWidget(id, build(c));
    }

    static RemoteViews build(Context c) {
        RemoteViews v = new RemoteViews(c.getPackageName(), R.layout.kar_widget);
        Intent open = c.getPackageManager().getLaunchIntentForPackage(c.getPackageName());
        if (open != null) v.setOnClickPendingIntent(R.id.kw_root, PendingIntent.getActivity(c, 0, open, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT));
        int[] rows = {R.id.kw_r1, R.id.kw_r2, R.id.kw_r3}, names = {R.id.kw_n1, R.id.kw_n2, R.id.kw_n3};
        int[] pcts = {R.id.kw_p1, R.id.kw_p2, R.id.kw_p3}, bars = {R.id.kw_b1, R.id.kw_b2, R.id.kw_b3};
        try {
            JSONObject o = new JSONObject(c.getSharedPreferences("kar_widget", Context.MODE_PRIVATE).getString("json", "{}"));
            JSONArray a = o.optJSONArray("rows");
            boolean emp = "employer".equals(o.optString("mode")), none = a == null || a.length() == 0;
            v.setTextViewText(R.id.kw_title, o.optString("title", "").isEmpty() ? "کارگاه هوشمند" : o.optString("title"));
            v.setTextViewText(R.id.kw_sub, none ? "کار جاری ندارید" : emp ? o.optInt("active") + " نفر در حال کار از " + o.optInt("total") + " • " + o.optInt("late") + " با تاخیر" : "پیشرفت کار جاری");
            for (int k = 0; k < 3; k++) {
                boolean has = !none && k < a.length();
                v.setViewVisibility(rows[k], has ? View.VISIBLE : View.GONE);
                if (!has) continue;
                JSONObject r = a.getJSONObject(k);
                int p = r.optInt("pct");
                v.setTextViewText(names[k], (emp ? r.optString("name") + " — " : "") + r.optString("job"));
                v.setTextViewText(pcts[k], p + "٪");
                v.setTextColor(pcts[k], Color.parseColor(r.optString("color", "#10b981")));
                v.setProgressBar(bars[k], 100, Math.min(100, p), false);
            }
        } catch (Exception ignored) { }
        return v;
    }
}
''',
    'res/drawable/kar_widget_bg.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="@color/kw_bg" />
    <stroke android:width="1dp" android:color="@color/kw_stroke" />
    <corners android:radius="20dp" />
</shape>
''',
    'res/drawable/kar_widget_progress.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:id="@android:id/background">
        <shape android:shape="rectangle">
            <solid android:color="@color/kw_track" />
            <corners android:radius="4dp" />
        </shape>
    </item>
    <item android:id="@android:id/progress">
        <clip>
            <shape android:shape="rectangle">
                <solid android:color="@color/kw_fill" />
                <corners android:radius="4dp" />
            </shape>
        </clip>
    </item>
</layer-list>
''',
    'res/layout/kar_widget.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/kw_root"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="@drawable/kar_widget_bg"
    android:orientation="vertical"
    android:padding="14dp">

    <TextView
        android:id="@+id/kw_title"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:ellipsize="end"
        android:maxLines="1"
        android:text="کارگاه هوشمند"
        android:textColor="@color/kw_text"
        android:textDirection="rtl"
        android:textSize="14sp"
        android:textStyle="bold" />

    <TextView
        android:id="@+id/kw_sub"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="2dp"
        android:ellipsize="end"
        android:maxLines="1"
        android:text="کار جاری ندارید"
        android:textColor="@color/kw_text_sub"
        android:textDirection="rtl"
        android:textSize="11sp" />

    <LinearLayout
        android:id="@+id/kw_r1"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="8dp"
        android:orientation="vertical">

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="horizontal">

            <TextView
                android:id="@+id/kw_n1"
                android:layout_width="0dp"
                android:layout_height="wrap_content"
                android:layout_weight="1"
                android:ellipsize="end"
                android:maxLines="1"
                android:textColor="@color/kw_text"
                android:textDirection="rtl"
                android:textSize="12sp" />

            <TextView
                android:id="@+id/kw_p1"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_marginStart="8dp"
                android:textColor="@color/kw_fill"
                android:textSize="12sp"
                android:textStyle="bold" />
        </LinearLayout>

        <ProgressBar
            android:id="@+id/kw_b1"
            style="?android:attr/progressBarStyleHorizontal"
            android:layout_width="match_parent"
            android:layout_height="6dp"
            android:layout_marginTop="4dp"
            android:max="100"
            android:progress="0"
            android:progressDrawable="@drawable/kar_widget_progress" />
    </LinearLayout>

    <LinearLayout
        android:id="@+id/kw_r2"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="8dp"
        android:orientation="vertical">

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="horizontal">

            <TextView
                android:id="@+id/kw_n2"
                android:layout_width="0dp"
                android:layout_height="wrap_content"
                android:layout_weight="1"
                android:ellipsize="end"
                android:maxLines="1"
                android:textColor="@color/kw_text"
                android:textDirection="rtl"
                android:textSize="12sp" />

            <TextView
                android:id="@+id/kw_p2"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_marginStart="8dp"
                android:textColor="@color/kw_fill"
                android:textSize="12sp"
                android:textStyle="bold" />
        </LinearLayout>

        <ProgressBar
            android:id="@+id/kw_b2"
            style="?android:attr/progressBarStyleHorizontal"
            android:layout_width="match_parent"
            android:layout_height="6dp"
            android:layout_marginTop="4dp"
            android:max="100"
            android:progress="0"
            android:progressDrawable="@drawable/kar_widget_progress" />
    </LinearLayout>

    <LinearLayout
        android:id="@+id/kw_r3"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="8dp"
        android:orientation="vertical">

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="horizontal">

            <TextView
                android:id="@+id/kw_n3"
                android:layout_width="0dp"
                android:layout_height="wrap_content"
                android:layout_weight="1"
                android:ellipsize="end"
                android:maxLines="1"
                android:textColor="@color/kw_text"
                android:textDirection="rtl"
                android:textSize="12sp" />

            <TextView
                android:id="@+id/kw_p3"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_marginStart="8dp"
                android:textColor="@color/kw_fill"
                android:textSize="12sp"
                android:textStyle="bold" />
        </LinearLayout>

        <ProgressBar
            android:id="@+id/kw_b3"
            style="?android:attr/progressBarStyleHorizontal"
            android:layout_width="match_parent"
            android:layout_height="6dp"
            android:layout_marginTop="4dp"
            android:max="100"
            android:progress="0"
            android:progressDrawable="@drawable/kar_widget_progress" />
    </LinearLayout>

</LinearLayout>
''',
    'res/values-night/kar_widget_colors.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="kw_bg">#1E293B</color>
    <color name="kw_stroke">#334155</color>
    <color name="kw_text">#F1F5F9</color>
    <color name="kw_text_sub">#94A3B8</color>
    <color name="kw_track">#334155</color>
    <color name="kw_fill">#10B981</color>
</resources>
''',
    'res/values/kar_widget_colors.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="kw_bg">#FFFFFF</color>
    <color name="kw_stroke">#E2E8F0</color>
    <color name="kw_text">#0F172A</color>
    <color name="kw_text_sub">#64748B</color>
    <color name="kw_track">#E2E8F0</color>
    <color name="kw_fill">#10B981</color>
</resources>
''',
    'res/xml/kar_widget_info.xml': r'''<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:minWidth="250dp"
    android:minHeight="110dp"
    android:targetCellWidth="4"
    android:targetCellHeight="2"
    android:updatePeriodMillis="1800000"
    android:initialLayout="@layout/kar_widget"
    android:previewLayout="@layout/kar_widget"
    android:resizeMode="horizontal|vertical"
    android:widgetCategory="home_screen" />
''',
}

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
