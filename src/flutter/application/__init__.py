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
    """Inject Smartech SDK initialization, debug level, and plugin init into the Application class, even if onCreate exists with other code."""
    with open(app_class_path, 'r') as f:
        content = f.read()
    debug_level = 9 if enable_debug else 1
    debug_code = f'Smartech.getInstance(WeakReference(applicationContext)).setDebugLevel({debug_level})' if language == 'kotlin' else f'Smartech.getInstance(new WeakReference<>(this)).setDebugLevel({debug_level});'
    smartech_init_kotlin = '''Smartech.getInstance(WeakReference(applicationContext)).initializeSdk(this)
        Smartech.getInstance(WeakReference(applicationContext)).trackAppInstallUpdateBySmartech()
        SmartechBasePlugin.initializePlugin(this)
        '''
    smartech_init_java = '''Smartech.getInstance(new WeakReference<>(getApplicationContext())).initializeSdk(this);
        Smartech.getInstance(new WeakReference<>(getApplicationContext())).trackAppInstallUpdateBySmartech();
        SmartechBasePlugin.initializePlugin(this);
        '''
    # Patterns for onCreate
    java_pattern = r'((?:public|protected)\s+void\s+onCreate\s*\(\s*(?:Bundle|android\.os\.Bundle)\s+\w+\s*\)\s*\{[^}]*super\.onCreate\s*\([^)]*\);)'
    kotlin_pattern = r'(override\s+fun\s+onCreate\s*\([^)]*\)\s*\{[^}]*super\.onCreate\s*\([^)]*\))'
    pattern = kotlin_pattern if language == 'kotlin' else java_pattern
    smartech_init = smartech_init_kotlin if language == 'kotlin' else smartech_init_java
    # If onCreate exists
    if re.search(pattern, content, re.DOTALL):
        # Inject Smartech init block after super.onCreate() if not present
        if 'Smartech.getInstance' not in content:
            content = re.sub(pattern, r'\1\n        ' + smartech_init, content, flags=re.DOTALL)
        # Inject debug level after Smartech init
        if 'setDebugLevel' not in content:
            content = re.sub(r'(Smartech\.getInstance\([^)]+\)\.initializeSdk\(this\)[;]?)', r'\1\n        ' + debug_code, content)
        # Inject plugin init if not present
        if 'SmartechBasePlugin.initializePlugin(this)' not in content:
            content = re.sub(r'(Smartech\.getInstance\([^)]+\)\.trackAppInstallUpdateBySmartech\(\)[;]?)', r'\1\n        SmartechBasePlugin.initializePlugin(this)' + ('' if language == 'kotlin' else ';'), content)
    else:
        # Add onCreate method to the class
        if language == 'kotlin':
            class_match = re.search(r'(class\s+\w+\s*:\s*FlutterApplication\s*\([^{]*\){)', content)
            if not class_match:
                class_match = re.search(r'(class\s+\w+\s*:\s*FlutterApplication\s*\{)', content)
            if class_match:
                insert_pos = class_match.end()
                oncreate_code = f"""
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        {smartech_init}        {debug_code}
    }}
"""
                new_content = content[:insert_pos] + '\n' + oncreate_code + content[insert_pos:]
                content = new_content
                print("   ✅ Added onCreate with Smartech SDK initialization to Application class (Kotlin)")
        else:
            class_match = re.search(r'(public\s+class\s+\w+\s+extends\s+FlutterApplication[^{]*\{)', content)
            if class_match:
                insert_pos = class_match.end()
                oncreate_code = f"""
    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        {smartech_init}        {debug_code}
    }}
"""
                new_content = content[:insert_pos] + '\n' + oncreate_code + content[insert_pos:]
                content = new_content
                print("   ✅ Added onCreate with Smartech SDK initialization to Application class (Java)")
    with open(app_class_path, 'w') as f:
        f.write(content)
    print(f"   ✅ Smartech SDK initialization and debug log level set in Application class") 