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
            content = re.sub(r'(override fun onCreate\([^)]*\) \s*{[^}]*super\.onCreate\([^)]*\);?)',
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
            content = re.sub(r'((?:public|protected)\s+void\s+onCreate\s*\(\s*(?:Bundle|android\.os\.Bundle)\s+\w+\s*\)\s*\{[^}]*super\.onCreate\s*\([^)]*\);?)',
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

    # Check if setNotificationOptions exists
    if 'setNotificationOptions' in content:
        # Update existing options
        if language == 'kotlin':
            for key, value in notification_options.items():
                if key == 'brand_logo':
                    content = re.sub(r'options\.brandLogo\s*=\s*"[^"]*"', f'options.brandLogo = "{value}"', content)
                elif key == 'large_icon':
                    content = re.sub(r'options\.largeIcon\s*=\s*"[^"]*"', f'options.largeIcon = "{value}"', content)
                elif key == 'small_icon':
                    content = re.sub(r'options\.smallIcon\s*=\s*"[^"]*"', f'options.smallIcon = "{value}"', content)
                elif key == 'small_icon_transparent':
                    content = re.sub(r'options\.smallIconTransparent\s*=\s*"[^"]*"', f'options.smallIconTransparent = "{value}"', content)
                elif key == 'transparent_bg_color':
                    content = re.sub(r'options\.transparentIconBgColor\s*=\s*"[^"]*"', f'options.transparentIconBgColor = "{value}"', content)
                elif key == 'placeholder_icon':
                    content = re.sub(r'options\.placeHolderIcon\s*=\s*"[^"]*"', f'options.placeHolderIcon = "{value}"', content)
        else:
            for key, value in notification_options.items():
                if key == 'brand_logo':
                    content = re.sub(r'options\.setBrandLogo\("[^"]*"\)', f'options.setBrandLogo("{value}")', content)
                elif key == 'large_icon':
                    content = re.sub(r'options\.setLargeIcon\("[^"]*"\)', f'options.setLargeIcon("{value}")', content)
                elif key == 'small_icon':
                    content = re.sub(r'options\.setSmallIcon\("[^"]*"\)', f'options.setSmallIcon("{value}")', content)
                elif key == 'small_icon_transparent':
                    content = re.sub(r'options\.setSmallIconTransparent\("[^"]*"\)', f'options.setSmallIconTransparent("{value}")', content)
                elif key == 'transparent_bg_color':
                    content = re.sub(r'options\.setTransparentIconBgColor\("[^"]*"\)', f'options.setTransparentIconBgColor("{value}")', content)
                elif key == 'placeholder_icon':
                    content = re.sub(r'options\.setPlaceHolderIcon\("[^"]*"\)', f'options.setPlaceHolderIcon("{value}")', content)
    else:
        # Add new notification options
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

        # Add after SDK initialization
        if language == 'kotlin':
            content = re.sub(r'(Smartech\.getInstance\(WeakReference\(applicationContext\)\)\.initializeSdk\(this\))',
                            r'\1\n        ' + options_code,
                            content)
        else:
            content = re.sub(r'(Smartech\.getInstance\(new\s+WeakReference<>\(this\)\)\.initializeSdk\(this\);)',
                            r'\1\n        ' + options_code,
                            content)
            # Also try to add after trackAppInstallUpdateBySmartech if initialization pattern not found
            if 'setNotificationOptions' not in content:
                content = re.sub(r'(Smartech\.getInstance\(new\s+WeakReference<>\(this\)\)\.trackAppInstallUpdateBySmartech\(\);)',
                                r'\1\n        ' + options_code,
                                content)

    with open(app_class_path, 'w') as f:
        f.write(content)

def integrate_product_experience_listeners(src_dir, language,application_id):
    """Create or update HanselInternalEventsListener and HanselDeepLinkListener classes."""
    hansel_event_listener_path = os.path.join(src_dir, "HanselInternalEventsListenerImpl.kt" if language == 'kotlin' else "HanselInternalEventsListenerImpl.java")
    hansel_deeplink_listener_path = os.path.join(src_dir, "HanselDeepLinkListenerImpl.kt" if language == 'kotlin' else "HanselDeepLinkListenerImpl.java")

    # HanselInternalEventsListener
    if language == 'kotlin':
        event_listener_code = f'''
package {application_id}

import com.netcore.android.Smartech
import java.lang.ref.WeakReference

class HanselInternalEventsListenerImpl(val context: android.content.Context) : HanselInternalEventsListener {{
    override fun onEvent(eventName: String, dataFromHansel: HashMap<String, Any>) {{
        Smartech.getInstance(WeakReference(applicationContext)).trackEvent(eventName, dataFromHansel)
        // You can also call your Analytics platform trackEvent to pass the data
    }}
}}
'''
        deeplink_listener_code = f'''
package {application_id}


class HanselDeepLinkListenerImpl : HanselDeepLinkListener {{
    override fun onLaunchUrl(s: String) {{
        // implementation here
    }}
}}
'''
    else:
        event_listener_code = f'''
package {application_id}

import com.netcore.android.Smartech;
import java.lang.ref.WeakReference;
import java.util.HashMap;

public class HanselInternalEventsListenerImpl implements HanselInternalEventsListener {{
    private final android.content.Context context;
    public HanselInternalEventsListenerImpl(android.content.Context context) {{
        this.context = context;
    }}
    @Override
    public void onEvent(String eventName, HashMap dataFromHansel) {{
        Smartech.getInstance(new WeakReference<>(getApplicationContext())).trackEvent(eventName, dataFromHansel);
        // You can also call your Analytics platform trackEvent to pass the data
    }}
}}
'''
        deeplink_listener_code = f'''
package {application_id}


public class HanselDeepLinkListenerImpl implements HanselDeepLinkListener {{
    @Override
    public void onLaunchUrl(String s) {{
        // implementation here
    }}
}}
'''
    # Write or update event listener
    with open(hansel_event_listener_path, 'w') as f:
        f.write(event_listener_code)
    # Write or update deeplink listener
    with open(hansel_deeplink_listener_path, 'w') as f:
        f.write(deeplink_listener_code)

def register_product_experience_listeners(app_class_path, language):
    """Register Hansel listeners in the application class after SDK initialization."""
    with open(app_class_path, 'r') as f:
        content = f.read()
    if language == 'kotlin':
        # Import and registration code
        import_code = 'import io.hansel.ujmtracker.HanselTracker\nimport io.hansel.ujmtracker.Hansel\n'
        registration_code = '''
        val hanselInternalEventsListener = HanselInternalEventsListenerImpl(this)
        HanselTracker.registerListener(hanselInternalEventsListener)
        Hansel.registerHanselDeeplinkListener(HanselDeepLinkListenerImpl())
'''
        if 'HanselTracker.registerListener' not in content:
            content = re.sub(r'(Smartech\.getInstance\(WeakReference\(applicationContext\)\)\.initializeSdk\(this\))',
                            r'\1\n' + registration_code,
                            content)
        # if 'import io.hansel.ujmtracker.HanselTracker' not in content:
        #     content = import_code + content
    else:
        import_code = 'import io.hansel.ujmtracker.HanselTracker;\nimport io.hansel.ujmtracker.Hansel;\n'
        registration_code = '''
        HanselInternalEventsListenerImpl hanselInternalEventsListener = new HanselInternalEventsListenerImpl(this);
        HanselTracker.registerListener(hanselInternalEventsListener);
        Hansel.registerHanselDeeplinkListener(new HanselDeepLinkListenerImpl());
'''
        if 'HanselTracker.registerListener' not in content:
            content = re.sub(r'(Smartech\.getInstance\(new\s+WeakReference<>\(this\)\)\.initializeSdk\(this\);)',
                            r'\1\n' + registration_code,
                            content)
        # if 'import io.hansel.ujmtracker.HanselTracker;' not in content:
        #     content = import_code + content
    with open(app_class_path, 'w') as f:
        f.write(content) 