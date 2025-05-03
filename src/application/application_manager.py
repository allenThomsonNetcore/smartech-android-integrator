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