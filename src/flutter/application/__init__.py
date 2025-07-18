import os
import re

def setup_flutter_application_class(src_dir, application_id):
    """Find or create the Application class that extends FlutterApplication."""
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".java") or file.endswith(".kt"):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read()
                    if re.search(r'class\s+\w+\s*:\s*FlutterApplication|extends\s+FlutterApplication', content):
                        language = 'kotlin' if file.endswith('.kt') else 'java'
                        return path, language
    # If not found, create new
    path = os.path.join(src_dir, "MyApplication.kt")
    content = f"""
package {application_id}

import io.flutter.app.FlutterApplication
import com.netcore.android.Smartech
import java.lang.ref.WeakReference

class MyApplication : FlutterApplication() {{
    override fun onCreate() {{
        super.onCreate()
        Smartech.getInstance(WeakReference(applicationContext)).initializeSdk(this)
        Smartech.getInstance(WeakReference(applicationContext)).trackAppInstallUpdateBySmartech()
        SmartechBasePlugin.initializePlugin(this)
    }}
}}
"""
    with open(path, "w") as f:
        f.write(content)
    print(f"   ✅ Created new Application class at {path}")
    return path, 'kotlin'

def inject_flutter_debug_level(app_class_path, language, enable_debug):
    """Inject debug log level code into the Application class."""
    with open(app_class_path, 'r') as f:
        content = f.read()
    debug_level = 9 if enable_debug else 1
    debug_code = f'Smartech.getInstance(WeakReference(applicationContext)).setDebugLevel({debug_level})' if language == 'kotlin' else f'Smartech.getInstance(new WeakReference<>(this)).setDebugLevel({debug_level});'
    # Check if setDebugLevel is already present
    if 'setDebugLevel' in content:
        # Update existing debug level
        if language == 'kotlin':
            content = re.sub(r'Smartech\.getInstance\(WeakReference\(applicationContext\)\)\.setDebugLevel\(\d+\)',
                            debug_code,
                            content)
        else:
            content = re.sub(r'Smartech\.getInstance\(new\s+WeakReference<\>\(this\)\)\.setDebugLevel\(\d+\);',
                            debug_code,
                            content)
    else:
        # Add debug level setting after SDK initialization
        if language == 'kotlin':
            content = re.sub(r'(Smartech\.getInstance\(WeakReference\(applicationContext\)\)\.initializeSdk\(this\))',
                            r'\1\n        ' + debug_code,
                            content)
        else:
            content = re.sub(r'(Smartech\.getInstance\(new\s+WeakReference<\>\(this\)\)\.initializeSdk\(this\);)',
                            r'\1\n        ' + debug_code,
                            content)
    # Inject SmartechBasePlugin.initializePlugin(this) if not present
    if 'SmartechBasePlugin.initializePlugin(this)' not in content:
        if language == 'kotlin':
            # Add after SDK initialization
            content = re.sub(r'(Smartech\.getInstance\(WeakReference\(applicationContext\)\)\.initializeSdk\(this\))',
                            r'\1\n        SmartechBasePlugin.initializePlugin(this)',
                            content)
        else:
            content = re.sub(r'(Smartech\.getInstance\(new\s+WeakReference<\>\(this\)\)\.initializeSdk\(this\);)',
                            r'\1\n        SmartechBasePlugin.initializePlugin(this);',
                            content)
    with open(app_class_path, 'w') as f:
        f.write(content)
    print(f"   ✅ Debug log level set to {debug_level} in Application class and SmartechBasePlugin.initializePlugin(this) injected if needed") 