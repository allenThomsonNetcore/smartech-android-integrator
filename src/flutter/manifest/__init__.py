import re

def update_flutter_manifest(manifest_path, smartech_app_id, app_class_relative, target_sdk):
    """Add Smartech App ID, application class, and meta-data to AndroidManifest.xml (native logic, multiline safe)."""
    with open(manifest_path, 'r') as f:
        content = f.read()
    # Robust pattern for <application ...> tag (multiline safe)
    app_tag_pattern = r'(<application[\s\S]*?>)'
    # Add or update SMT_APP_ID meta-data
    if 'SMT_APP_ID' not in content:
        content = re.sub(app_tag_pattern,
                         r'\1\n        <meta-data android:name="SMT_APP_ID" android:value="{}" />'.format(smartech_app_id),
                         content, flags=re.DOTALL)
    else:
        content = re.sub(r'<meta-data android:name="SMT_APP_ID" android:value="[^"]*" ?/>',
                         r'<meta-data android:name="SMT_APP_ID" android:value="{}" />'.format(smartech_app_id),
                         content)
    # Always set android:name to the application class path
    if app_class_relative:
        if re.search(r'<application[^>]*android:name=', content, re.DOTALL):
            content = re.sub(
                r'(<application[^>]*?)android:name="[^"]*"([^>]*>)',
                rf'\1android:name="{app_class_relative}"\2',
                content,
                flags=re.DOTALL
            )
        else:
            content = re.sub(r'<application',
                             f'<application android:name="{app_class_relative}"',
                             content)
    # --- Backup file registration logic (native parity) ---
    def ensure_or_replace_attr(tag, attr, value):
        if attr in tag:
            tag = re.sub(r'{}="[^"]*"'.format(attr), '{}="{}"'.format(attr, value), tag)
        else:
            tag = tag.rstrip('>') + f' {attr}="{value}">'
        return tag
    match = re.search(app_tag_pattern, content, re.DOTALL)
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
    with open(manifest_path, "w") as f:
        f.write(content)
    print("   ✅ Manifest updated with Smartech App ID, application class, and backup registration")

def inject_flutter_location_tracking(manifest_path, enable_location):
    """Inject location tracking meta-data into the manifest (native logic, no permission, multiline safe)."""
    with open(manifest_path, 'r') as f:
        content = f.read()
    app_tag_pattern = r'(<application[\s\S]*?>)'
    if 'SMT_IS_AUTO_FETCHED_LOCATION' not in content:
        content = re.sub(app_tag_pattern,
                         r'\1\n        <meta-data android:name="SMT_IS_AUTO_FETCHED_LOCATION" android:value="{}" />'.format('1' if enable_location else '0'),
                         content, flags=re.DOTALL)
    else:
        content = re.sub(r'<meta-data android:name="SMT_IS_AUTO_FETCHED_LOCATION" android:value="[^"]*" ?/>',
                         r'<meta-data android:name="SMT_IS_AUTO_FETCHED_LOCATION" android:value="{}" />'.format('1' if enable_location else '0'),
                         content)
    with open(manifest_path, 'w') as f:
        f.write(content)
    print(f"   ✅ Location tracking meta-data set to {'1' if enable_location else '0'} in manifest (no permission added)") 