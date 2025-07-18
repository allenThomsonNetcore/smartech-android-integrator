import os

def create_flutter_backup_xml_files(project_dir, target_sdk):
    """Create backup configuration XML files for Flutter (android/app/src/main/res/xml)."""
    res_dir = os.path.join(project_dir, "android", "app", "src", "main", "res")
    xml_dir = os.path.join(res_dir, "xml")
    os.makedirs(xml_dir, exist_ok=True)
    # Create backup file for targetSdk < 31
    if target_sdk < 31:
        backup_file_path = os.path.join(xml_dir, "my_backup_file.xml")
        with open(backup_file_path, 'w') as f:
            f.write("""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<full-backup-content>
    <include domain=\"sharedpref\" path=\"smt_guid_preferences.xml\"/>
    <include domain=\"sharedpref\" path=\"smt_preferences_guid.xml\"/>
</full-backup-content>
""")
    # Create backup file for targetSdk >= 31
    if target_sdk >= 31:
        backup_file_path = os.path.join(xml_dir, "my_backup_file_31.xml")
        with open(backup_file_path, 'w') as f:
            f.write("""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<data-extraction-rules>
      <cloud-backup disableIfNoEncryptionCapabilities=\"false\">
       <include  domain=\"sharedpref\" path=\"smt_guid_preferences.xml\" />
       <include domain=\"sharedpref\" path=\"smt_preferences_guid.xml\" />
   </cloud-backup>
</data-extraction-rules>
""")
    print("   ✅ Backup XML files created in android/app/src/main/res/xml/") 