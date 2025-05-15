import re
import os

def extract_target_sdk(gradle_path):
    """Extract targetSdkVersion from build.gradle file."""
    with open(gradle_path, 'r') as f:
        content = f.read()
        
    # Check if it's a .kts file
    is_kts = gradle_path.endswith('.kts')
    
    # Pattern for both .gradle and .gradle.kts
    pattern = r'targetSdk\s*(?:=|)\s*(\d+)'
    match = re.search(pattern, content)
    if match:
        return int(match.group(1))
    return 33  # Default to 33 if not found

def extract_application_id(gradle_path):
    """Extract applicationId from build.gradle file."""
    with open(gradle_path, 'r') as f:
        content = f.read()
        
    # Check if it's a .kts file
    is_kts = gradle_path.endswith('.kts')
    
    # Pattern for both .gradle and .gradle.kts
    pattern = r'applicationId\s*(?:=|)\s*["\']([^"\']+)["\']'
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    return None

def modify_gradle(gradle_path):
    """Modify build.gradle file to add Smartech dependencies."""
    with open(gradle_path, 'r') as f:
        content = f.read()
        
    # Check if it's a .kts file
    is_kts = gradle_path.endswith('.kts')
    
    # Add core dependency if not present
    core_dependency = 'implementation("com.netcore.android:smartech-sdk:3.6.2")' if is_kts else 'implementation "com.netcore.android:smartech-sdk:${SMARTECH_BASE_SDK_VERSION}"'
    if 'com.netcore.android:smartech-base' not in content:
        # Find the dependencies block
        if is_kts:
            content = re.sub(r'(dependencies\s*\{)', r'\1\n    ' + core_dependency, content)
        else:
            content = re.sub(r'(dependencies\s*\{)', r'\1\n    ' + core_dependency, content)
    
    with open(gradle_path, 'w') as f:
        f.write(content)

def modify_settings_gradle(settings_path):
    """Modify settings.gradle file to add Smartech repository."""
    with open(settings_path, 'r') as f:
        content = f.read()
        
    # Check if it's a .kts file
    is_kts = settings_path.endswith('.kts')
    
    # Add repository if not present
    repository = 'maven { url = uri("https://artifacts.netcore.co.in/artifactory/android") }' if is_kts else 'maven { url "https://artifacts.netcore.co.in/artifactory/android" }'
    
    if repository not in content:
        if re.search(r'dependencyResolutionManagement\s*\{', content):
            # Add inside existing dependencyResolutionManagement block
            if re.search(r'repositories\s*\{', content):
                # Add inside existing repositories block
                content = re.sub(r'(repositories\s*\{)', r'\1\n        ' + repository, content)
            else:
                # Add repositories block inside dependencyResolutionManagement
                content = re.sub(r'(dependencyResolutionManagement\s*\{)', r'\1\n    repositories {\n        ' + repository + '\n    }', content)
        else:
            # Add dependencyResolutionManagement block at the top
            new_block = f'dependencyResolutionManagement {{\n    repositories {{\n        {repository}\n    }}\n}}\n\n'
            content = new_block + content
    
    with open(settings_path, 'w') as f:
        f.write(content)

def inject_push_dependency(gradle_path):
    """Inject push notification dependency into build.gradle file."""
    with open(gradle_path, 'r') as f:
        content = f.read()
        
    # Check if it's a .kts file
    is_kts = gradle_path.endswith('.kts')
    
    # Add push dependency if not present
    push_dependency = 'implementation("com.netcore.android:smartech-push:3.5.6")' if is_kts else 'implementation "com.netcore.android:smartech-push:${SMARTECH_BASE_SDK_VERSION}"'
    if 'com.netcore.android:smartech-push' not in content:
        # Find the dependencies block
        if is_kts:
            content = re.sub(r'(dependencies\s*\{)', r'\1\n    ' + push_dependency, content)
        else:
            content = re.sub(r'(dependencies\s*\{)', r'\1\n    ' + push_dependency, content)
    
    with open(gradle_path, 'w') as f:
        f.write(content)

def integrate_product_experience_dependency(gradle_path, ui_type):
    """Inject Product Experience SDK dependency based on UI type."""
    with open(gradle_path, 'r') as f:
        content = f.read()
    is_kts = gradle_path.endswith('.kts')
    if ui_type == 'compose':
        dep = 'implementation("com.netcore.android:smartech-nudges-compose:10.5.2")' if is_kts else 'implementation "com.netcore.android:smartech-nudges-compose:10.5.2"'
    else:
        dep = 'implementation("com.netcore.android:smartech-nudges:10.2.5")' if is_kts else 'implementation "com.netcore.android:smartech-nudges:10.2.5"'
    if 'com.netcore.android:smartech-nudges' not in content and 'com.netcore.android:smartech-nudges-compose' not in content:
        content = re.sub(r'(dependencies\s*\{)', r'\1\n    ' + dep, content)
        with open(gradle_path, 'w') as f:
            f.write(content) 


def add_core_sdk_version_to_properties(properties_path,gradle_path):
    """Add or update Smartech Core SDK version in gradle.properties file."""
    is_kts = gradle_path.endswith('.kts')
    if is_kts:
        return
    version_key = 'SMARTECH_BASE_SDK_VERSION'
    version_value = '3.5.8'
    
    # Read existing properties if file exists
    content = ""
    if os.path.exists(properties_path):
        with open(properties_path, 'r') as f:
            content = f.read()
    
    # Check if version already exists and update it
    if version_key in content:
        # Update existing version
        pattern = f'^{version_key}=.*$'
        content = re.sub(pattern, f'{version_key}={version_value}', content, flags=re.MULTILINE)
    else:
        # Add new version
        content += f"\n{version_key}={version_value}"
    
    # Write back to file
    with open(properties_path, 'w') as f:
        f.write(content.strip() + "\n")

def add_push_sdk_version_to_properties(properties_path,gradle_path):
    """Add or update Smartech Push SDK version in gradle.properties file."""
    is_kts = gradle_path.endswith('.kts')
    if is_kts:
        return
    version_key = 'SMARTECH_PUSH_SDK_VERSION'
    version_value = '3.5.4'
    
    # Read existing properties if file exists
    content = ""
    if os.path.exists(properties_path):
        with open(properties_path, 'r') as f:
            content = f.read()
    
    # Check if version already exists and update it
    if version_key in content:
        # Update existing version
        pattern = f'^{version_key}=.*$'
        content = re.sub(pattern, f'{version_key}={version_value}', content, flags=re.MULTILINE)
    else:
        # Add new version
        content += f"\n{version_key}={version_value}"
    
    # Write back to file
    with open(properties_path, 'w') as f:
        f.write(content.strip() + "\n")
                  