import os
import re

def inject_flutter_deeplink_handler(main_dart_path):
    """Inject the Smartech deeplink handler code inside main() in main.dart (Dart-side)."""
    handler_code = '''Smartech().onHandleDeeplink((String? smtDeeplinkSource, String? smtDeeplink, Map<dynamic, dynamic>? smtPayload, Map<dynamic, dynamic>? smtCustomPayload) async {\n  // Perform action on click of Notification\n});\n'''
    with open(main_dart_path, 'r') as f:
        main_dart_content = f.read()
    if 'Smartech().onHandleDeeplink' in main_dart_content:
        print("   ⚠️ Smartech deeplink handler already present in main.dart")
        return
    # Robustly match main() with any modifiers (async, etc.)
    main_func_match = re.search(r'(void\s+main\s*\([^)]*\)\s*(async\s*)?\{)', main_dart_content)
    if main_func_match:
        insert_pos = main_func_match.end()
        new_content = main_dart_content[:insert_pos] + '\n  ' + handler_code + main_dart_content[insert_pos:]
    else:
        new_content = main_dart_content + '\n' + handler_code
    with open(main_dart_path, 'w') as f:
        f.write(new_content)
    print("   ✅ Smartech deeplink handler injected inside main() in main.dart")

def add_flutter_scheme_intent_filter_to_manifest(manifest_path, scheme):
    """Add or update scheme-based intent filter for smartech_sdk_td in the launcher activity. Returns the android:name of the activity."""
    with open(manifest_path, 'r') as f:
        content = f.read()
    # Find all <activity ...>...</activity> blocks
    activity_blocks = re.findall(r'(<activity[\s\S]*?</activity>)', content, re.DOTALL)
    for block in activity_blocks:
        # Check for MAIN action and LAUNCHER category
        if ('android.intent.action.MAIN' in block and 'android.intent.category.LAUNCHER' in block):
            # Extract android:name
            name_match = re.search(r'android:name="([^"]+)"', block)
            activity_name = name_match.group(1) if name_match else None
            # Check if an intent filter with smartech_sdk_td host already exists
            smartech_host_pattern = r'(<intent-filter>[\s\S]*?<data[^>]*android:host="smartech_sdk_td"[^>]*/>[\s\S]*?</intent-filter>)'
            host_match = re.search(smartech_host_pattern, block)
            if host_match:
                # Update the scheme in the existing filter
                intent_filter = host_match.group(1)
                # Replace or add android:scheme
                if 'android:scheme=' in intent_filter:
                    updated_filter = re.sub(r'android:scheme="[^"]*"', f'android:scheme="{scheme}"', intent_filter)
                else:
                    updated_filter = intent_filter.replace('android:host="smartech_sdk_td"', f'android:scheme="{scheme}" android:host="smartech_sdk_td"')
                new_block = block.replace(intent_filter, updated_filter)
                content = content.replace(block, new_block)
                with open(manifest_path, 'w') as f:
                    f.write(content)
                print(f"   ✅ Updated smartech_sdk_td intent filter with scheme '{scheme}' in launcher activity: {activity_name}")
                return activity_name
            # Otherwise, add a new intent filter
            scheme_intent_filter = f"""
        <intent-filter>
            <action android:name=\"android.intent.action.VIEW\" />
            <category android:name=\"android.intent.category.DEFAULT\" />
            <category android:name=\"android.intent.category.BROWSABLE\" />
            <data android:scheme=\"{scheme}\" android:host=\"smartech_sdk_td\" />
        </intent-filter>"""
            # Insert after the last </intent-filter> in the block
            new_block = re.sub(r'(</intent-filter>)', r'\1' + scheme_intent_filter, block, count=1)
            content = content.replace(block, new_block)
            with open(manifest_path, 'w') as f:
                f.write(content)
            print(f"   ✅ Added new smartech_sdk_td intent filter with scheme '{scheme}' to launcher activity: {activity_name}")
            return activity_name
    print("   ⚠️ Could not find launcher activity to add intent filter")
    return None

def inject_flutter_deeplink_handling_code(activity_path, language):
    """Inject deep link handling code at the start of onCreate() in any class extending FlutterActivity. Add onCreate if missing. Support both Kotlin and Java."""
    with open(activity_path, 'r') as f:
        content = f.read()
    # Java and Kotlin code templates
    java_handler = '''boolean isSmartechHandledDeeplink = Smartech.getInstance(new WeakReference<>(this)).isDeepLinkFromSmartech(getIntent());
        if (!isSmartechHandledDeeplink) {
            //Handle deeplink on app side
        }'''
    kotlin_handler = '''val isSmartechHandledDeeplink = Smartech.getInstance(WeakReference(this)).isDeepLinkFromSmartech(intent)
        if (!isSmartechHandledDeeplink) {
            //Handle deeplink on app side
        }'''
    # Patterns for onCreate
    java_pattern = r'((?:public|protected)\s+void\s+onCreate\s*\(\s*(?:Bundle|android\.os\.Bundle)\s+\w+\s*\)\s*\{[^}]*super\.onCreate\s*\([^)]*\);)'
    kotlin_pattern = r'(override\s+fun\s+onCreate\s*\([^)]*\)\s*\{[^}]*super\.onCreate\s*\([^)]*\))'
    pattern = kotlin_pattern if language == 'kotlin' else java_pattern
    handler_code = kotlin_handler if language == 'kotlin' else java_handler
    # If onCreate exists
    if re.search(pattern, content, re.DOTALL):
        # Inject handler code after super.onCreate() if not present
        if 'isDeepLinkFromSmartech' not in content:
            content = re.sub(pattern, r'\1\n        ' + handler_code, content, flags=re.DOTALL)
            print("   ✅ Injected deep link handler at start of onCreate() in Activity class")
    else:
        # Add onCreate method to the class that extends FlutterActivity
        if language == 'kotlin':
            class_match = re.search(r'(class\s+\w+\s*:\s*FlutterActivity\s*\([^{]*\){)', content)
            if not class_match:
                class_match = re.search(r'(class\s+\w+\s*:\s*FlutterActivity\s*\{)', content)
            if class_match:
                insert_pos = class_match.end()
                oncreate_code = f"""
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        {handler_code}
    }}
"""
                new_content = content[:insert_pos] + '\n' + oncreate_code + content[insert_pos:]
                content = new_content
                print("   ✅ Added onCreate with deep link handler to FlutterActivity class (Kotlin)")
        else:
            class_match = re.search(r'(public\s+class\s+\w+\s+extends\s+FlutterActivity[^{]*\{)', content)
            if class_match:
                insert_pos = class_match.end()
                oncreate_code = f"""
    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        {handler_code}
    }}
"""
                new_content = content[:insert_pos] + '\n' + oncreate_code + content[insert_pos:]
                content = new_content
                print("   ✅ Added onCreate with deep link handler to FlutterActivity class (Java)")
    # Ensure required imports are added
    required_imports = []
    if language == 'java':
        if 'import java.lang.ref.WeakReference;' not in content:
            required_imports.append('import java.lang.ref.WeakReference;')
        if 'import com.netcore.android.Smartech;' not in content:
            required_imports.append('import com.netcore.android.Smartech;')
        if 'import android.os.Bundle;' not in content:
            required_imports.append('import android.os.Bundle;')
    else:
        if 'import java.lang.ref.WeakReference' not in content:
            required_imports.append('import java.lang.ref.WeakReference')
        if 'import com.netcore.android.Smartech' not in content:
            required_imports.append('import com.netcore.android.Smartech')
        if 'import android.os.Bundle' not in content:
            required_imports.append('import android.os.Bundle')
    if required_imports:
        import_block = '\n'.join(required_imports)
        if 'package ' in content:
            content = re.sub(r'(package\s+[^;]*;)', r'\1\n\n' + import_block, content)
        else:
            content = import_block + '\n\n' + content
    with open(activity_path, 'w') as f:
        f.write(content) 