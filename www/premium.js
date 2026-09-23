/*
 * ماژول «نسخه ویژه» — اتصال به سرویس پرداخت درون‌برنامه‌ای کافه بازار (Poolakey)
 * این فایل فقط داخل اپ اندرویدی (ساخته‌شده با Capacitor) فعال می‌شود؛
 * وقتی سایت در مرورگر معمولی/PWA باز شود، بی‌صدا غیرفعال می‌ماند و به بقیه برنامه آسیبی نمی‌زند.
 *
 * قبل از استفاده:
 *  ۱) در پنل کافه بازار، برای اپ یک محصول درون‌برنامه‌ای با شناسه PRODUCT_ID تعریف کن.
 *  ۲) کلید عمومی RSA اپ رو از پنل کافه بازار (بخش پرداخت درون‌برنامه‌ای) کپی کن و جای RSA_PUBLIC_KEY بذار.
 */
(function () {
    const PRODUCT_ID = 'premium_unlock';
    const RSA_PUBLIC_KEY = 'RSA_PUBLIC_KEY_FROM_BAZAAR_PANEL'; // TODO: از پنل کافه بازار جایگزین شود
    const STORAGE_KEY = 'sewing_premium_v1';

    function isNative() {
        return !!(window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform());
    }

    function setUnlocked(value) {
        try { localStorage.setItem(STORAGE_KEY, value ? 'true' : 'false'); } catch (e) { /* بی‌اهمیت */ }
    }

    function isUnlocked() {
        try { return localStorage.getItem(STORAGE_KEY) === 'true'; } catch (e) { return false; }
    }

    async function connect() {
        if (!isNative()) return false;
        try {
            const { Poolakey } = await import('capacitor-poolakey');
            window.__poolakey = Poolakey;
            await Poolakey.connectPayment(RSA_PUBLIC_KEY);
            return true;
        } catch (e) {
            console.warn('اتصال به Poolakey ناموفق بود:', e);
            return false;
        }
    }

    // بررسی خریدهای قبلی (مثلاً بعد از نصب مجدد اپ) و همگام‌سازی وضعیت قفل
    async function restore() {
        if (!(await connect())) return isUnlocked();
        try {
            const res = await window.__poolakey.getPurchasedProducts();
            const owned = !!(res && res.list && res.list.some(p => p.productId === PRODUCT_ID));
            setUnlocked(owned);
            return owned;
        } catch (e) {
            console.warn('خواندن خریدهای قبلی ناموفق بود:', e);
            return isUnlocked();
        }
    }

    // شروع فرآیند خرید نسخه ویژه
    async function purchase() {
        if (!isNative()) {
            alert('خرید نسخه ویژه فقط در نسخه اندرویدی (کافه بازار) امکان‌پذیر است.');
            return false;
        }
        if (!(await connect())) {
            alert('اتصال به کافه بازار برقرار نشد. لطفاً از نصب‌بودن اپ بازار روی گوشی مطمئن شوید.');
            return false;
        }
        try {
            await window.__poolakey.purchaseProduct(PRODUCT_ID);
            setUnlocked(true);
            return true;
        } catch (e) {
            console.warn('خرید ناموفق یا لغو شد:', e);
            return false;
        }
    }

    window.SewingPremium = { isUnlocked, purchase, restore };

    // در باز شدن اپ (فقط نسخه نیتیو)، وضعیت خرید قبلی را همگام می‌کند
    // (این کار async است و ممکن است بعد از رندر اولیه صفحه تمام شود، پس UI تنظیمات را هم دوباره به‌روزرسانی می‌کنیم)
    if (isNative()) {
        restore().then(() => {
            if (typeof window.updatePremiumStatusUI === 'function') window.updatePremiumStatusUI();
        });
    }
})();
