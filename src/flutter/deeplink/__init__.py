import os
import re

def inject_flutter_deeplink_handler(main_dart_path):
    """Inject the Smartech deeplink handler code into main.dart (Dart-side)."""
    handler_code = '''Smartech().onHandleDeeplink((String? smtDeeplinkSource, String? smtDeeplink, Map<dynamic, dynamic>? smtPayload, Map<dynamic, dynamic>? smtCustomPayload) async {\n  // Perform action on click of Notification\n});\n'''
    with open(main_dart_path, 'r') as f:
        main_dart_content = f.read()
    if 'Smartech().onHandleDeeplink' in main_dart_content:
        print("   ⚠️ Smartech deeplink handler already present in main.dart")
        return
    main_func_match = re.search(r'void\s+main\s*\([^)]*\)\s*{', main_dart_content)
    if main_func_match:
        insert_pos = main_func_match.end()
        new_content = main_dart_content[:insert_pos] + '\n  ' + handler_code + main_dart_content[insert_pos:]
    else:
        new_content = main_dart_content + '\n' + handler_code
    with open(main_dart_path, 'w') as f:
        f.write(new_content)
    print("   ✅ Smartech deeplink handler injected in main.dart")

def add_flutter_scheme_intent_filter_to_manifest(manifest_path, scheme):
    """Add scheme-based intent filter to the manifest for the launcher activity (Flutter). Returns the android:name of the activity."""
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
            # Add the intent filter for the scheme
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
    """Inject deep link handling code in the MainActivity class (Flutter)."""
    with open(activity_path, 'r') as f:
        content = f.read()
    # Check if deep link handling code already exists
    if 'isDeepLinkFromSmartech' in content:
        return  # Code already exists
    # Java code template
    java_code = """
        boolean isSmartechHandledDeeplink = Smartech.getInstance(new WeakReference<>(this)).isDeepLinkFromSmartech(getIntent());
        if (!isSmartechHandledDeeplink) {
        //Handle deeplink on app side
        }"""
    # Kotlin code template
    kotlin_code = """
        val isSmartechHandledDeeplink = Smartech.getInstance(WeakReference(this)).isDeepLinkFromSmartech(intent)
        if (!isSmartechHandledDeeplink) {
        //Handle deeplink on app side
        }"""
    code_to_inject = kotlin_code if language == 'kotlin' else java_code
    # For onCreate method in Java
    java_pattern = r'((?:public|protected)\s+void\s+onCreate\s*\(\s*(?:Bundle|android\.os\.Bundle)\s+\w+\s*\)\s*\{[^}]*super\.onCreate\s*\([^)]*\);)'
    # For onCreate method in Kotlin
    kotlin_pattern = r'(override\s+fun\s+onCreate\s*\([^)]*\)\s*\{[^}]*super\.onCreate\s*\([^)]*\))'
    pattern = kotlin_pattern if language == 'kotlin' else java_pattern
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, r'\1' + code_to_inject, content, flags=re.DOTALL)
        # Ensure required imports are added
        required_imports = []
        if 'import java.lang.ref.WeakReference;' not in content and language == 'java':
            required_imports.append('import java.lang.ref.WeakReference;')
        if 'import com.netcore.android.Smartech;' not in content and language == 'java':
            required_imports.append('import com.netcore.android.Smartech;')
        if 'import java.lang.ref.WeakReference' not in content and language == 'kotlin':
            required_imports.append('import java.lang.ref.WeakReference')
        if 'import com.netcore.android.Smartech' not in content and language == 'kotlin':
            required_imports.append('import com.netcore.android.Smartech')
        if required_imports:
            import_block = '\n'.join(required_imports)
            if 'package ' in content:
                content = re.sub(r'(package\s+[^;]*;)', r'\1\n\n' + import_block, content)
            else:
                content = import_block + '\n\n' + content
    with open(activity_path, 'w') as f:
        f.write(content) 