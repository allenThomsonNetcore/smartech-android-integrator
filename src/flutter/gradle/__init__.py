import os
import re

def update_flutter_gradle(gradle_path, properties_path):
    """Add Smartech dependency and version to build.gradle(.kts) and gradle.properties."""
    with open(gradle_path, 'r') as f:
        content = f.read()
    is_kts = gradle_path.endswith('.kts')
    core_dependency = 'implementation("com.netcore.android:smartech-sdk:3.6.2")' if is_kts else 'implementation "com.netcore.android:smartech-sdk:${SMARTECH_BASE_SDK_VERSION}"'
    if 'com.netcore.android:smartech-sdk' not in content:
        if re.search(r'dependencies\s*\{', content):
            content = re.sub(r'(dependencies\s*\{)', r'\1\n    ' + core_dependency, content)
        else:
            content += f"\n\ndependencies {{\n    {core_dependency}\n}}\n"
    with open(gradle_path, 'w') as f:
        f.write(content)
    # gradle.properties
    version_key = 'SMARTECH_BASE_SDK_VERSION'
    version_value = '3.5.8'
    prop_content = ""
    if os.path.exists(properties_path):
        with open(properties_path, 'r') as f:
            prop_content = f.read()
    if version_key not in prop_content:
        prop_content += f"\n{version_key}={version_value}"
    else:
        prop_content = re.sub(f'^{version_key}=.*$', f'{version_key}={version_value}', prop_content, flags=re.MULTILINE)
    with open(properties_path, 'w') as f:
        f.write(prop_content.strip() + "\n")
    print(f"   ✅ Dependency and version added to {os.path.basename(gradle_path)} and gradle.properties")

def modify_flutter_settings_gradle(settings_path):
    """Add Smartech repository to settings.gradle or settings.gradle.kts (reuse native logic)."""
    with open(settings_path, 'r') as f:
        content = f.read()
    is_kts = settings_path.endswith('.kts')
    repository = 'maven { url = uri("https://artifacts.netcore.co.in/artifactory/android") }' if is_kts else 'maven { url "https://artifacts.netcore.co.in/artifactory/android" }'
    if repository not in content:
        if re.search(r'dependencyResolutionManagement\s*\{', content):
            if re.search(r'repositories\s*\{', content):
                content = re.sub(r'(repositories\s*\{)', r'\1\n        ' + repository, content)
            else:
                content = re.sub(r'(dependencyResolutionManagement\s*\{)', r'\1\n    repositories {\n        ' + repository + '\n    }', content)
        else:
            new_block = f'dependencyResolutionManagement {{\n    repositories {{\n        {repository}\n    }}\n}}\n\n'
            content = new_block + content
    with open(settings_path, 'w') as f:
        f.write(content)
    print(f"   ✅ Smartech repository added to {os.path.basename(settings_path)}") 