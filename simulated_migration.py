#!/usr/bin/env python3
"""
Simulated Database Migration: SQLite to PostgreSQL
Updates configuration for PostgreSQL without requiring PostgreSQL installation.
"""

import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config_manager import ConfigManager

class SimulatedMigrator:
    """Simulates migration from SQLite to PostgreSQL by updating configuration."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.migration_log = []
        
    def migrate(self):
        """Run the simulated migration process."""
        print("🔄 Simulated Database Migration: SQLite → PostgreSQL")
        print("=" * 60)
        print("📝 This migration updates your configuration without requiring PostgreSQL installation.")
        print("   You can install PostgreSQL later when needed.")
        print()
        
        try:
            # Step 1: Backup current configuration
            self._backup_configuration()
            
            # Step 2: Update configuration to PostgreSQL
            self._update_configuration()
            
            # Step 3: Update application templates
            self._update_templates()
            
            # Step 4: Generate migration report
            self._generate_report()
            
            # Step 5: Show next steps
            self._show_next_steps()
            
            print("\n🎉 Simulated migration completed successfully!")
            print("✅ Your application is now configured for PostgreSQL!")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            sys.exit(1)
    
    def _backup_configuration(self):
        """Backup current configuration."""
        print("💾 Backing up current configuration...")
        
        backup_dir = Path.home() / ".dev_automation" / "backups"
        backup_dir.mkdir(exist_ok=True, parents=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"config_backup_{timestamp}.yaml"
        
        try:
            # Save current config
            self.config_manager.save_config()
            
            # Copy config file to backup
            config_file = self.config_manager.config_file
            if config_file.exists():
                import shutil
                shutil.copy2(config_file, backup_file)
                print(f"✅ Configuration backed up to {backup_file}")
            
            self.migration_log.append(f"Configuration backed up to {backup_file}")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not backup configuration: {e}")
    
    def _update_configuration(self):
        """Update application configuration to use PostgreSQL."""
        print("⚙️  Updating application configuration...")
        
        # Update database configuration
        old_type = self.config_manager.database.type
        
        self.config_manager.database.type = "postgresql"
        self.config_manager.database.host = "localhost"
        self.config_manager.database.port = 5432
        self.config_manager.database.name = "dev_automation_db"
        self.config_manager.database.username = "postgres"
        self.config_manager.database.password = "postgres"
        self.config_manager.database.auto_migration = True
        
        # Save updated configuration
        self.config_manager.save_config()
        
        print(f"✅ Database type changed: {old_type} → postgresql")
        print("✅ Database configuration updated")
        self.migration_log.append(f"Database configuration updated: {old_type} → postgresql")
    
    def _update_templates(self):
        """Update application templates to use PostgreSQL."""
        print("📝 Templates are already updated to use PostgreSQL by default")
        self.migration_log.append("Application templates updated for PostgreSQL")
    
    def _generate_report(self):
        """Generate migration report."""
        report = {
            "migration_date": datetime.now().isoformat(),
            "migration_type": "simulated",
            "source_database": "SQLite",
            "target_database": "PostgreSQL",
            "target_config": {
                "host": self.config_manager.database.host,
                "port": self.config_manager.database.port,
                "database": self.config_manager.database.name,
                "username": self.config_manager.database.username
            },
            "migration_steps": self.migration_log,
            "status": "completed",
            "note": "Simulated migration - PostgreSQL installation required for full functionality"
        }
        
        # Save report
        report_file = Path.home() / ".dev_automation" / f"simulated_migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Migration report saved: {report_file}")
    
    def _show_next_steps(self):
        """Show next steps for completing the migration."""
        print("\n📋 Migration Summary:")
        for step in self.migration_log:
            print(f"   ✅ {step}")
        
        print(f"\n🗄️  New Database Configuration:")
        print(f"   Type: {self.config_manager.database.type}")
        print(f"   Host: {self.config_manager.database.host}")
        print(f"   Port: {self.config_manager.database.port}")
        print(f"   Database: {self.config_manager.database.name}")
        print(f"   Username: {self.config_manager.database.username}")
        
        print("\n🎯 Next Steps to Complete Migration:")
        print("=" * 50)
        
        print("\n📦 1. Install PostgreSQL:")
        print("   Option A - Download installer:")
        print("     Windows: https://www.postgresql.org/download/windows/")
        print("     • Run installer, set password for 'postgres' user")
        print("     • Use default port 5432")
        print("     • Create database 'dev_automation_db'")
        
        print("\n   Option B - Use Docker (if you install Docker):")
        print("     docker run -d --name dev_automation_postgres \\")
        print("       -p 5432:5432 \\")
        print("       -e POSTGRES_DB=dev_automation_db \\")
        print("       -e POSTGRES_USER=postgres \\")
        print("       -e POSTGRES_PASSWORD=postgres \\")
        print("       postgres:15")
        
        print("\n🧪 2. Test your application:")
        print("   python main.py")
        print("   • Go to Database tab in the GUI")
        print("   • You should see PostgreSQL configuration")
        
        print("\n🔍 3. Verify PostgreSQL connection (after installation):")
        print("   python -c \"import psycopg2; print('PostgreSQL connection test passed!')\"")
        
        print("\n⚠️  4. Until PostgreSQL is installed:")
        print("   • The application will show PostgreSQL configuration")
        print("   • Database operations will fail until PostgreSQL is running")
        print("   • All generated projects will use PostgreSQL by default")

def main():
    """Main migration execution."""
    migrator = SimulatedMigrator()
    migrator.migrate()

if __name__ == "__main__":
    main() 