# PostgreSQL Setup Guide

## 🗄️ **PostgreSQL Database Setup for Development Automation Suite**

The Development Automation Suite has been **migrated from SQLite to PostgreSQL** for better performance, scalability, and robust data management.

---

## 📋 **Quick Setup Steps**

### **Step 1: Install PostgreSQL**

#### **Windows**
1. Download PostgreSQL from: https://www.postgresql.org/download/windows/
2. Run the installer and follow the setup wizard
3. Set the password for the `postgres` user (remember this!)
4. Default port is `5432` (keep this setting)

#### **macOS**
```bash
# Using Homebrew (recommended)
brew install postgresql
brew services start postgresql

# Or download from: https://www.postgresql.org/download/macos/
```

#### **Linux (Ubuntu/Debian)**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### **Step 2: Verify PostgreSQL Installation**
```bash
# Test connection (should prompt for password)
psql -h localhost -U postgres -d postgres
```

### **Step 3: Run the Migration Script**
```bash
python database_migration.py
```

---

## ⚙️ **Configuration Details**

### **Default Database Settings**
- **Host**: `localhost`
- **Port**: `5432`
- **Database Name**: `dev_automation_db`
- **Username**: `postgres`
- **Password**: `postgres` (change in production!)

### **Connection String**
```
postgresql://postgres:postgres@localhost:5432/dev_automation_db
```

---

## 🔧 **Troubleshooting**

### **Issue: "Could not connect to PostgreSQL"**
**Solutions:**
1. ✅ Ensure PostgreSQL service is running
2. ✅ Check username/password (default: postgres/postgres)
3. ✅ Verify port 5432 is not blocked by firewall
4. ✅ Try connecting manually: `psql -h localhost -U postgres`

### **Issue: "Permission denied for database"**
**Solutions:**
1. ✅ Run migration as administrator/sudo
2. ✅ Check PostgreSQL user permissions
3. ✅ Verify database exists

### **Issue: "Database already exists"**
**Solution:**
✅ This is normal - the migration script will use the existing database

---

## 🔐 **Security Recommendations**

### **For Development**
- Default settings are fine for local development
- Keep the `postgres/postgres` credentials for simplicity

### **For Production**
1. **Create a dedicated user:**
```sql
CREATE USER dev_automation WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE dev_automation_db TO dev_automation;
```

2. **Update configuration:**
```yaml
database:
  type: postgresql
  host: your-server.com
  port: 5432
  name: dev_automation_db
  username: dev_automation
  password: secure_password_here
```

3. **Enable SSL:**
```
postgresql://username:password@host:5432/database?sslmode=require
```

---

## 📊 **Benefits of PostgreSQL Migration**

### **Performance Improvements**
- ✅ **Concurrent Access**: Multiple users can work simultaneously
- ✅ **Advanced Indexing**: Faster queries and data retrieval
- ✅ **ACID Compliance**: Data integrity and consistency
- ✅ **Connection Pooling**: Better resource management

### **Advanced Features**
- ✅ **Full-Text Search**: Advanced search capabilities
- ✅ **JSON Support**: Store and query complex data structures
- ✅ **Extensions**: PostGIS, UUID, and more
- ✅ **Backup/Restore**: Robust backup and recovery options

### **Scalability**
- ✅ **Large Datasets**: Handle millions of records efficiently
- ✅ **Replication**: Master-slave replication for high availability
- ✅ **Partitioning**: Distribute large tables across multiple storage
- ✅ **Cloud Support**: Easy deployment to AWS RDS, Google Cloud SQL, etc.

---

## 🚀 **Post-Migration Verification**

### **Test Database Connection**
```bash
# Run the application
python main.py

# Check in GUI: Database tab should show PostgreSQL configuration
```

### **Verify Data Migration**
```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d dev_automation_db

# List tables
\dt

# Check data
SELECT COUNT(*) FROM your_table_name;
```

### **Check Application Logs**
- Migration log file: `migration_YYYYMMDD_HHMMSS.log`
- Migration report: `~/.dev_automation/migration_report_YYYYMMDD_HHMMSS.json`

---

## 📋 **Migration Report**

After running the migration, you'll receive a detailed report showing:

- ✅ **Migration Status**: Success/failure with details
- ✅ **Data Transferred**: Tables and row counts migrated
- ✅ **Configuration Updates**: New database settings
- ✅ **Backup Location**: Where old configuration was saved

---

## 🔄 **Rollback (if needed)**

If you need to rollback to SQLite:

1. **Restore configuration backup:**
```bash
cp ~/.dev_automation/backups/config_backup_YYYYMMDD_HHMMSS.yaml ~/.dev_automation/config.yaml
```

2. **Or manually edit configuration:**
```yaml
database:
  type: sqlite
  name: app.db
```

---

## 🎉 **Success Indicators**

After successful migration, you should see:

✅ **GUI Application**: Database tab shows PostgreSQL settings  
✅ **Migration Report**: Detailed migration summary  
✅ **No Errors**: Application starts without database errors  
✅ **Data Preservation**: All existing data migrated successfully  

---

*Migration completed successfully! Your Development Automation Suite now uses PostgreSQL for enhanced performance and reliability.* 