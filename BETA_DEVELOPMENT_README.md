# 🚧 BETA Development Environment

## 🎯 **Purpose**
This is the **Beta development branch** - an isolated environment for active application development, separate from the Alpha read-only archive.

---

## 🏗️ **Environment Structure**

### **📋 Branch Strategy**
- **🏷️ Alpha**: Read-only archive for reference and rollback
- **🚧 Beta**: Active development environment (THIS BRANCH)
- **🔄 main**: Stable releases and production-ready code

### **🎯 Beta Environment Goals**
- ✅ **Isolated Development**: Safe space to build new applications
- ✅ **Shell Monitor Integration**: All development protected from hanging
- ✅ **PostgreSQL Ready**: Database configured for robust applications
- ✅ **Cursor IDE Optimized**: Enhanced development experience
- ✅ **CI/CD Ready**: Automated workflows and deployment

---

## 🚀 **Getting Started in Beta**

### **1. Environment Setup**
```bash
# Clone Beta branch
git clone --branch Beta https://github.com/mdcognizant/cursor.git
cd cursor

# Or switch to Beta in existing repo
git checkout Beta

# Install dependencies
pip install -r requirements.txt
```

### **2. Development Tools Available**
- ✅ **Shell Monitor**: `python shellmonitor/shell_monitor.py run "command"`
- ✅ **PostgreSQL Tools**: `python database_migration.py`
- ✅ **Project Generator**: `python main.py`
- ✅ **Cursor Integration**: `cursor_integration/` directory

### **3. Create New Application**
```bash
# Use the Development Automation Suite to generate new project
python main.py

# Or use Shell Monitor for safe command execution
python shellmonitor/shell_monitor.py run "your-command-here"
```

---

## 🛡️ **Shell Monitor Protection**

**All development commands should use Shell Monitor to prevent hanging:**

```bash
# Safe Git operations
python shellmonitor/shell_monitor.py run "git status"
python shellmonitor/shell_monitor.py run "git commit -m 'message'"

# Safe NPM/Python operations  
python shellmonitor/shell_monitor.py run "npm install"
python shellmonitor/shell_monitor.py run "pip install package"

# Safe Docker operations
python shellmonitor/shell_monitor.py run "docker build -t myapp ."
```

---

## 🗄️ **Database Configuration**

### **PostgreSQL Ready**
- **Host**: localhost
- **Port**: 5432
- **Database**: dev_automation_db
- **Username**: postgres
- **Password**: postgres

### **Migration Tools**
```bash
# Set up PostgreSQL (if not installed)
python setup_postgresql_docker.py

# Run database migrations
python database_migration.py
```

---

## 📁 **Development Structure**

### **🏗️ Core Application Framework**
```
src/
├── automation/          # Project generation and CI/CD
├── core/               # Configuration and logging
└── gui/                # User interface components
```

### **🛡️ Shell Monitor Library**
```
shellmonitor/
├── monitor.py          # Core monitoring engine
├── diagnostics.py      # System diagnostics
├── cli.py             # Command-line interface
└── README.md          # Complete documentation
```

### **🔧 Cursor Integration**
```
cursor_integration/
├── bin/               # Command wrappers (git_monitor.bat, etc.)
├── enhanced_cursor_settings.json
└── install_cursor_integration.py
```

---

## 🚀 **Development Workflow**

### **1. Start New Feature**
```bash
# Create feature branch from Beta
git checkout -b feature/my-new-feature

# Use Shell Monitor for all operations
python shellmonitor/shell_monitor.py run "command"
```

### **2. Safe Development**
```bash
# Generate project structure
python main.py

# Test with Shell Monitor
python shellmonitor/shell_monitor.py run "python -m pytest"

# Commit safely
python shellmonitor/shell_monitor.py run "git add ."
python shellmonitor/shell_monitor.py run "git commit -m 'Add feature'"
```

### **3. Merge Back to Beta**
```bash
# Switch back to Beta
git checkout Beta

# Merge feature (using Shell Monitor)
python shellmonitor/shell_monitor.py run "git merge feature/my-new-feature"

# Push to GitHub
python shellmonitor/shell_monitor.py run "git push origin Beta"
```

---

## 🔄 **Integration with Alpha**

### **Reverting to Alpha (Clean Start)**
```bash
# If you need to start from scratch, revert to Alpha
git checkout Alpha
git checkout -b new-development-branch

# Alpha contains the original stable foundation
```

### **Cherry-picking from Alpha**
```bash
# Get specific commits from Alpha if needed
git cherry-pick <commit-hash-from-alpha>
```

---

## 📊 **Available Tools**

### **🛠️ Development Automation**
- **Project Scaffolding**: Multi-language project generation
- **CI/CD Pipelines**: GitHub Actions, GitLab CI, Jenkins
- **Docker Integration**: Container setup and orchestration
- **Database Migration**: SQLite to PostgreSQL migration

### **🛡️ Stability Tools**
- **Shell Monitor**: Prevents command hanging and timeouts
- **Diagnostics**: System health checking and performance monitoring
- **Cursor Integration**: Enhanced IDE experience with monitoring

### **🗄️ Database Tools**
- **PostgreSQL Setup**: Automated database configuration
- **Migration Scripts**: Safe data migration tools
- **Docker Database**: Containerized database setup

---

## ⚠️ **Important Notes**

### **🚫 DO NOT**
- Push directly to Alpha (it's read-only archive)
- Use unmonitored commands that might hang
- Skip Shell Monitor for Git operations

### **✅ DO**
- Use Shell Monitor for all command execution
- Create feature branches for new development
- Test thoroughly before merging to Beta
- Document new features and changes

---

## 🆘 **Troubleshooting**

### **Commands Hanging?**
```bash
# Always use Shell Monitor
python shellmonitor/shell_monitor.py run "your-command"

# Run diagnostics if issues persist
python shellmonitor/shell_monitor.py diagnose
```

### **Database Issues?**
```bash
# Check PostgreSQL status
python shellmonitor/shell_monitor.py run "psql --version"

# Reinstall if needed
python setup_postgresql_docker.py
```

### **Cursor Integration Problems?**
```bash
# Reinstall Cursor integration
python cursor_integration/setup_cursor_integration.py
```

---

## 📈 **Success Metrics**

**✅ Shell Monitor Active**: No hanging commands  
**✅ PostgreSQL Connected**: Database ready for development  
**✅ Cursor Integration**: Enhanced IDE experience  
**✅ CI/CD Ready**: Automated workflows available  
**✅ Isolated from Alpha**: Clean development environment  

---

*Beta Environment Created: July 24, 2025*  
*Status: 🚧 ACTIVE DEVELOPMENT - Ready for Application Building* 