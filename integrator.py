# Smartech SDK integrator for Android Native (Java/Kotlin)
# Modular, scalable integration framework to support multiple platforms

import os
import re

def find_application_class(src_dir):
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".java") or file.endswith(".kt"):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read()
                    if re.search(r'class\s+\w+\s*:\s*Application|extends\s+Application', content):
                        return path, 'kotlin' if file.endswith('.kt') else 'java'
    return None, None

def create_application_class(src_dir, language):
    path = os.path.join(src_dir, "MyApplication.kt" if language == 'kotlin' else "MyApplication.java")
    if language == 'kotlin':
        content = """

import android.app.Application
import android.content.IntentFilter
import com.netcore.android.Smartech
import java.lang.ref.WeakReference

class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        Smartech.getInstance(WeakReference(applicationContext)).initializeSdk(this)
        Smartech.getInstance(WeakReference(applicationContext)).trackAppInstallUpdateBySmartech()
    }
}
"""
    else:
        content = """

import android.app.Application;
import android.content.IntentFilter;
import com.netcore.android.Smartech;
import java.lang.ref.WeakReference;

public class MyApplication extends Application {
    @Override
    public void onCreate() {
        super.onCreate();
        Smartech.getInstance(new WeakReference<>(getApplicationContext())).initializeSdk(this);
        Smartech.getInstance(new WeakReference<>(getApplicationContext())).trackAppInstallUpdateBySmartech();
    }
}
"""
    with open(path, "w") as f:
        f.write(content)
    return path

def create_deeplink_receiver(src_dir, language):
    path = os.path.join(src_dir, "DeeplinkReceiver.kt" if language == 'kotlin' else "DeeplinkReceiver.java")
    if os.path.exists(path):
        return
    if language == 'kotlin':
        content = """package com.example

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class DeeplinkReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context?, intent: Intent?) {
        try {
            val bundleExtra = intent?.extras
            bundleExtra?.let {
                val deepLinkSource = it.getString(SMTBundleKeys.SMT_KEY_DEEPLINK_SOURCE)
                val deepLink = it.getString(SMTBundleKeys.SMT_KEY_DEEPLINK)
                val customPayload = it.getString(SMTBundleKeys.SMT_KEY_CUSTOM_PAYLOAD)
                if (deepLink != null && deepLink.isNotEmpty()) {
                    // handle deepLink
                }
                if (customPayload != null && customPayload.isNotEmpty()) {
                    // handle custom payload
                }
            }
        } catch (t: Throwable) {
            Log.e("DeeplinkReceiver", "Error occurred in deeplink:${t.localizedMessage}")
        }
    }
}
"""
    else:
        content = """package com.example;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;

public class DeeplinkReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        try {
            Bundle bundleExtra = intent.getExtras();
            if (bundleExtra != null) {
                String deepLinkSource = bundleExtra.getString(SMTBundleKeys.SMT_KEY_DEEPLINK_SOURCE);
                String deepLink = bundleExtra.getString(SMTBundleKeys.SMT_KEY_DEEPLINK);
                String customPayload = bundleExtra.getString(SMTBundleKeys.SMT_KEY_CUSTOM_PAYLOAD);
                if (deepLink != null && !deepLink.isEmpty()) {
                    // handle deepLink
                }
                if (customPayload != null && !customPayload.isEmpty()) {
                    // handle custom payload
                }
            }
        } catch (Throwable t) {
            Log.e("DeeplinkReceiver", "Error occurred in deeplink:" + t.getLocalizedMessage());
        }
    }
}
"""
    with open(path, 'w') as f:
        f.write(content)


def modify_manifest(manifest_path, app_id, app_class_relative, target_sdk):
    with open(manifest_path, 'r') as f:
        content = f.read()

    # Add SMT_APP_ID if missing
    if 'SMT_APP_ID' not in content:
        content = re.sub(r'(<application\b[^>]*>)',
                         r'\1\n        <meta-data android:name="SMT_APP_ID" android:value="{}" />'.format(app_id),
                         content)

    # Add android:name if not present in application tag
    if not re.search(r'<application[^>]*android:name=', content):
        content = re.sub(r'<application\b',
                         r'<application android:name="{}"'.format(app_class_relative),
                         content)

    # Ensure allowBackup is true
    def ensure_or_replace_attr(tag, attr, value):
        if attr in tag:
            tag = re.sub(r'{}="[^"]*"'.format(attr), '{}="{}"'.format(attr, value), tag)
        else:
            tag = tag.rstrip('>') + f' {attr}="{value}">'
        return tag

    # Find the application tag
    match = re.search(r'<application\b[^>]*>', content)
    if match:
        app_tag = match.group(0)

        # Enforce allowBackup = true
        app_tag = ensure_or_replace_attr(app_tag, 'android:allowBackup', 'true')

        # Handle fullBackupContent (only if targetSdk < 31)
        if target_sdk < 31:
            app_tag = ensure_or_replace_attr(app_tag, 'android:fullBackupContent', '@xml/my_backup_file')

        # Handle dataExtractionRules (only if targetSdk >= 31)
        if target_sdk >= 31:
            app_tag = ensure_or_replace_attr(app_tag, 'android:dataExtractionRules', '@xml/my_backup_file_31')

        # Replace the old <application ...> tag with the modified one
        content = content.replace(match.group(0), app_tag)

    # Write back to file
    with open(manifest_path, "w") as f:
        f.write(content)

def inject_sdk_initialization(app_class_path, language, target_sdk):
    with open(app_class_path, 'r') as f:
        content = f.read()

    # Determine if SDK code and DeeplinkReceiver code are already present
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
            # Insert after super.onCreate() in onCreate() method
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


    

# def inject_sdk_initialization(app_class_path, language, target_sdk):
#     with open(app_class_path, 'r') as f:
#         content = f.read()

#     # Kotlin branch
#     if language == 'kotlin':
#         if 'Smartech.getInstance' not in content:
#             sdk_init = """
#         Smartech.getInstance(WeakReference(applicationContext)).initializeSdk(this)
#         Smartech.getInstance(WeakReference(applicationContext)).trackAppInstallUpdateBySmartech()
# """
#         else:
#             sdk_init = ""

#         if 'DeeplinkReceiver' not in content:
#             deeplink_code = """
#         val deeplinkReceiver = DeeplinkReceiver()
#         val filter = IntentFilter("com.smartech.EVENT_PN_INBOX_CLICK")
#         if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
#             registerReceiver(deeplinkReceiver, filter, RECEIVER_EXPORTED)
#         } else {
#             registerReceiver(deeplinkReceiver, filter)
#         }
# """ if target_sdk >= 34 else """
#         val deeplinkReceiver = DeeplinkReceiver()
#         val filter = IntentFilter("com.smartech.EVENT_PN_INBOX_CLICK")
#         registerReceiver(deeplinkReceiver, filter)
# """
#         else:
#             deeplink_code = ""

#         insertion_code = f"""
#         {sdk_init}{deeplink_code}
# """
#         content = re.sub(r'override fun onCreate\(\) \{',
#                          r'override fun onCreate() {\n' + insertion_code.strip(),
#                          content)

#     # Java branch
#     else:
#         if 'Smartech.getInstance' not in content:
#             sdk_init = """
#         Smartech.getInstance(new WeakReference<>(getApplicationContext())).initializeSdk(this);
#         Smartech.getInstance(new WeakReference<>(getApplicationContext())).trackAppInstallUpdateBySmartech();
# """
#         else:
#             sdk_init = ""

#         if 'DeeplinkReceiver' not in content:
#             deeplink_code = """
#         DeeplinkReceiver deeplinkReceiver = new DeeplinkReceiver();
#         IntentFilter filter = new IntentFilter("com.smartech.EVENT_PN_INBOX_CLICK");
#         if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
#             registerReceiver(deeplinkReceiver, filter, Context.RECEIVER_EXPORTED);
#         } else {
#             registerReceiver(deeplinkReceiver, filter);
#         }
# """ if target_sdk >= 34 else """
#         DeeplinkReceiver deeplinkReceiver = new DeeplinkReceiver();
#         IntentFilter filter = new IntentFilter("com.smartech.EVENT_PN_INBOX_CLICK");
#         registerReceiver(deeplinkReceiver, filter);
# """
#         else:
#             deeplink_code = ""

#         insertion_code = f"""
#         {sdk_init}{deeplink_code}
# """
#         content = re.sub(r'public void onCreate\(\) \{',
#                          r'public void onCreate() {\n' + insertion_code.strip(),
#                          content)

#     with open(app_class_path, 'w') as f:
#         f.write(content)


def extract_target_sdk(gradle_path):
    with open(gradle_path, 'r') as f:
        content = f.read()
    match = re.search(r'targetSdk\s*[=:]\s*(\d+)', content)
    print("the target sdk version is"+str(match))
    return int(match.group(1)) if match else 0

def create_backup_xml_files(project_dir,target_sdk,manifest_path):
    xml_dir = os.path.join(project_dir, "app", "src", "main", "res", "xml")
    os.makedirs(xml_dir, exist_ok=True)
    with open(manifest_path, 'r') as g:
        content = g.read()


    if(target_sdk<31):
        with open(os.path.join(xml_dir, "my_backup_file.xml"), "w") as f:
            f.write("""<?xml version=\"1.0\" encoding=\"utf-8\"?>
            <full-backup-content>
            <include domain=\"sharedpref\" path=\"smt_guid_preferences.xml\"/>
            <include domain=\"sharedpref\" path=\"smt_preferences_guid.xml\"/>
            </full-backup-content>""")

    else:
        with open(os.path.join(xml_dir, "my_backup_file_31.xml"), "w") as f:
            f.write("""<?xml version=\"1.0\" encoding=\"utf-8\"?>
     <data-extraction-rules>
        <cloud-backup disableIfNoEncryptionCapabilities=\"false\">
             <include domain=\"sharedpref\" path=\"smt_guid_preferences.xml\" />
             <include domain=\"sharedpref\" path=\"smt_preferences_guid.xml\" />
        </cloud-backup>
    </data-extraction-rules>""")


def modify_gradle(gradle_path):
    with open(gradle_path, "r") as f:
        content = f.read()

    if "smartech-sdk" not in content:
        content = re.sub(r'dependencies\s*{',
                         r'dependencies {\n    implementation \"com.netcore.android:smartech-sdk:3.6.2\"',
                         content)

    with open(gradle_path, "w") as f:
        f.write(content)

def find_push_service_class(src_dir):
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
    with open(push_class_path, 'r') as f:
        content = f.read()

    if language == 'kotlin':
        if 'setDevicePushToken' not in content:
            content = re.sub(r'override fun onNewToken\(token: String\) {',
                             r'''override fun onNewToken(token: String) {

        SmartPush.getInstance(WeakReference(this)).setDevicePushToken(token)''',
                             content)
        if 'handleRemotePushNotification' not in content:
            content = re.sub(r'override fun onMessageReceived\(message: RemoteMessage\) {',
                             r'''override fun onMessageReceived(message: RemoteMessage) {
        
        if (remoteMessage.data.containsKey("smtSrc")) {
            SmartPush.getInstance(WeakReference(applicationContext)).handleRemotePushNotification(remoteMessage)
        }''',
                             content)
    else:
        if 'setDevicePushToken' not in content:
            content = re.sub(r'public void onNewToken\(String token\) {',
                             r'''public void onNewToken(String token) {
        # super.onNewToken(token);
        SmartPush.getInstance(new WeakReference<Context>(this)).setDevicePushToken(token);''',
                             content)
        if 'handleRemotePushNotification' not in content:
            content = re.sub(r'public void onMessageReceived\(RemoteMessage remoteMessage\) {',
                             r'''public void onMessageReceived(RemoteMessage remoteMessage) {
        # super.onMessageReceived(remoteMessage);
        if (remoteMessage.getData().containsKey("smtSrc")) {
            SmartPush.getInstance(new WeakReference<Context>(getApplicationContext())).handleRemotePushNotification(remoteMessage);
        }''',
                             content)

    with open(push_class_path, 'w') as f:
        f.write(content)


def create_push_service_class(src_dir, language):
    path = os.path.join(src_dir, "MyFirebaseMessagingService.kt" if language == 'kotlin' else "MyFirebaseMessagingService.java")
    if os.path.exists(path):
        return
    if language == 'kotlin':
        content = """package com.example

import android.content.Context
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.netcore.android.SmartPush
import java.lang.ref.WeakReference

class MyFirebaseMessagingService : FirebaseMessagingService() {
    override fun onNewToken(token: String) {
        super.onNewToken(token)
        SmartPush.getInstance(WeakReference(this)).setDevicePushToken(token)
    }

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        super.onMessageReceived(remoteMessage)
        if (remoteMessage.data.containsKey("smtSrc")) {
            SmartPush.getInstance(WeakReference(applicationContext)).handleRemotePushNotification(remoteMessage)
        }
    }
}
"""
    else:
        content = """package com.example;

import android.content.Context;
import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;
import com.netcore.android.SmartPush;
import java.lang.ref.WeakReference;

public class MyFirebaseMessagingService extends FirebaseMessagingService {
    @Override
    public void onNewToken(String token) {
        super.onNewToken(token);
        SmartPush.getInstance(new WeakReference<Context>(this)).setDevicePushToken(token);
    }

    @Override
    public void onMessageReceived(RemoteMessage remoteMessage) {
        super.onMessageReceived(remoteMessage);
        if (remoteMessage.getData().containsKey("smtSrc")) {
            SmartPush.getInstance(new WeakReference<Context>(getApplicationContext())).handleRemotePushNotification(remoteMessage);
        }
    }
}
"""
    with open(path, 'w') as f:
        f.write(content)


def inject_push_meta_tag(manifest_path, ask_permission):
    with open(manifest_path, 'r') as f:
        content = f.read()

    tag = '<meta-data android:name="SMT_IS_AUTO_ASK_NOTIFICATION_PERMISSION" android:value="{}" />'.format("0" if ask_permission else "1")
    if 'SMT_IS_AUTO_ASK_NOTIFICATION_PERMISSION' not in content:
        content = re.sub(r'(<application\b[^>]*>)', r'\1\n        {}'.format(tag), content)

    with open(manifest_path, 'w') as f:
        f.write(content)


def inject_push_dependency(gradle_path):
    with open(gradle_path, 'r') as f:
        content = f.read()

    if "smartech-push" not in content:
        content = re.sub(r'dependencies\s*{',
                         r'dependencies {\n    implementation "com.netcore.android:smartech-push:3.5.4"',
                         content)

    with open(gradle_path, "w") as f:
        f.write(content)


def main():
    print("🔧 Smartech SDK Integration for Android Native")
    framework = input("Enter framework (android, flutter, react-native): ").strip().lower()
    if framework != "android":
        print("❌ Only Android Native is supported right now.")
        return

    project_dir = input("📁 Enter path to your Android project root: ").strip()
    app_id = input("🔑 Enter your Smartech App ID: ").strip()

    # gradle_path = os.path.join(project_dir, "app", "build.gradle")

    gradle_path_groovy = os.path.join(project_dir, "app", "build.gradle")
    gradle_path_kts = os.path.join(project_dir, "app", "build.gradle.kts")

    if os.path.exists(gradle_path_groovy):
         gradle_path = gradle_path_groovy
    if os.path.exists(gradle_path_kts):
        gradle_path = gradle_path_kts
    manifest_path = os.path.join(project_dir, "app", "src", "main", "AndroidManifest.xml")
    java_src_path = os.path.join(project_dir, "app", "src", "main", "java")

    if not os.path.isfile(gradle_path) or not os.path.isfile(manifest_path):
        print("❌ Could not locate Gradle or Manifest file.")
        return

    app_class_path, language = find_application_class(java_src_path)

    if not app_class_path:
        print("🔍 No Application class found. Creating a new one.")
        language = "java"  # or detect Kotlin project here
        app_class_path = create_application_class(java_src_path, language)

    create_deeplink_receiver(os.path.dirname(app_class_path), language)
    target_sdk = extract_target_sdk(gradle_path)

    inject_sdk_initialization(app_class_path, language, target_sdk)
    modify_gradle(gradle_path)
    modify_manifest(manifest_path, app_id, ".MyApplication" if "MyApplication" in app_class_path else os.path.splitext(os.path.basename(app_class_path))[0],target_sdk)
    create_backup_xml_files(project_dir,target_sdk,manifest_path)

    print("✅ SDK integration complete.")


    integrate_push = input("🔔 Do you want to integrate push notifications? (yes/no): ").strip().lower()
    if integrate_push == "yes":
        ask_permission = input("🔐 Are you already handling notification permissions? (yes/no): ").strip().lower()
        inject_push_dependency(gradle_path)
        inject_push_meta_tag(manifest_path, ask_permission == "yes")

        push_class_path, push_lang = find_push_service_class(java_src_path)
        if push_class_path:
            print(f"🔍 Found existing push service: {os.path.basename(push_class_path)}")
            inject_push_logic(push_class_path, push_lang)
        else:
            print("📄 No push service found. Creating new one.")
            create_push_service_class(os.path.dirname(app_class_path), language)

        print("✅ Push notification integration complete.")
    else:
        print("🚫 Skipped push notification integration.")




if __name__ == "__main__":
    main()
