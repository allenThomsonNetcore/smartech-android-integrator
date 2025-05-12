import os
import re

def find_application_class(src_dir):
    """Find the application class in the source directory."""
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".java") or file.endswith(".kt"):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read()
                    if re.search(r'class\s+\w+\s*:\s*Application|extends\s+Application', content):
                        return path, 'kotlin' if file.endswith('.kt') else 'java'
    return None, None

def create_application_class(src_dir, language, application_id):
    """Create a new application class if one doesn't exist."""
    path = os.path.join(src_dir, "MyApplication.kt" if language == 'kotlin' else "MyApplication.java")
    if language == 'kotlin':
        content = f"""
package {application_id}

import android.app.Application
import android.content.IntentFilter
import com.netcore.android.Smartech
import java.lang.ref.WeakReference

class MyApplication : Application() {{
    override fun onCreate() {{
        super.onCreate()
        Smartech.getInstance(WeakReference(applicationContext)).initializeSdk(this)
        Smartech.getInstance(WeakReference(applicationContext)).trackAppInstallUpdateBySmartech()
    }}
}}
"""
    else:
        content = f"""
package {application_id};

import android.app.Application;
import android.content.IntentFilter;
import com.netcore.android.Smartech;
import java.lang.ref.WeakReference;

public class MyApplication extends Application {{
    @Override
    public void onCreate() {{
        super.onCreate();
        Smartech.getInstance(new WeakReference<>(getApplicationContext())).initializeSdk(this);
        Smartech.getInstance(new WeakReference<>(getApplicationContext())).trackAppInstallUpdateBySmartech();
    }}
}}
"""
    with open(path, "w") as f:
        f.write(content)
    return path

def inject_sdk_initialization(app_class_path, language, target_sdk):
    """Inject SDK initialization code into the application class."""
    with open(app_class_path, 'r') as f:
        content = f.read()

    has_smartech_init = 'initializeSdk' in content
    has_deeplink = 'DeeplinkReceiver' in content or 'EVENT_PN_INBOX_CLICK' in content

    if language == 'kotlin':
        insertion = ""

        if not has_smartech_init:
            insertion += """
        Smartech.getInstance(WeakReference(applicationContext)).initializeSdk(this)
        Smartech.getInstance(WeakReference(applicationContext)).trackAppInstallUpdateBySmartech()
"""

        if not has_deeplink:
            if target_sdk >= 34:
                insertion += """
        val deeplinkReceiver = DeeplinkReceiver()
        val filter = IntentFilter("com.smartech.EVENT_PN_INBOX_CLICK")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            registerReceiver(deeplinkReceiver, filter, RECEIVER_EXPORTED)
        } else {
            registerReceiver(deeplinkReceiver, filter)
        }
"""
            else:
                insertion += """
        val deeplinkReceiver = DeeplinkReceiver()
        val filter = IntentFilter("com.smartech.EVENT_PN_INBOX_CLICK")
        registerReceiver(deeplinkReceiver, filter)
"""

        if insertion.strip():
            content = re.sub(r'(override fun onCreate\(\) \s*{[^}]*super\.onCreate\(\);?)',
                             lambda m: m.group(0) + insertion,
                             content)

    else:  # Java
        insertion = ""

        if not has_smartech_init:
            insertion += """
        Smartech.getInstance(new WeakReference<>(getApplicationContext())).initializeSdk(this);
        Smartech.getInstance(new WeakReference<>(getApplicationContext())).trackAppInstallUpdateBySmartech();
"""

        if not has_deeplink:
            if target_sdk >= 34:
                insertion += """
        DeeplinkReceiver deeplinkReceiver = new DeeplinkReceiver();
        IntentFilter filter = new IntentFilter("com.smartech.EVENT_PN_INBOX_CLICK");
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            registerReceiver(deeplinkReceiver, filter, Context.RECEIVER_EXPORTED);
        } else {
            registerReceiver(deeplinkReceiver, filter);
        }
"""
            else:
                insertion += """
        DeeplinkReceiver deeplinkReceiver = new DeeplinkReceiver();
        IntentFilter filter = new IntentFilter("com.smartech.EVENT_PN_INBOX_CLICK");
        registerReceiver(deeplinkReceiver, filter);
"""

        if insertion.strip():
            content = re.sub(r'(public void onCreate\(\) \s*{[^}]*super\.onCreate\(\);?)',
                             lambda m: m.group(0) + insertion,
                             content)

    with open(app_class_path, 'w') as f:
        f.write(content)

def inject_debug_level(app_class_path, language, enable_debug):
    """Inject debug level setting into the application class."""
    with open(app_class_path, 'r') as f:
        content = f.read()

    debug_level = 9 if enable_debug else 0
    debug_code = f'Smartech.getInstance(WeakReference(applicationContext)).setDebugLevel({debug_level})' if language == 'kotlin' else f'Smartech.getInstance(new WeakReference<>(this)).setDebugLevel({debug_level});'

    # Check if setDebugLevel is already present
    if 'setDebugLevel' in content:
        # Update existing debug level
        if language == 'kotlin':
            content = re.sub(r'Smartech\.getInstance\(WeakReference\(applicationContext\)\)\.setDebugLevel\(\d+\)',
                            debug_code,
                            content)
        else:
            content = re.sub(r'Smartech\.getInstance\(new\s+WeakReference<>\(this\)\)\.setDebugLevel\(\d+\);',
                            debug_code,
                            content)
    else:
        # Add debug level setting after SDK initialization
        if language == 'kotlin':
            content = re.sub(r'(Smartech\.getInstance\(WeakReference\(applicationContext\)\)\.initializeSdk\(this\))',
                            r'\1\n        ' + debug_code,
                            content)
        else:
            content = re.sub(r'(Smartech\.getInstance\(new\s+WeakReference<>\(this\)\)\.initializeSdk\(this\);)',
                            r'\1\n        ' + debug_code,
                            content)

    with open(app_class_path, 'w') as f:
        f.write(content)

def inject_notification_appearance(app_class_path, language, notification_options):
    """Inject notification appearance settings into the application class."""
    with open(app_class_path, 'r') as f:
        content = f.read()

    # Build the options code based on user input
    if language == 'kotlin':
        options_code = "val options = SMTNotificationOptions(context)\n"
        if notification_options.get('brand_logo'):
            options_code += f'options.brandLogo = "{notification_options["brand_logo"]}"\n'
        if notification_options.get('large_icon'):
            options_code += f'options.largeIcon = "{notification_options["large_icon"]}"\n'
        if notification_options.get('small_icon'):
            options_code += f'options.smallIcon = "{notification_options["small_icon"]}"\n'
        if notification_options.get('small_icon_transparent'):
            options_code += f'options.smallIconTransparent = "{notification_options["small_icon_transparent"]}"\n'
        if notification_options.get('transparent_bg_color'):
            options_code += f'options.transparentIconBgColor = "{notification_options["transparent_bg_color"]}"\n'
        if notification_options.get('placeholder_icon'):
            options_code += f'options.placeHolderIcon = "{notification_options["placeholder_icon"]}"\n'
        options_code += 'SmartPush.getInstance(WeakReference(context)).setNotificationOptions(options)'
    else:
        options_code = "SMTNotificationOptions options = new SMTNotificationOptions(this);\n"
        if notification_options.get('brand_logo'):
            options_code += f'options.setBrandLogo("{notification_options["brand_logo"]}");\n'
        if notification_options.get('large_icon'):
            options_code += f'options.setLargeIcon("{notification_options["large_icon"]}");\n'
        if notification_options.get('small_icon'):
            options_code += f'options.setSmallIcon("{notification_options["small_icon"]}");\n'
        if notification_options.get('small_icon_transparent'):
            options_code += f'options.setSmallIconTransparent("{notification_options["small_icon_transparent"]}");\n'
        if notification_options.get('transparent_bg_color'):
            options_code += f'options.setTransparentIconBgColor("{notification_options["transparent_bg_color"]}");\n'
        if notification_options.get('placeholder_icon'):
            options_code += f'options.setPlaceHolderIcon("{notification_options["placeholder_icon"]}");\n'
        options_code += 'SmartPush.getInstance(new WeakReference<>(this)).setNotificationOptions(options);'

    # Check if SMTNotificationOptions is already present
    if 'SMTNotificationOptions' in content:
        # Update existing notification options
        if language == 'kotlin':
            # Find the entire block from options creation to setNotificationOptions
            pattern = r'val\s+options\s*=\s*SMTNotificationOptions\([^)]*\)[^}]*SmartPush\.getInstance\([^)]*\)\.setNotificationOptions\(options\)'
            if re.search(pattern, content):
                content = re.sub(pattern, options_code, content)
        else:
            # Find the entire block from options creation to setNotificationOptions
            pattern = r'SMTNotificationOptions\s+options\s*=\s*new\s+SMTNotificationOptions\([^)]*\);[^;]*SmartPush\.getInstance\([^)]*\)\.setNotificationOptions\(options\);'
            if re.search(pattern, content):
                content = re.sub(pattern, options_code, content)
    else:
        # Add notification options after SDK initialization
        if language == 'kotlin':
            content = re.sub(r'(Smartech\.getInstance\(WeakReference\(applicationContext\)\)\.initializeSdk\(this\))',
                            r'\1\n        ' + options_code,
                            content)
        else:
            content = re.sub(r'(Smartech\.getInstance\(new\s+WeakReference<>\(this\)\)\.initializeSdk\(this\);)',
                            r'\1\n        ' + options_code,
                            content)

    with open(app_class_path, 'w') as f:
        f.write(content) 