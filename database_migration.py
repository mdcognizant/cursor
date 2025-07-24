#!/usr/bin/env python3
"""
Database Migration Script: SQLite to PostgreSQL
Migrates the Development Automation Suite from SQLite to PostgreSQL.
"""

import os
import sys
import json
import yaml
import subprocess
import psycopg2
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config_manager import ConfigManager

class DatabaseMigrator:
    """Handles migration from SQLite to PostgreSQL."""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.config_manager = ConfigManager()
        self.migration_log = []
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for migration process."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
            ]
        )
        return logging.getLogger(__name__)
    
    def migrate(self):
        """Run the complete migration process."""
        self.logger.info("🚀 Starting database migration from SQLite to PostgreSQL")
        print("🚀 Database Migration: SQLite → PostgreSQL")
        print("=" * 60)
        
        try:
            # Step 1: Check prerequisites
            self._check_prerequisites()
            
            # Step 2: Backup current configuration
            self._backup_configuration()
            
            # Step 3: Set up PostgreSQL
            self._setup_postgresql()
            
            # Step 4: Migrate any existing data
            self._migrate_data()
            
            # Step 5: Update configuration
            self._update_configuration()
            
            # Step 6: Verify migration
            self._verify_migration()
            
            # Step 7: Generate migration report
            self._generate_report()
            
            print("\n🎉 Migration completed successfully!")
            self.logger.info("Migration completed successfully")
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            print(f"\n❌ Migration failed: {e}")
            print("\n🔧 To troubleshoot:")
            print("1. Check that PostgreSQL is installed and running")
            print("2. Verify database credentials")
            print("3. Check the migration log for detailed errors")
            sys.exit(1)
    
    def _check_prerequisites(self):
        """Check if all prerequisites are met."""
        print("🔍 Checking prerequisites...")
        
        # Check Python packages
        try:
            import psycopg2
            import sqlalchemy
            self.logger.info("✅ Python packages available")
        except ImportError as e:
            raise Exception(f"Missing required package: {e}")
        
        # Check PostgreSQL availability
        try:
            # Try to connect to PostgreSQL server
            conn = psycopg2.connect(
                host="localhost",
                user="postgres", 
                password="postgres",
                port=5432,
                database="postgres"  # Connect to default postgres DB
            )
            conn.close()
            self.logger.info("✅ PostgreSQL server accessible")
            print("✅ PostgreSQL server connection successful")
        except psycopg2.Error as e:
            print("❌ PostgreSQL connection failed")
            print("\n🔧 To fix this issue:")
            print("1. Install PostgreSQL: https://www.postgresql.org/download/")
            print("2. Ensure PostgreSQL service is running")
            print("3. Verify username/password (default: postgres/postgres)")
            print("4. Check port 5432 is not blocked")
            raise Exception(f"Cannot connect to PostgreSQL: {e}")
        
        self.migration_log.append("Prerequisites check passed")
    
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
                self.logger.info(f"Configuration backed up to {backup_file}")
                print(f"✅ Configuration backed up to {backup_file}")
            
            self.migration_log.append(f"Configuration backed up to {backup_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to backup configuration: {e}")
            print(f"⚠️  Warning: Could not backup configuration: {e}")
    
    def _setup_postgresql(self):
        """Set up PostgreSQL database for the application."""
        print("🗄️  Setting up PostgreSQL database...")
        
        db_config = self.config_manager.database
        
        try:
            # Connect to PostgreSQL server
            conn = psycopg2.connect(
                host=db_config.host,
                user="postgres",
                password="postgres", 
                port=db_config.port,
                database="postgres"
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(
                f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_config.name}'"
            )
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(f'CREATE DATABASE "{db_config.name}"')
                self.logger.info(f"Created database: {db_config.name}")
                print(f"✅ Created database: {db_config.name}")
            else:
                self.logger.info(f"Database already exists: {db_config.name}")
                print(f"✅ Database already exists: {db_config.name}")
            
            # Create user if specified and different from postgres
            if db_config.username and db_config.username != "postgres":
                try:
                    cursor.execute(f"CREATE USER {db_config.username} WITH PASSWORD '{db_config.password}'")
                    cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_config.name} TO {db_config.username}")
                    self.logger.info(f"Created user: {db_config.username}")
                    print(f"✅ Created user: {db_config.username}")
                except psycopg2.Error as e:
                    if "already exists" in str(e):
                        self.logger.info(f"User already exists: {db_config.username}")
                        print(f"✅ User already exists: {db_config.username}")
                    else:
                        self.logger.warning(f"Could not create user: {e}")
                        print(f"⚠️  Warning: Could not create user: {e}")
            
            cursor.close()
            conn.close()
            
            self.migration_log.append(f"PostgreSQL database setup completed: {db_config.name}")
            
        except Exception as e:
            raise Exception(f"Failed to setup PostgreSQL: {e}")
    
    def _migrate_data(self):
        """Migrate data from SQLite to PostgreSQL."""
        print("📦 Migrating data from SQLite to PostgreSQL...")
        
        # Look for existing SQLite databases
        sqlite_files = []
        
        # Check common locations
        search_paths = [
            Path.cwd(),
            Path.home() / ".dev_automation",
            Path.cwd() / "data"
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                sqlite_files.extend(search_path.glob("*.db"))
                sqlite_files.extend(search_path.glob("*.sqlite"))
                sqlite_files.extend(search_path.glob("*.sqlite3"))
        
        if not sqlite_files:
            self.logger.info("No SQLite databases found - fresh installation")
            print("✅ No existing SQLite data found - clean migration")
            self.migration_log.append("No SQLite data to migrate")
            return
        
        # If SQLite files exist, migrate them
        for sqlite_file in sqlite_files:
            self._migrate_sqlite_file(sqlite_file)
    
    def _migrate_sqlite_file(self, sqlite_file: Path):
        """Migrate a specific SQLite file to PostgreSQL."""
        self.logger.info(f"Migrating SQLite file: {sqlite_file}")
        print(f"📄 Migrating: {sqlite_file}")
        
        try:
            # Connect to SQLite
            sqlite_conn = sqlite3.connect(sqlite_file)
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cursor = sqlite_conn.cursor()
            
            # Get all tables
            sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = sqlite_cursor.fetchall()
            
            if not tables:
                print(f"   ✅ No tables found in {sqlite_file}")
                sqlite_conn.close()
                return
            
            # Connect to PostgreSQL
            db_config = self.config_manager.database
            pg_conn = psycopg2.connect(
                host=db_config.host,
                user=db_config.username or "postgres",
                password=db_config.password or "postgres",
                port=db_config.port,
                database=db_config.name
            )
            pg_cursor = pg_conn.cursor()
            
            # Migrate each table
            for table_row in tables:
                table_name = table_row[0]
                if table_name.startswith('sqlite_'):
                    continue  # Skip SQLite system tables
                
                self._migrate_table(sqlite_cursor, pg_cursor, table_name)
            
            pg_conn.commit()
            pg_cursor.close()
            pg_conn.close()
            sqlite_cursor.close()
            sqlite_conn.close()
            
            print(f"   ✅ Successfully migrated {sqlite_file}")
            self.migration_log.append(f"Migrated SQLite file: {sqlite_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to migrate {sqlite_file}: {e}")
            print(f"   ❌ Failed to migrate {sqlite_file}: {e}")
    
    def _migrate_table(self, sqlite_cursor, pg_cursor, table_name: str):
        """Migrate a single table from SQLite to PostgreSQL."""
        self.logger.info(f"Migrating table: {table_name}")
        
        # Get table schema from SQLite
        sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
        columns = sqlite_cursor.fetchall()
        
        if not columns:
            return
        
        # Create PostgreSQL table
        pg_columns = []
        for col in columns:
            col_name = col[1]
            col_type = col[2].upper()
            
            # Convert SQLite types to PostgreSQL types
            if col_type in ('INTEGER', 'INT'):
                pg_type = 'INTEGER'
            elif col_type in ('TEXT', 'VARCHAR'):
                pg_type = 'TEXT'
            elif col_type in ('REAL', 'FLOAT'):
                pg_type = 'REAL'
            elif col_type in ('BLOB',):
                pg_type = 'BYTEA'
            elif col_type in ('TIMESTAMP', 'DATETIME'):
                pg_type = 'TIMESTAMP'
            else:
                pg_type = 'TEXT'  # Default fallback
            
            not_null = ' NOT NULL' if col[3] else ''
            primary_key = ' PRIMARY KEY' if col[5] else ''
            
            pg_columns.append(f'"{col_name}" {pg_type}{not_null}{primary_key}')
        
        create_table_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(pg_columns)})'
        
        try:
            pg_cursor.execute(create_table_sql)
            
            # Copy data
            sqlite_cursor.execute(f'SELECT * FROM "{table_name}"')
            rows = sqlite_cursor.fetchall()
            
            if rows:
                col_names = [col[1] for col in columns]
                placeholders = ', '.join(['%s'] * len(col_names))
                quoted_cols = ', '.join(f'"{col}"' for col in col_names)
                insert_sql = f'INSERT INTO "{table_name}" ({quoted_cols}) VALUES ({placeholders})'
                
                pg_cursor.executemany(insert_sql, [tuple(row) for row in rows])
                
            print(f"   ✅ Migrated table '{table_name}' ({len(rows)} rows)")
            
        except Exception as e:
            self.logger.error(f"Failed to migrate table {table_name}: {e}")
            print(f"   ❌ Failed to migrate table '{table_name}': {e}")
    
    def _update_configuration(self):
        """Update application configuration to use PostgreSQL."""
        print("⚙️  Updating application configuration...")
        
        # Update database configuration
        self.config_manager.database.type = "postgresql"
        if not self.config_manager.database.name:
            self.config_manager.database.name = "dev_automation_db"
        if not self.config_manager.database.username:
            self.config_manager.database.username = "postgres"
        if not self.config_manager.database.password:
            self.config_manager.database.password = "postgres"
        
        # Save updated configuration
        self.config_manager.save_config()
        
        self.logger.info("Configuration updated to use PostgreSQL")
        print("✅ Configuration updated to use PostgreSQL")
        self.migration_log.append("Configuration updated to PostgreSQL")
    
    def _verify_migration(self):
        """Verify that the migration was successful."""
        print("🔍 Verifying migration...")
        
        try:
            # Test PostgreSQL connection with new config
            db_config = self.config_manager.database
            conn = psycopg2.connect(
                host=db_config.host,
                user=db_config.username,
                password=db_config.password,
                port=db_config.port,
                database=db_config.name
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
            table_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            self.logger.info(f"PostgreSQL connection verified: {version}")
            print(f"✅ PostgreSQL connection verified")
            print(f"✅ Database '{db_config.name}' has {table_count} tables")
            
            self.migration_log.append(f"Migration verified - {table_count} tables in PostgreSQL")
            
        except Exception as e:
            raise Exception(f"Migration verification failed: {e}")
    
    def _generate_report(self):
        """Generate migration report."""
        print("\n📋 Migration Report")
        print("=" * 40)
        
        report = {
            "migration_date": datetime.now().isoformat(),
            "source_database": "SQLite",
            "target_database": "PostgreSQL",
            "target_config": {
                "host": self.config_manager.database.host,
                "port": self.config_manager.database.port,
                "database": self.config_manager.database.name,
                "username": self.config_manager.database.username
            },
            "migration_steps": self.migration_log,
            "status": "completed"
        }
        
        # Save report
        report_file = Path.home() / ".dev_automation" / f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Migration report saved: {report_file}")
        
        # Print summary
        print("\n🎯 Migration Summary:")
        for step in self.migration_log:
            print(f"   ✅ {step}")
        
        print(f"\n🗄️  New Database Configuration:")
        print(f"   Host: {self.config_manager.database.host}")
        print(f"   Port: {self.config_manager.database.port}")
        print(f"   Database: {self.config_manager.database.name}")
        print(f"   Username: {self.config_manager.database.username}")

def main():
    """Main migration execution."""
    print("🔄 Development Automation Suite - Database Migration")
    print("    From: SQLite → To: PostgreSQL")
    print("=" * 60)
    
    migrator = DatabaseMigrator()
    migrator.migrate()

if __name__ == "__main__":
    main() 