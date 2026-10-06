#!/usr/bin/env python3
"""افزودن پلاگین بومی KarBilling (Poolakey / کافه بازار) به پروژه‌ی android که `npx cap add android` ساخته.
اجرا از ریشه‌ی مخزن، بعد از cap add و بعد از مرحله‌ی ویجت:  python3 bazaar/apply_bazaar.py
متغیرهای محیطی: BAZAAR_SKU (شناسه‌ی اشتراک در پنل بازار)، BAZAAR_RSA_KEY (کلید RSA برنامه)،
POOLAKEY_VERSION، KOTLIN_VERSION. چند بار اجرا شود مشکلی ندارد."""
import os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
SKU = os.environ.get('BAZAAR_SKU', 'kar_premium').strip()
RSA = os.environ.get('BAZAAR_RSA_KEY', '').strip()
POOL = os.environ.get('POOLAKEY_VERSION', '2.2.0').strip()
KOTLIN = os.environ.get('KOTLIN_VERSION', '1.9.22').strip()
MARK = 'kar-bazaar'

def rd(p): return open(p, encoding='utf-8').read()
def wr(p, s): open(p, 'w', encoding='utf-8').write(s)
def die(m): print('ERROR:', m); sys.exit(1)

main = glob.glob('android/app/src/main/java/**/MainActivity.java', recursive=True)
if not main: die('MainActivity.java پیدا نشد؛ آیا cap add android اجرا شده؟')
main = main[0]; src = rd(main)
pkg = re.search(r'^\s*package\s+([\w.]+)\s*;', src, re.M).group(1)

# 1) فایل پلاگین
kt = rd(os.path.join(HERE, 'KarBillingPlugin.kt.tmpl')).replace('__PKG__', pkg).replace('__SKU__', SKU).replace('__RSA__', RSA)
wr(os.path.join(os.path.dirname(main), 'KarBillingPlugin.kt'), kt)
print('plugin written, package', pkg, '| sku', SKU, '| rsa key', 'SET' if RSA else 'EMPTY (local security check OFF!)')

# 2) ثبت پلاگین در MainActivity
if 'KarBillingPlugin.class' not in src:
    reg = '        registerPlugin(KarBillingPlugin.class); // ' + MARK + '\n'
    if re.search(r'super\.onCreate\(', src):
        src = re.sub(r'([ \t]*)super\.onCreate\(', lambda m: reg + m.group(0), src, count=1)
    else:
        src = re.sub(r'(public class MainActivity[^{]*\{)',
            lambda m: m.group(1) + '\n    @Override\n    public void onCreate(android.os.Bundle savedInstanceState) {\n' + reg +
                      '        super.onCreate(savedInstanceState);\n    }\n', src, count=1)
    wr(main, src); print('MainActivity patched')

# 3) gradle ریشه: jitpack و پلاگین kotlin
rg = 'android/build.gradle'; g = rd(rg)
if MARK not in g:
    g = re.sub(r"(classpath\s+['\"]com\.android\.tools\.build:gradle:[^'\"]+['\"])",
               lambda m: m.group(1) + "\n        classpath 'org.jetbrains.kotlin:kotlin-gradle-plugin:%s' // %s" % (KOTLIN, MARK), g, count=1)
    if 'jitpack.io' not in g:
        g = re.sub(r'(allprojects\s*\{\s*repositories\s*\{)', lambda m: m.group(1) + "\n        maven { url 'https://jitpack.io' } // " + MARK, g, count=1)
    wr(rg, g); print('root build.gradle patched')

# 4) gradle برنامه: kotlin و وابستگی Poolakey
ag = 'android/app/build.gradle'; a = rd(ag)
if MARK not in a:
    a = re.sub(r"(apply plugin:\s*['\"]com\.android\.application['\"])", lambda m: m.group(1) + "\napply plugin: 'kotlin-android' // " + MARK, a, count=1)
    a = re.sub(r'(\nandroid\s*\{)', lambda m: m.group(1) + "\n    kotlinOptions { jvmTarget = '17' } // " + MARK, a, count=1)
    a = re.sub(r'(\ndependencies\s*\{)', lambda m: m.group(1) + '\n    implementation "com.github.cafebazaar.Poolakey:poolakey:%s" // %s' % (POOL, MARK), a, count=1)
    wr(ag, a); print('app build.gradle patched')

# 5) مجوز و queries در manifest
mf = 'android/app/src/main/AndroidManifest.xml'; m = rd(mf)
if 'PAY_THROUGH_BAZAAR' not in m:
    add = ('    <uses-permission android:name="com.farsitel.bazaar.permission.PAY_THROUGH_BAZAAR" />\n'
           '    <queries><package android:name="com.farsitel.bazaar" /></queries>\n')
    m = re.sub(r'(\s*<application)', lambda x: '\n' + add + x.group(1).lstrip('\n'), m, count=1)
    wr(mf, m); print('manifest patched')
print('DONE')
