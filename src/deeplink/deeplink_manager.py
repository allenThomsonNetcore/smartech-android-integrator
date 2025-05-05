import os

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