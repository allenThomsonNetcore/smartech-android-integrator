import yaml
import os

def add_flutter_pubspec_dependency(pubspec_path):
    """Add or update smartech_base dependency in pubspec.yaml."""
    with open(pubspec_path, 'r') as f:
        pubspec = yaml.safe_load(f)
    if 'dependencies' not in pubspec:
        pubspec['dependencies'] = {}
    pubspec['dependencies']['smartech_base'] = '^3.5.0'
    with open(pubspec_path, 'w') as f:
        yaml.dump(pubspec, f, default_flow_style=False, sort_keys=False)
    print("   ✅ Added/updated smartech_base dependency in pubspec.yaml") 