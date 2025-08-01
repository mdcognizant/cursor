#!/usr/bin/env python3
"""
Template Backup Manager
======================
Manages backups and versions of news platform templates.

Features:
- Create timestamped backups
- List all available versions
- Restore from backup
- Switch between versions
- Compare template differences
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path

class TemplateBackupManager:
    def __init__(self):
        self.templates = {
            'v2_primary': 'enhanced_news_platform_ultimate_v2.html',
            'v2_backup': 'enhanced_news_platform_ultimate_v2_BACKUP_STABLE.html',
            'delta_complete': 'enhanced_delta_news_platform_complete.html'
        }
        
        self.backup_dir = 'template_backups'
        self.manifest_file = 'backup_manifest.json'
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Load or create manifest
        self.manifest = self.load_manifest()

    def load_manifest(self):
        """Load backup manifest or create new one"""
        try:
            if os.path.exists(self.manifest_file):
                with open(self.manifest_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading manifest: {e}")
        
        return {
            'created': datetime.now().isoformat(),
            'backups': [],
            'active_version': 'v2_primary',
            'last_backup': None
        }

    def save_manifest(self):
        """Save backup manifest"""
        try:
            with open(self.manifest_file, 'w') as f:
                json.dump(self.manifest, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving manifest: {e}")

    def create_backup(self, template_key, description="Manual backup"):
        """Create a timestamped backup of a template"""
        if template_key not in self.templates:
            print(f"❌ Unknown template: {template_key}")
            return False
        
        template_file = self.templates[template_key]
        
        if not os.path.exists(template_file):
            print(f"❌ Template file not found: {template_file}")
            return False
        
        # Create backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{template_key}_{timestamp}.html"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # Copy the file
            shutil.copy2(template_file, backup_path)
            
            # Update manifest
            backup_info = {
                'filename': backup_filename,
                'original_template': template_key,
                'original_file': template_file,
                'created': datetime.now().isoformat(),
                'description': description,
                'size_bytes': os.path.getsize(backup_path)
            }
            
            self.manifest['backups'].append(backup_info)
            self.manifest['last_backup'] = datetime.now().isoformat()
            self.save_manifest()
            
            print(f"✅ Backup created: {backup_filename}")
            print(f"📝 Description: {description}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
            return False

    def list_backups(self):
        """List all available backups"""
        print("📋 AVAILABLE TEMPLATE BACKUPS")
        print("=" * 50)
        
        if not self.manifest['backups']:
            print("No backups found.")
            return
        
        # Sort by creation date (newest first)
        sorted_backups = sorted(
            self.manifest['backups'], 
            key=lambda x: x['created'], 
            reverse=True
        )
        
        for i, backup in enumerate(sorted_backups, 1):
            size_mb = backup['size_bytes'] / (1024 * 1024)
            created = datetime.fromisoformat(backup['created']).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"{i:2}. {backup['filename']}")
            print(f"    📁 Original: {backup['original_template']}")
            print(f"    📅 Created: {created}")
            print(f"    📝 Description: {backup['description']}")
            print(f"    📊 Size: {size_mb:.1f} MB")
            print()

    def restore_backup(self, backup_filename, target_template=None):
        """Restore a backup to active template"""
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            print(f"❌ Backup file not found: {backup_filename}")
            return False
        
        # Find backup info in manifest
        backup_info = None
        for backup in self.manifest['backups']:
            if backup['filename'] == backup_filename:
                backup_info = backup
                break
        
        if not backup_info:
            print(f"❌ Backup not found in manifest: {backup_filename}")
            return False
        
        # Determine target template
        if target_template is None:
            target_template = backup_info['original_template']
        
        if target_template not in self.templates:
            print(f"❌ Unknown target template: {target_template}")
            return False
        
        target_file = self.templates[target_template]
        
        try:
            # Create a backup of current file before restoring
            if os.path.exists(target_file):
                self.create_backup(target_template, f"Auto-backup before restore from {backup_filename}")
            
            # Restore the backup
            shutil.copy2(backup_path, target_file)
            
            # Update manifest
            self.manifest['active_version'] = target_template
            self.save_manifest()
            
            print(f"✅ Restored {backup_filename} to {target_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to restore backup: {e}")
            return False

    def switch_version(self, new_version):
        """Switch to a different template version"""
        if new_version not in self.templates:
            print(f"❌ Unknown version: {new_version}")
            return False
        
        current_version = self.manifest['active_version']
        
        if current_version == new_version:
            print(f"ℹ️ Already using version: {new_version}")
            return True
        
        # Create backup of current version
        self.create_backup(current_version, f"Auto-backup before switching to {new_version}")
        
        # Update active version
        self.manifest['active_version'] = new_version
        self.save_manifest()
        
        print(f"✅ Switched from {current_version} to {new_version}")
        print(f"📁 Active template: {self.templates[new_version]}")
        return True

    def get_template_info(self):
        """Get information about all templates"""
        print("📊 TEMPLATE INFORMATION")
        print("=" * 50)
        
        for key, filename in self.templates.items():
            status = "✅ EXISTS" if os.path.exists(filename) else "❌ MISSING"
            active = "🔥 ACTIVE" if key == self.manifest['active_version'] else ""
            
            if os.path.exists(filename):
                size_mb = os.path.getsize(filename) / (1024 * 1024)
                modified = datetime.fromtimestamp(os.path.getmtime(filename)).strftime('%Y-%m-%d %H:%M:%S')
                print(f"{key:15} | {status} | {size_mb:5.1f} MB | {modified} {active}")
            else:
                print(f"{key:15} | {status} {active}")

    def create_all_backups(self):
        """Create backups of all existing templates"""
        print("🔄 Creating backups of all templates...")
        
        success_count = 0
        for key, filename in self.templates.items():
            if os.path.exists(filename):
                if self.create_backup(key, "Batch backup - all templates"):
                    success_count += 1
        
        print(f"✅ Created {success_count} backups")

    def cleanup_old_backups(self, keep_count=10):
        """Clean up old backups, keeping only the most recent"""
        if len(self.manifest['backups']) <= keep_count:
            print(f"ℹ️ Only {len(self.manifest['backups'])} backups exist (keeping all)")
            return
        
        # Sort by creation date (oldest first)
        sorted_backups = sorted(
            self.manifest['backups'], 
            key=lambda x: x['created']
        )
        
        # Determine which backups to delete
        to_delete = sorted_backups[:-keep_count]
        
        deleted_count = 0
        for backup in to_delete:
            backup_path = os.path.join(self.backup_dir, backup['filename'])
            try:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                    deleted_count += 1
                
                # Remove from manifest
                self.manifest['backups'].remove(backup)
                
            except Exception as e:
                print(f"❌ Failed to delete {backup['filename']}: {e}")
        
        if deleted_count > 0:
            self.save_manifest()
            print(f"🗑️ Cleaned up {deleted_count} old backups")

def show_menu():
    """Show interactive menu"""
    print("""
🗂️ TEMPLATE BACKUP MANAGER
==========================
1. List all backups
2. Create backup of V2 template
3. Create backup of all templates
4. Restore from backup
5. Switch template version
6. Show template information
7. Cleanup old backups
8. Exit

""")

def main():
    """Main interactive interface"""
    manager = TemplateBackupManager()
    
    print("🗂️ Template Backup Manager Initialized")
    print(f"📁 Backup directory: {manager.backup_dir}")
    print(f"📋 {len(manager.manifest['backups'])} backups available")
    print(f"🔥 Active version: {manager.manifest['active_version']}")
    
    while True:
        show_menu()
        choice = input("Select option (1-8): ").strip()
        
        if choice == '1':
            manager.list_backups()
            
        elif choice == '2':
            description = input("Enter backup description (optional): ").strip()
            if not description:
                description = "Manual backup"
            manager.create_backup('v2_primary', description)
            
        elif choice == '3':
            manager.create_all_backups()
            
        elif choice == '4':
            manager.list_backups()
            if manager.manifest['backups']:
                filename = input("Enter backup filename to restore: ").strip()
                if filename:
                    manager.restore_backup(filename)
            
        elif choice == '5':
            print("Available versions:")
            for key in manager.templates.keys():
                print(f"  - {key}")
            version = input("Enter version to switch to: ").strip()
            if version:
                manager.switch_version(version)
            
        elif choice == '6':
            manager.get_template_info()
            
        elif choice == '7':
            keep = input("How many backups to keep? (default: 10): ").strip()
            keep_count = int(keep) if keep.isdigit() else 10
            manager.cleanup_old_backups(keep_count)
            
        elif choice == '8':
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 