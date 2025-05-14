import os
import sys
from ..application.application_manager import find_application_class, create_application_class, inject_sdk_initialization, inject_debug_level, inject_notification_appearance, integrate_product_experience_listeners, register_product_experience_listeners
from ..deeplink.deeplink_manager import create_deeplink_receiver
from ..manifest.manifest_manager import integrate_product_experience_manifest, modify_manifest, inject_push_meta_tag, register_firebase_service, inject_location_tracking_meta_tag
from ..gradle.gradle_manager import add_core_sdk_version_to_properties, add_push_sdk_version_to_properties, extract_target_sdk, extract_application_id, integrate_product_experience_dependency, modify_gradle, inject_push_dependency, modify_settings_gradle
from ..push.push_manager import find_push_service_class, create_push_service_class, inject_push_logic
from ..backup.backup_manager import create_backup_xml_files

def validate_android_project(project_dir):
    """Validate that the project directory contains the required Android project structure."""
    required_paths = [
        os.path.join(project_dir, "app"),
        os.path.join(project_dir, "app", "src", "main"),
        os.path.join(project_dir, "app", "src", "main", "java"),
        os.path.join(project_dir, "app", "src", "main", "AndroidManifest.xml")
    ]
    
    # Check for either build.gradle or build.gradle.kts
    gradle_path = os.path.join(project_dir, "app", "build.gradle")
    gradle_kts_path = os.path.join(project_dir, "app", "build.gradle.kts")
    if not os.path.exists(gradle_path) and not os.path.exists(gradle_kts_path):
        required_paths.append("app/build.gradle or app/build.gradle.kts")
    
    missing_paths = [path for path in required_paths if not os.path.exists(path)]
    
    if missing_paths:
        print("\nError: The specified directory is not a valid Android project.")
        print("Missing required files/directories:")
        for path in missing_paths:
            print(f"- {os.path.relpath(path, project_dir) if isinstance(path, str) else path}")
        print("\nPlease make sure you're pointing to the root directory of an Android project.")
        return False
    
    return True

def get_user_input():
    """Get user input for project path and app ID."""
    while True:
        project_dir = input("Enter the path to your Android project directory: ").strip()
        if not os.path.exists(project_dir):
            print("Error: The specified directory does not exist. Please try again.")
            continue
            
        if not validate_android_project(project_dir):
            continue
            
        break

    while True:
        app_id = input("Enter your Smartech App ID: ").strip()
        if app_id:
            break
        print("Error: App ID cannot be empty. Please try again.")

    return project_dir, app_id

def integrate_smartech(project_dir, app_id):
    """
    Main integration function that orchestrates the Smartech SDK integration process.
    
    Args:
        project_dir (str): Path to the Android project directory
        app_id (str): Smartech App ID
    """
    try:
        print("\n 🧑🏻‍💻 Starting Smartech SDK integration process...")
        
        # Define paths
        app_dir = os.path.join(project_dir, "app")
        src_dir = os.path.join(app_dir, "src", "main", "java")
        manifest_path = os.path.join(app_dir, "src", "main", "AndroidManifest.xml")
        
        # Check for both gradle file types
        gradle_path = os.path.join(app_dir, "build.gradle")
        gradle_kts_path = os.path.join(app_dir, "build.gradle.kts")
        if os.path.exists(gradle_kts_path):
            gradle_path = gradle_kts_path

        # Check for settings.gradle file
        settings_path = os.path.join(project_dir, "settings.gradle")
        settings_kts_path = os.path.join(project_dir, "settings.gradle.kts")
        if os.path.exists(settings_kts_path):
            settings_path = settings_kts_path
        elif not os.path.exists(settings_path):
            print("Error: Could not find settings.gradle or settings.gradle.kts file")
            return False


        #finding gradle.properties file
        properties_path = os.path.join(project_dir, 'gradle.properties') 

        # Add Smartech repository to settings.gradle
        print("1. Adding Smartech repository...")
        modify_settings_gradle(settings_path)
        print("   ✅ Added Smartech repository to settings.gradle")

        # Extract target SDK version and application ID
        print("2. Extracting project information...")
        target_sdk = extract_target_sdk(gradle_path)
        application_id = extract_application_id(gradle_path)
        if not application_id:
            print("Error: Could not find applicationId in build.gradle file")
            return False
        print(f"   ✅ Target SDK version: {target_sdk}")
        print(f"   🔔 Application ID: {application_id}")

        # Find or create application class
        print("3. Setting up application class...")
        app_class_path, language = find_application_class(src_dir)
        if not app_class_path:
            app_class_path = create_application_class(src_dir, language,application_id)
            print("   ✅ Created new application class")
        else:
            print("   ⚠️ Found existing application class")
        
        # Create deep link receiver
        print("4. Setting up deep link receiver...")
        create_deeplink_receiver(src_dir, language,application_id)
        print("   ✅ Deep link receiver configured")

        # Modify manifest
        print("5. Updating Android manifest...")
        app_class_relative = os.path.relpath(app_class_path, src_dir).replace(os.sep, '.').replace('.java', '').replace('.kt', '')
        modify_manifest(manifest_path, app_id, app_class_relative, target_sdk)
        print("   ✅ Manifest updated with Smartech configurations")

        # Modify gradle
        print("6. Updating Gradle configuration...")
        modify_gradle(gradle_path)
        print("   ✅ Gradle configuration updated")


        add_core_sdk_version_to_properties(properties_path)

        # Create backup configuration files
        print("7. Setting up backup configuration...")
        create_backup_xml_files(project_dir, target_sdk, manifest_path)
        print("   ✅ Backup configuration created")

        # Inject SDK initialization
        print("8. Injecting SDK initialization...")
        inject_sdk_initialization(app_class_path, language, target_sdk)
        print("   ✅ SDK initialization code injected")

        # Ask about debug logs
        while True:
            enable_debug = input("\nDo you want to enable debug logs? (yes/no): ").strip().lower()
            if enable_debug in ['yes', 'no']:
                break
            print("Error: Please enter 'yes' or 'no'.")

        # Inject debug level setting
        print("9. Setting debug level...")
        inject_debug_level(app_class_path, language, enable_debug == 'yes')
        print(f"   ✅ Debug logs {'enabled' if enable_debug == 'yes' else 'disabled'}")

        # Ask about location tracking
        while True:
            enable_location = input("\nDo you want to enable location tracking? (yes/no): ").strip().lower()
            if enable_location in ['yes', 'no']:
                break
            print("Error: Please enter 'yes' or 'no'.")

        # Inject location tracking meta tag
        print("10. Setting location tracking...")
        inject_location_tracking_meta_tag(manifest_path, enable_location == 'yes')
        print(f"   ✅ Location tracking: {'Enabled' if enable_location == 'yes' else 'Disabled'}")

        print("\nCore Smartech SDK integration completed successfully!")
        print(f"Project directory: {project_dir}")
        print(f"Smartech App ID: {app_id}")

        # Ask about push SDK integration
        while True:
            integrate_push = input("\nDo you want to integrate Push SDK? (yes/no): ").strip().lower()
            if integrate_push in ['yes', 'no']:
                break
            print("Error: Please enter 'yes' or 'no'.")

        if integrate_push == 'yes':
            print("\nStarting Push SDK integration process...")
            
            # Handle push notifications
            print("1. Setting up push notification service...")
            push_class_path, push_language = find_push_service_class(src_dir)
            if not push_class_path:
                push_class_path = create_push_service_class(src_dir, language,application_id)
                print("   🔔 Created new push notification service")
            else:
                inject_push_logic(push_class_path, push_language)
                print("   ✅ Updated existing push notification service")

            # Register Firebase service in manifest
            print("2. Registering Firebase service in manifest...")
            service_name = os.path.basename(push_class_path).replace('.kt', '').replace('.java', '')
            register_firebase_service(manifest_path, service_name)
            print("   🔔 Firebase service registered")

            # Add push dependency to gradle
            print("3. Adding push dependencies to Gradle...")
            inject_push_dependency(gradle_path)
            print("   🔔 Push dependencies added")

            add_push_sdk_version_to_properties(properties_path)

            # Ask about push permission
            while True:
                ask_permission = input("\nDo you want to ask for push notification permission? (yes/no): ").strip().lower()
                if ask_permission in ['yes', 'no']:
                    break
                print("Error: Please enter 'yes' or 'no'.")

            # Update manifest with push permission setting
            print("4. Updating push notification settings...")
            inject_push_meta_tag(manifest_path, ask_permission == 'yes')
            print(f"   ✅ Push notification permission: {'Enabled' if ask_permission == 'yes' else 'Disabled'}")

            # Ask about notification appearance
            while True:
                modify_notification = input("\nDo you want to modify notification appearance? (yes/no): ").strip().lower()
                if modify_notification in ['yes', 'no']:
                    break
                print("Error: Please enter 'yes' or 'no'.")

            if modify_notification == 'yes':
                print("\nPlease provide the resource names for notification customization (press Enter to skip any option):")
                notification_options = {}
                
                brand_logo = input("Brand logo resource name (e.g., logo): ").strip()
                if brand_logo:
                    notification_options['brand_logo'] = brand_logo

                large_icon = input("Large icon resource name (e.g., icon_notification): ").strip()
                if large_icon:
                    notification_options['large_icon'] = large_icon

                small_icon = input("Small icon resource name (e.g., ic_action_play): ").strip()
                if small_icon:
                    notification_options['small_icon'] = small_icon

                small_icon_transparent = input("Transparent small icon resource name (e.g., ic_action_play): ").strip()
                if small_icon_transparent:
                    notification_options['small_icon_transparent'] = small_icon_transparent

                transparent_bg_color = input("Transparent icon background color (e.g., #FF0000): ").strip()
                if transparent_bg_color:
                    notification_options['transparent_bg_color'] = transparent_bg_color

                placeholder_icon = input("Placeholder icon resource name (e.g., ic_notification): ").strip()
                if placeholder_icon:
                    notification_options['placeholder_icon'] = placeholder_icon

                if notification_options:
                    print("10. Setting notification appearance...")
                    inject_notification_appearance(app_class_path, language, notification_options)
                    print("   ✅ Notification appearance configured")

            print("\n 🔔 Push SDK integration completed successfully!")

        # --- Product Experience SDK Integration ---
        while True:
            integrate_product_exp = input("\nDo you want to integrate Product Experience SDK? (yes/no): ").strip().lower()
            if integrate_product_exp in ['yes', 'no']:
                break
            print("Error: Please enter 'yes' or 'no'.")

        if integrate_product_exp == 'yes':
            hansel_app_id = input("Enter the Hansel APP ID: ").strip()
            hansel_app_key = input("Enter the Hansel APP Key: ").strip()
            while True:
                ui_type = input("Is your app UI Jetpack Compose or Native Views? (compose/native): ").strip().lower()
                if ui_type in ['compose', 'native']:
                    break
                print("Error: Please enter 'compose' or 'native'.")

            print("\nIntegrating Product Experience SDK...")
            # Dependency injection
            integrate_product_experience_dependency(gradle_path, ui_type)
            # Manifest meta-data
            integrate_product_experience_manifest(manifest_path, hansel_app_id, hansel_app_key)
            # Listener classes
            integrate_product_experience_listeners(src_dir, language,application_id)
            # Register listeners in application class
            register_product_experience_listeners(app_class_path, language)
            print("   ✅ Product Experience SDK integration completed!")

        print("\nIntegration process completed!")
        print(f"Project directory: {project_dir}")
        print(f"Smartech App ID: {app_id}")

    except Exception as e:
        print(f"\nError during integration: {str(e)}")
        print("Please check the error message above and try again.")
        return False
    
    return True

if __name__ == "__main__":
    print("🛠  Welcome to Smartech SDK Integrator!")
    print(" 🩺This tool will help you integrate the Smartech SDK into your Android project.")
    print("\nPlease provide the following information:")
    
    print("🔧 Smartech SDK Integration for Android Native")
    framework = input("Enter framework (android, flutter, react-native): ").strip().lower()
    if framework != "android":
        print("❌ Only Android Native is supported right now.")
        sys.exit(1)

    project_dir, app_id = get_user_input()
    
    print("\nStarting integration process...")
    if integrate_smartech(project_dir, app_id):
        print("\n ✅🧑🏻‍💻Integration completed successfully! ✅🧑🏻‍💻")
    else:
        print("\n ❌❌❌ Integration failed. Please check the error messages above. ❌❌❌") 