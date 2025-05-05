import os
import re

def find_push_service_class(src_dir):
    """Find the push notification service class in the source directory."""
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".java") or file.endswith(".kt"):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read()
                    if re.search(r'class\s+\w+\s*:\s*FirebaseMessagingService|extends\s+FirebaseMessagingService', content):
                        return path, 'kotlin' if file.endswith('.kt') else 'java'
    return None, None

def inject_push_logic(push_class_path, language):
    """Inject push notification handling logic into the service class."""
    with open(push_class_path, 'r') as f:
        content = f.read()

    if language == 'kotlin':
        # Check and add onNewToken if not present, or update if present but doesn't use Smartech
        if 'onNewToken' not in content:
            content = re.sub(r'(class\s+\w+\s*:\s*FirebaseMessagingService\s*{[^}]*)}',
                             lambda m: m.group(0) + """
    override fun onNewToken(token: String) {
        super.onNewToken(token)
        Smartech.getInstance(WeakReference(applicationContext)).setPushToken(token)
    }
}""",
                             content)
        elif 'onNewToken' in content and 'setPushToken' not in content:
            content = re.sub(r'(override\s+fun\s+onNewToken\s*\(\s*token\s*:\s*String\s*\)\s*{[^}]*})',
                             lambda m: m.group(0).replace('}', """
        Smartech.getInstance(WeakReference(applicationContext)).setPushToken(token)
    }"""),
                             content)

        # Check and add onMessageReceived if not present, or update if present but doesn't use Smartech
        if 'onMessageReceived' not in content:
            content = re.sub(r'(class\s+\w+\s*:\s*FirebaseMessagingService\s*{[^}]*)}',
                             lambda m: m.group(0) + """
    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        super.onMessageReceived(remoteMessage)
        if(remoteMessage.getData().containsKey("smtSrc")){
            Smartech.getInstance(WeakReference(applicationContext)).handlePushNotification(remoteMessage)
        }
    }
}""",
                             content)
        elif 'onMessageReceived' in content and 'handlePushNotification' not in content:
            content = re.sub(r'(override\s+fun\s+onMessageReceived\s*\(\s*remoteMessage\s*:\s*RemoteMessage\s*\)\s*{[^}]*super\.onMessageReceived\s*\(\s*remoteMessage\s*\)[^}]*})',
                             lambda m: m.group(0).replace('}', """
        if(remoteMessage.getData().containsKey("smtSrc")){
            Smartech.getInstance(WeakReference(applicationContext)).handlePushNotification(remoteMessage)
        }
    }"""),
                             content)
    else:  # Java
        # Check and add onNewToken if not present, or update if present but doesn't use Smartech
        if 'onNewToken' not in content:
            content = re.sub(r'(class\s+\w+\s*extends\s*FirebaseMessagingService\s*{[^}]*)}',
                             lambda m: m.group(0) + """
    @Override
    public void onNewToken(@NonNull String token) {
        super.onNewToken(token);
        Smartech.getInstance(new WeakReference<>(getApplicationContext())).setPushToken(token);
    }
}""",
                             content)
        elif 'onNewToken' in content and 'setPushToken' not in content:
            content = re.sub(r'(@Override\s+public\s+void\s+onNewToken\s*\(\s*@NonNull\s*String\s+token\s*\)\s*{[^}]*})',
                             lambda m: m.group(0).replace('}', """
        Smartech.getInstance(new WeakReference<>(getApplicationContext())).setPushToken(token);
    }"""),
                             content)

        # Check and add onMessageReceived if not present, or update if present but doesn't use Smartech
        if 'onMessageReceived' not in content:
            content = re.sub(r'(class\s+\w+\s*extends\s*FirebaseMessagingService\s*{[^}]*)}',
                             lambda m: m.group(0) + """
    @Override
    public void onMessageReceived(RemoteMessage remoteMessage) {
        super.onMessageReceived(remoteMessage);
        if(remoteMessage.getData().containsKey("smtSrc")){
            Smartech.getInstance(new WeakReference<>(getApplicationContext())).handlePushNotification(remoteMessage);
        }
    }
}""",
                             content)
        elif 'onMessageReceived' in content and 'handlePushNotification' not in content:
            content = re.sub(r'(@Override\s+public\s+void\s+onMessageReceived\s*\(\s*RemoteMessage\s+remoteMessage\s*\)\s*{[^}]*super\.onMessageReceived\s*\(\s*remoteMessage\s*\)[^}]*})',
                             lambda m: m.group(0).replace('}', """
        if(remoteMessage.getData().containsKey("smtSrc")){
            Smartech.getInstance(new WeakReference<>(getApplicationContext())).handlePushNotification(remoteMessage);
        }
    }"""),
                             content)

    with open(push_class_path, 'w') as f:
        f.write(content)

def create_push_service_class(src_dir, language, application_id):
    """Create a new push notification service class if one doesn't exist."""
    path = os.path.join(src_dir, "MyFirebaseMessagingService.kt" if language == 'kotlin' else "MyFirebaseMessagingService.java")
    if os.path.exists(path):
        return path

    if language == 'kotlin':
        content = f"""
package {application_id}

import android.content.Context
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.netcore.android.Smartech
import java.lang.ref.WeakReference

class MyFirebaseMessagingService : FirebaseMessagingService() {{
    override fun onMessageReceived(remoteMessage: RemoteMessage) {{
        super.onMessageReceived(remoteMessage)
        if(remoteMessage.getData().containsKey("smtSrc")){{
            Smartech.getInstance(WeakReference(applicationContext)).handlePushNotification(remoteMessage)
        }}
    }}

    override fun onNewToken(token: String) {{
        super.onNewToken(token)
        Smartech.getInstance(WeakReference(applicationContext)).setPushToken(token)
    }}
}}
"""
    else:
        content = f"""
package {application_id};

import android.content.Context;
import androidx.annotation.NonNull;
import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;
import com.netcore.android.Smartech;
import java.lang.ref.WeakReference;

public class MyFirebaseMessagingService extends FirebaseMessagingService {{
    @Override
    public void onMessageReceived(RemoteMessage remoteMessage) {{
        super.onMessageReceived(remoteMessage);
        if(remoteMessage.getData().containsKey("smtSrc")){{
            Smartech.getInstance(new WeakReference<>(getApplicationContext())).handlePushNotification(remoteMessage);
        }}
    }}

    @Override
    public void onNewToken(@NonNull String token) {{
        super.onNewToken(token);
        Smartech.getInstance(new WeakReference<>(getApplicationContext())).setPushToken(token);
    }}
}}
"""
    with open(path, 'w') as f:
        f.write(content)
    return path 