import os
import re

def create_deeplink_receiver(src_dir, language, application_id):
    """Create a deep link receiver class if it doesn't exist."""
    path = os.path.join(src_dir, "DeeplinkReceiver.kt" if language == 'kotlin' else "DeeplinkReceiver.java")
    if os.path.exists(path):
        return
        
    if language == 'kotlin':
        content = f"""
package {application_id}

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.netcore.android.*

class DeeplinkReceiver : BroadcastReceiver() {{
    override fun onReceive(context: Context?, intent: Intent?) {{
        try {{
            val bundleExtra = intent?.extras
            bundleExtra?.let {{
                val deepLinkSource = it.getString(SMTBundleKeys.SMT_KEY_DEEPLINK_SOURCE)
                val deepLink = it.getString(SMTBundleKeys.SMT_KEY_DEEPLINK)
                val customPayload = it.getString(SMTBundleKeys.SMT_KEY_CUSTOM_PAYLOAD)
                if (deepLink != null && deepLink.isNotEmpty()) {{
                    // handle deepLink
                }}
                if (customPayload != null && customPayload.isNotEmpty()) {{
                    // handle custom payload
                }}
            }}
        }} catch (t: Throwable) {{
            Log.e("DeeplinkReceiver", "Error occurred in deeplink:${{t.localizedMessage}}")
        }}
    }}
}}
"""
    else:
        content = f"""
package {application_id};

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import com.netcore.android.*;

public class DeeplinkReceiver extends BroadcastReceiver {{
    @Override
    public void onReceive(Context context, Intent intent) {{
        try {{
            Bundle bundleExtra = intent.getExtras();
            if (bundleExtra != null) {{
                String deepLinkSource = bundleExtra.getString(SMTBundleKeys.SMT_KEY_DEEPLINK_SOURCE);
                String deepLink = bundleExtra.getString(SMTBundleKeys.SMT_KEY_DEEPLINK);
                String customPayload = bundleExtra.getString(SMTBundleKeys.SMT_KEY_CUSTOM_PAYLOAD);
                if (deepLink != null && !deepLink.isEmpty()) {{
                    // handle deepLink
                }}
                if (customPayload != null && !customPayload.isEmpty()) {{
                    // handle custom payload
                }}
            }}
        }} catch (Throwable t) {{
            Log.e("DeeplinkReceiver", "Error occurred in deeplink:" + t.getLocalizedMessage());
        }}
    }}
}}
"""
    with open(path, 'w') as f:
        f.write(content) 

def add_scheme_intent_filter_to_manifest(manifest_path, scheme):
    """Add scheme-based intent filter to the manifest for the launcher activity."""
    with open(manifest_path, 'r') as f:
        content = f.read()
    
    # Look for the launcher activity
    launcher_activity_pattern = r'(<activity\s+[^>]*android:name="[^"]*"[^>]*>(?:.*?)<intent-filter>(?:.*?)<action\s+android:name="android.intent.action.MAIN"(?:.*?)<category\s+android:name="android.intent.category.LAUNCHER"(?:.*?)</intent-filter>)'
    
    # Check if an intent filter with smartech_sdk_td host already exists
    smartech_host_pattern = r'<data[^>]*android:host="smartech_sdk_td"[^>]*>'
    smartech_host_match = re.search(smartech_host_pattern, content)
    
    if smartech_host_match:
        # Update the existing intent filter's scheme attribute
        existing_filter = smartech_host_match.group(0)
        if f'android:scheme="{scheme}"' in existing_filter:
            # Scheme is already correct, nothing to do
            print(f"   ℹ️ Intent filter for smartech_sdk_td with scheme '{scheme}' already exists")
            return
        
        # Update the scheme value
        if 'android:scheme="' in existing_filter:
            # Replace existing scheme value
            updated_filter = re.sub(r'android:scheme="[^"]*"', f'android:scheme="{scheme}"', existing_filter)
        else:
            # Add scheme attribute if missing
            updated_filter = existing_filter.replace('android:host="smartech_sdk_td"', 
                                                   f'android:scheme="{scheme}" android:host="smartech_sdk_td"')
        
        # Replace the old filter with the updated one
        content = content.replace(existing_filter, updated_filter)
        print(f"   ✅ Updated existing smartech_sdk_td intent filter with scheme '{scheme}'")
    else:
        # Create the new intent filter
        scheme_intent_filter = f"""
        <intent-filter>
            <action android:name="android.intent.action.VIEW" />
            <category android:name="android.intent.category.DEFAULT" />
            <category android:name="android.intent.category.BROWSABLE" />
            <data android:scheme="{scheme}"
                  android:host="smartech_sdk_td" />
        </intent-filter>"""
        
        # Add the intent filter after the launcher intent filter
        match = re.search(launcher_activity_pattern, content, re.DOTALL)
        if match:
            content = re.sub(launcher_activity_pattern, r'\1' + scheme_intent_filter, content, flags=re.DOTALL)
            print(f"   ✅ Added new smartech_sdk_td intent filter with scheme '{scheme}'")
        else:
            print("   ⚠️ Could not find launcher activity to add intent filter")
    
    with open(manifest_path, 'w') as f:
        f.write(content)

def inject_deeplink_handling_code(activity_path, language):
    """Inject deep link handling code in the activity class."""
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
    
    # The code to inject
    code_to_inject = kotlin_code if language == 'kotlin' else java_code
    
    # For onCreate method in Java
    java_pattern = r'((?:public|protected)\s+void\s+onCreate\s*\(\s*(?:Bundle|android\.os\.Bundle)\s+\w+\s*\)\s*\{[^}]*super\.onCreate\s*\([^)]*\);)'
    
    # For onCreate method in Kotlin
    kotlin_pattern = r'(override\s+fun\s+onCreate\s*\([^)]*\)\s*\{[^}]*super\.onCreate\s*\([^)]*\))'
    
    pattern = kotlin_pattern if language == 'kotlin' else java_pattern
    
    # Inject the code after super.onCreate()
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
            # Add imports after package line or at the beginning
            if 'package ' in content:
                content = re.sub(r'(package\s+[^;]*;)', r'\1\n\n' + import_block, content)
            else:
                content = import_block + '\n\n' + content
    
    with open(activity_path, 'w') as f:
        f.write(content)         