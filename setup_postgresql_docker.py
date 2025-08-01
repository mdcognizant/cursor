#!/usr/bin/env python3
"""
Quick PostgreSQL Setup using Docker
Sets up PostgreSQL in a Docker container for development.
"""

import subprocess
import time
import psycopg2
import os
import sys

def check_docker():
    """Check if Docker is available."""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker available: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker not found. Please install Docker Desktop:")
        print("   Windows: https://desktop.docker.com/win/stable/Docker%20Desktop%20Installer.exe")
        print("   macOS: https://desktop.docker.com/mac/stable/Docker.dmg")
        print("   Linux: https://docs.docker.com/engine/install/")
        return False

def setup_postgresql_docker():
    """Set up PostgreSQL using Docker."""
    print("🐳 Setting up PostgreSQL with Docker...")
    
    container_name = "dev_automation_postgres"
    
    # Check if container already exists
    try:
        result = subprocess.run(['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
                              capture_output=True, text=True)
        if container_name in result.stdout:
            print(f"📦 Container '{container_name}' already exists")
            
            # Check if it's running
            result = subprocess.run(['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}'],
                                  capture_output=True, text=True)
            if container_name in result.stdout:
                print("✅ PostgreSQL container is already running")
                return True
            else:
                print("🔄 Starting existing PostgreSQL container...")
                subprocess.run(['docker', 'start', container_name], check=True)
                time.sleep(5)  # Wait for startup
                print("✅ PostgreSQL container started")
                return True
    except subprocess.CalledProcessError:
        pass
    
    # Create new container
    print("📦 Creating new PostgreSQL container...")
    
    docker_cmd = [
        'docker', 'run', '-d',
        '--name', container_name,
        '-p', '5432:5432',
        '-e', 'POSTGRES_DB=dev_automation_db',
        '-e', 'POSTGRES_USER=postgres', 
        '-e', 'POSTGRES_PASSWORD=postgres',
        '-v', 'dev_automation_postgres_data:/var/lib/postgresql/data',
        'postgres:15'
    ]
    
    try:
        subprocess.run(docker_cmd, check=True)
        print("✅ PostgreSQL container created successfully")
        
        print("⏳ Waiting for PostgreSQL to start...")
        time.sleep(10)  # Wait for PostgreSQL to initialize
        
        # Test connection
        max_retries = 30
        for i in range(max_retries):
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    user="postgres",
                    password="postgres",
                    port=5432,
                    database="dev_automation_db"
                )
                conn.close()
                print("✅ PostgreSQL is ready!")
                return True
            except psycopg2.Error:
                if i < max_retries - 1:
                    print(f"⏳ Waiting for PostgreSQL... ({i+1}/{max_retries})")
                    time.sleep(2)
                else:
                    print("❌ PostgreSQL failed to start properly")
                    return False
                    
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create PostgreSQL container: {e}")
        return False

def show_connection_info():
    """Show PostgreSQL connection information."""
    print("\n📋 PostgreSQL Connection Info:")
    print("=" * 40)
    print("Host: localhost")
    print("Port: 5432")
    print("Database: dev_automation_db")
    print("Username: postgres")
    print("Password: postgres")
    print("Connection URL: postgresql://postgres:postgres@localhost:5432/dev_automation_db")

def main():
    """Main setup process."""
    print("🚀 PostgreSQL Quick Setup for Development Automation Suite")
    print("=" * 60)
    
    if not check_docker():
        print("\n🔧 Alternative: Install PostgreSQL directly")
        print("   Windows: https://www.postgresql.org/download/windows/")
        print("   macOS: brew install postgresql")
        print("   Linux: sudo apt install postgresql")
        return False
    
    if setup_postgresql_docker():
        show_connection_info()
        
        print("\n🎯 Next Steps:")
        print("1. Run the migration script: python database_migration.py")
        print("2. Or start the application: python main.py")
        
        # Create a docker management script
        create_docker_management_script()
        
        return True
    else:
        print("\n❌ Failed to setup PostgreSQL")
        return False

def create_docker_management_script():
    """Create a script to manage the PostgreSQL Docker container."""
    
    script_content = '''@echo off
REM PostgreSQL Docker Management Script

if "%1"=="start" (
    echo Starting PostgreSQL container...
    docker start dev_automation_postgres
    echo PostgreSQL started!
    goto end
)

if "%1"=="stop" (
    echo Stopping PostgreSQL container...
    docker stop dev_automation_postgres
    echo PostgreSQL stopped!
    goto end
)

if "%1"=="restart" (
    echo Restarting PostgreSQL container...
    docker restart dev_automation_postgres
    echo PostgreSQL restarted!
    goto end
)

if "%1"=="status" (
    echo PostgreSQL container status:
    docker ps --filter name=dev_automation_postgres
    goto end
)

if "%1"=="logs" (
    echo PostgreSQL container logs:
    docker logs dev_automation_postgres
    goto end
)

if "%1"=="connect" (
    echo Connecting to PostgreSQL...
    docker exec -it dev_automation_postgres psql -U postgres -d dev_automation_db
    goto end
)

echo PostgreSQL Docker Management
echo Usage: postgres_docker.bat [command]
echo Commands:
echo   start    - Start PostgreSQL container
echo   stop     - Stop PostgreSQL container  
echo   restart  - Restart PostgreSQL container
echo   status   - Show container status
echo   logs     - Show container logs
echo   connect  - Connect to PostgreSQL shell

:end
'''
    
    with open('postgres_docker.bat', 'w') as f:
        f.write(script_content)
    
    print("\n📜 Created PostgreSQL management script: postgres_docker.bat")
    print("   Usage: postgres_docker.bat start|stop|restart|status|logs|connect")

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 PostgreSQL setup complete!")
    else:
        print("\n💡 You can also install PostgreSQL manually and run: python database_migration.py")
        sys.exit(1) 