import re

def modify_manifest(manifest_path, app_id, app_class_relative, target_sdk):
    """Modify the Android manifest file with necessary Smartech configurations."""
    with open(manifest_path, 'r') as f:
        content = f.read()

    # Add SMT_APP_ID if missing
    if 'SMT_APP_ID' not in content:
        content = re.sub(r'(<application\b[^>]*>)',
                         r'\1\n        <meta-data android:name="SMT_APP_ID" android:value="{}" />'.format(app_id),
                         content)

    # Always set android:name to the application class path
    if re.search(r'<application[^>]*android:name=', content):
        # Replace existing android:name
     # Only update android:name inside the <application> tag
        content = re.sub(
        r'(<application[^>]*?)android:name="[^"]*"([^>]*>)',
        rf'\1android:name="{app_class_relative}"\2',
        content
        )

    else:
        # Add android:name if not present
        content = re.sub(r'<application\b',
                         f'<application android:name="{app_class_relative}"',
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

def inject_push_meta_tag(manifest_path, ask_permission):
    """Inject push notification meta tag into the manifest."""
    with open(manifest_path, 'r') as f:
        content = f.read()

    if 'SMT_IS_AUTO_ASK_NOTIFICATION_PERMISSION' not in content:
        content = re.sub(r'(<application\b[^>]*>)',
                         r'\1\n        <meta-data android:name="SMT_IS_AUTO_ASK_NOTIFICATION_PERMISSION" android:value="{}" />'.format(
                             '1' if ask_permission else '0'),
                         content)
    else:
        content = re.sub(r'<meta-data android:name="SMT_IS_AUTO_ASK_NOTIFICATION_PERMISSION" android:value="[^"]*" ?/>',
                         r'<meta-data android:name="SMT_IS_AUTO_ASK_NOTIFICATION_PERMISSION" android:value="{}" />'.format(
                             '1' if ask_permission else '0'),
                         content)

    with open(manifest_path, 'w') as f:
        f.write(content)

def register_firebase_service(manifest_path, service_name):
    """Register Firebase Messaging Service in the AndroidManifest.xml."""
    with open(manifest_path, 'r') as f:
        content = f.read()

    # Check if the service is already registered
    if f'android:name=".{service_name}"' in content:
        return

    service_registration = f"""
        <service 
            android:name=".{service_name}">
            <intent-filter>
                <action android:name="com.google.firebase.MESSAGING_EVENT"/>
            </intent-filter>
        </service>"""

    # Case 1: <application> and </application> present
    if '</application>' in content:
        content = re.sub(r'(</application>)', service_registration + r'\n\1', content)
    
    # Case 2: <application> present but </application> missing
    elif '<application' in content:
        content += '\n' + service_registration + '\n</application>'

    # Case 3: No <application> tag at all — raise error or create it (optional)
    else:
        raise ValueError("No <application> tag found in AndroidManifest.xml.")

    with open(manifest_path, 'w') as f:
        f.write(content)

def inject_location_tracking_meta_tag(manifest_path, enable_location):
    """Inject location tracking meta tag into the manifest."""
    with open(manifest_path, 'r') as f:
        content = f.read()

    if 'SMT_IS_AUTO_FETCHED_LOCATION' not in content:
        content = re.sub(r'(<application\b[^>]*>)',
                         r'\1\n        <meta-data android:name="SMT_IS_AUTO_FETCHED_LOCATION" android:value="{}" />'.format(
                             '1' if enable_location else '0'),
                         content)
    else:
        content = re.sub(r'<meta-data android:name="SMT_IS_AUTO_FETCHED_LOCATION" android:value="[^"]*" ?/>',
                         r'<meta-data android:name="SMT_IS_AUTO_FETCHED_LOCATION" android:value="{}" />'.format(
                             '1' if enable_location else '0'),
                         content)

def integrate_product_experience_manifest(manifest_path, hansel_app_id, hansel_app_key):
    """Inject Hansel App ID and App Key as meta-data in the manifest under <application>."""
    with open(manifest_path, 'r') as f:
        content = f.read()
    # Only add if not already present
    if 'HANSEL_APP_ID' not in content:
        content = re.sub(r'(<application\b[^>]*>)',
            r'\1\n        <meta-data android:name="HANSEL_APP_ID" android:value="%s" />' % hansel_app_id,
            content)
    else:
        content = re.sub(r'<meta-data android:name="HANSEL_APP_ID" android:value="[^"]*" ?/>',
            r'<meta-data android:name="HANSEL_APP_ID" android:value="%s" />' % hansel_app_id,
            content)
    if 'HANSEL_APP_KEY' not in content:
        content = re.sub(r'(<application\b[^>]*>)',
            r'\1\n        <meta-data android:name="HANSEL_APP_KEY" android:value="%s" />' % hansel_app_key,
            content)
    else:
        content = re.sub(r'<meta-data android:name="HANSEL_APP_KEY" android:value="[^"]*" ?/>',
            r'<meta-data android:name="HANSEL_APP_KEY" android:value="%s" />' % hansel_app_key,
            content)
    with open(manifest_path, 'w') as f:
        f.write(content)