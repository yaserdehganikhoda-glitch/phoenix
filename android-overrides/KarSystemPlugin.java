package ir.sewingstats.app;

import android.app.AlarmManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Build;
import android.os.PowerManager;
import android.provider.Settings;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/**
 * پلاگین کوچک سیستمی: معافیت از بهینه‌سازی باتری، آلارم دقیق و باز کردن تنظیمات برنامه.
 * در جاوااسکریپت با نام KarSystem صدا زده می‌شود.
 */
@CapacitorPlugin(name = "KarSystem")
public class KarSystemPlugin extends Plugin {

    private void launch(Intent i) {
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        getContext().startActivity(i);
    }

    private Uri pkgUri() {
        return Uri.parse("package:" + getContext().getPackageName());
    }

    @PluginMethod
    public void batteryStatus(PluginCall call) {
        JSObject r = new JSObject();
        boolean ignoring = true;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            PowerManager pm = (PowerManager) getContext().getSystemService(Context.POWER_SERVICE);
            ignoring = pm != null && pm.isIgnoringBatteryOptimizations(getContext().getPackageName());
        }
        r.put("ignoring", ignoring);
        call.resolve(r);
    }

    @PluginMethod
    public void requestIgnoreBattery(PluginCall call) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                try {
                    launch(new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, pkgUri()));
                } catch (Exception e) {
                    launch(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS));
                }
            }
            call.resolve(new JSObject().put("opened", true));
        } catch (Exception e) {
            call.reject("battery settings unavailable");
        }
    }

    @PluginMethod
    public void exactAlarmStatus(PluginCall call) {
        boolean allowed = true;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            AlarmManager am = (AlarmManager) getContext().getSystemService(Context.ALARM_SERVICE);
            allowed = am != null && am.canScheduleExactAlarms();
        }
        call.resolve(new JSObject().put("allowed", allowed));
    }

    @PluginMethod
    public void requestExactAlarm(PluginCall call) {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                launch(new Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM, pkgUri()));
            }
            call.resolve(new JSObject().put("opened", true));
        } catch (Exception e) {
            call.reject("exact alarm settings unavailable");
        }
    }

    @PluginMethod
    public void openAppSettings(PluginCall call) {
        try {
            launch(new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, pkgUri()));
            call.resolve(new JSObject().put("opened", true));
        } catch (Exception e) {
            call.reject("app settings unavailable");
        }
    }

    /** دوره‌ی آزمایشی ۳۰ روزه از زمان نصب (با پاک‌کردن داده‌ی برنامه ریست نمی‌شود)؛ ساعت به عقب برنمی‌گردد. */
    @PluginMethod
    public void trialStatus(PluginCall call) {
        try {
            Context c = getContext();
            final long DAY = 86400000L;
            long first = c.getPackageManager().getPackageInfo(c.getPackageName(), 0).firstInstallTime;
            SharedPreferences sp = c.getSharedPreferences("kar_s", Context.MODE_PRIVATE);
            long wall = System.currentTimeMillis();
            long el = android.os.SystemClock.elapsedRealtime();
            long tw = sp.getLong("tw", 0L), te = sp.getLong("te", 0L);
            long now;
            if (tw > 0 && el >= te) now = tw + (el - te);   // زمان واقعی سپری‌شده، مستقل از ساعت گوشی
            else now = Math.max(tw, wall);                   // اولین اجرا یا بعد از ریبوت
            if (wall > now) now = wall;                      // جلو بردن ساعت فقط به ضرر کاربر است
            sp.edit().putLong("tw", now).putLong("te", el).apply();
            long left = (long) Math.ceil((first + 30 * DAY - now) / (double) DAY);
            if (left > 30) left = 30;
            JSObject r = new JSObject();
            r.put("daysLeft", (int) Math.max(left, 0));
            r.put("expired", left <= 0);
            call.resolve(r);
        } catch (Exception e) {
            call.reject("trial unavailable");
        }
    }
}
