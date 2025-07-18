import os
from src.flutter.pubspec import add_flutter_pubspec_dependency
from src.flutter.application import setup_flutter_application_class, inject_flutter_debug_level
from src.flutter.manifest import update_flutter_manifest, inject_flutter_location_tracking
from src.flutter.gradle import update_flutter_gradle, modify_flutter_settings_gradle
from src.flutter.deeplink import inject_flutter_deeplink_handler, add_flutter_scheme_intent_filter_to_manifest, inject_flutter_deeplink_handling_code
from src.flutter.backup import create_flutter_backup_xml_files

def get_flutter_paths(project_dir):
    """Return a dict of relevant paths (manifest, gradle, gradle.kts, properties, pubspec, etc.) and their existence."""
    android_dir = os.path.join(project_dir, "android")
    app_dir = os.path.join(android_dir, "app")
    paths = {
        'manifest': os.path.join(app_dir, "src", "main", "AndroidManifest.xml"),
        'gradle': os.path.join(app_dir, "build.gradle"),
        'gradle_kts': os.path.join(app_dir, "build.gradle.kts"),
        'properties': os.path.join(android_dir, "gradle.properties"),
        'pubspec': os.path.join(project_dir, "pubspec.yaml"),
        'src_dir': os.path.join(app_dir, "src", "main", "java"),
        'main_dart': os.path.join(project_dir, "lib", "main.dart"),
    }
    exists_flags = {k + '_exists': os.path.exists(v) for k, v in paths.items()}
    paths.update(exists_flags)
    return paths

def validate_flutter_project(project_dir):
    """Validate that the project directory contains the required Flutter project structure."""
    required_paths = [
        os.path.join(project_dir, "pubspec.yaml"),
        os.path.join(project_dir, "android"),
        os.path.join(project_dir, "lib"),
        os.path.join(project_dir, "android", "app", "src", "main", "AndroidManifest.xml")
    ]
    missing_paths = [path for path in required_paths if not os.path.exists(path)]
    if missing_paths:
        print("\nError: The specified directory is not a valid Flutter project.")
        print("Missing required files/directories:")
        for path in missing_paths:
            print(f"- {os.path.relpath(path, project_dir) if isinstance(path, str) else path}")
        print("\nPlease make sure you're pointing to the root directory of a Flutter project.")
        return False
    return True

def integrate_smartech_flutter():
    print("🛠  Smartech SDK Integration for Flutter")
    while True:
        project_dir = input("Enter the path to your Flutter project directory: ").strip()
        if not os.path.exists(project_dir):
            print("Error: The specified directory does not exist. Please try again.")
            continue
        if not validate_flutter_project(project_dir):
            continue
        break
    paths = get_flutter_paths(project_dir)
    print("\nStep 1: Adding/Updating pubspec.yaml dependency...")
    add_flutter_pubspec_dependency(paths['pubspec'])
    print("\nStep 2: Adding Smartech repository to settings.gradle(.kts)...")
    android_dir = os.path.join(project_dir, "android")
    settings_gradle = os.path.join(android_dir, "settings.gradle")
    settings_gradle_kts = os.path.join(android_dir, "settings.gradle.kts")
    if os.path.exists(settings_gradle_kts):
        modify_flutter_settings_gradle(settings_gradle_kts)
    elif os.path.exists(settings_gradle):
        modify_flutter_settings_gradle(settings_gradle)
    else:
        print("   ⚠️ No settings.gradle or settings.gradle.kts found. Skipping Smartech repository addition.")
    print("\nStep 3: Setting up Application class...")
    app_class_path, language = setup_flutter_application_class(paths['src_dir'], application_id=None)  # application_id will be extracted below
    print("\nStep 4: Updating gradle and gradle.properties...")
    gradle_path = paths['gradle_kts'] if paths['gradle_kts_exists'] else paths['gradle']
    update_flutter_gradle(gradle_path, paths['properties'])
    print("\nStep 5: Prompting for Smartech App ID...")
    smartech_app_id = input("Enter your Smartech App ID: ").strip()
    print("\nStep 6: Extracting applicationId and targetSdk from gradle...")
    import re
    application_id = None
    target_sdk = 33
    with open(gradle_path, 'r') as f:
        content = f.read()
        m = re.search(r'applicationId\s*(?:=|)\s*["\']([^"\']+)["\']', content)
        if m:
            application_id = m.group(1)
        m2 = re.search(r'targetSdk\s*(?:=|)\s*(\d+)', content)
        if m2:
            target_sdk = int(m2.group(1))
    if not application_id:
        application_id = input("Enter your Android applicationId (package name): ").strip()
    print("\nStep 7: Creating backup XML files...")
    create_flutter_backup_xml_files(project_dir, target_sdk)
    print("\nStep 8: Updating manifest with Smartech App ID, application class, and backup registration...")
    app_class_relative = os.path.relpath(app_class_path, paths['src_dir']).replace(os.sep, ".").replace(".java", "").replace(".kt", "")
    update_flutter_manifest(paths['manifest'], smartech_app_id, app_class_relative, target_sdk)
    print("\nStep 9: Injecting debug log level...")
    while True:
        enable_debug = input("\nDo you want to enable debug logs? (yes/no): ").strip().lower()
        if enable_debug in ['yes', 'no']:
            break
        print("Error: Please enter 'yes' or 'no'.")
    inject_flutter_debug_level(app_class_path, language, enable_debug == 'yes')
    print("\nStep 10: Injecting location tracking meta-data (no permission)...")
    while True:
        enable_location = input("\nDo you want to enable location tracking? (yes/no): ").strip().lower()
        if enable_location in ['yes', 'no']:
            break
        print("Error: Please enter 'yes' or 'no'.")
    inject_flutter_location_tracking(paths['manifest'], enable_location == 'yes')
    print("\nStep 11: Injecting Dart-side deeplink handler in main.dart...")
    inject_flutter_deeplink_handler(paths['main_dart'])
    print("\nStep 12: Prompting for scheme for test device pairing...")
    scheme = input("\nEnter the URI scheme for Adding test device (e.g., myapp): ").strip()
    if scheme:
        print("Step 13: Setting up scheme-based deep linking for test device...")
        # Add intent filter to launcher activity in manifest and get its android:name
        activity_name = add_flutter_scheme_intent_filter_to_manifest(paths['manifest'], scheme)
        main_activity_path = None
        if activity_name:
            # Convert android:name to file path
            # If fully qualified, use as is; if relative (starts with .), prepend application_id
            if activity_name.startswith('.'):
                # Prepend application_id
                java_path = os.path.join(paths['src_dir'], *(application_id.split('.')), activity_name[1:] + ".java")
                kt_path = os.path.join(paths['src_dir'], *(application_id.split('.')), activity_name[1:] + ".kt")
            elif '.' in activity_name:
                # Fully qualified
                java_path = os.path.join(paths['src_dir'], *(activity_name.split('.'))) + ".java"
                kt_path = os.path.join(paths['src_dir'], *(activity_name.split('.'))) + ".kt"
            else:
                # Just the class name
                java_path = os.path.join(paths['src_dir'], activity_name + ".java")
                kt_path = os.path.join(paths['src_dir'], activity_name + ".kt")
            if os.path.exists(java_path):
                main_activity_path = java_path
                activity_language = 'java'
            elif os.path.exists(kt_path):
                main_activity_path = kt_path
                activity_language = 'kotlin'
            else:
                # Fallback: search for file in src_dir
                for root, _, files in os.walk(paths['src_dir']):
                    for file in files:
                        if file == os.path.basename(java_path) or file == os.path.basename(kt_path):
                            main_activity_path = os.path.join(root, file)
                            activity_language = 'kotlin' if file.endswith('.kt') else 'java'
                            break
                    if main_activity_path:
                        break
            if main_activity_path:
                inject_flutter_deeplink_handling_code(main_activity_path, activity_language)
                print(f"   ✅ Injected deep link handling code in {main_activity_path}")
            else:
                print(f"   ⚠️ Could not find MainActivity file ({activity_name}) to inject deep link handling code.")
        else:
            print("   ⚠️ Could not find launcher activity to add intent filter.")
    else:
        print("   ⚠️ No scheme provided. Skipping scheme-based deep linking setup.")
    print("\n✅ Smartech SDK Flutter integration completed!")

if __name__ == "__main__":
    integrate_smartech_flutter() 