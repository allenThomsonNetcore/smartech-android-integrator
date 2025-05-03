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
    """Modify build.gradle file to add Smartech repository and dependencies."""
    with open(gradle_path, 'r') as f:
        content = f.read()
        
    # Check if it's a .kts file
    is_kts = gradle_path.endswith('.kts')
    
    # Add repository if not present
    repository = 'maven { url = uri("https://netcore.jfrog.io/netcore/libs-release") }' if is_kts else 'maven { url "https://netcore.jfrog.io/netcore/libs-release" }'
    if repository not in content:
        # Find the repositories block
        if is_kts:
            content = re.sub(r'(repositories\s*\{)', r'\1\n        ' + repository, content)
        else:
            content = re.sub(r'(repositories\s*\{)', r'\1\n        ' + repository, content)
    
    # Add core dependency if not present
    core_dependency = 'implementation("com.netcore.android:smartech-base:3.6.2")' if is_kts else 'implementation "com.netcore.android:smartech-base:3.6.2"'
    if 'com.netcore.android:smartech-base' not in content:
        # Find the dependencies block
        if is_kts:
            content = re.sub(r'(dependencies\s*\{)', r'\1\n    ' + core_dependency, content)
        else:
            content = re.sub(r'(dependencies\s*\{)', r'\1\n    ' + core_dependency, content)
    
    with open(gradle_path, 'w') as f:
        f.write(content)

def inject_push_dependency(gradle_path):
    """Inject push notification dependency into build.gradle file."""
    with open(gradle_path, 'r') as f:
        content = f.read()
        
    # Check if it's a .kts file
    is_kts = gradle_path.endswith('.kts')
    
    # Add push dependency if not present
    push_dependency = 'implementation("com.netcore.android:smartech-push:3.6.2")' if is_kts else 'implementation "com.netcore.android:smartech-push:3.6.2"'
    if 'com.netcore.android:smartech-push' not in content:
        # Find the dependencies block
        if is_kts:
            content = re.sub(r'(dependencies\s*\{)', r'\1\n    ' + push_dependency, content)
        else:
            content = re.sub(r'(dependencies\s*\{)', r'\1\n    ' + push_dependency, content)
    
    with open(gradle_path, 'w') as f:
        f.write(content) 