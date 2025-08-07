# Universal API Bridge - Requirements Guide

## 🎯 **CRITICAL ISSUES FIXED**

This guide addresses the **2 critical consistency issues** identified in the code review:
1. ❌ **Multiple conflicting requirements files** → ✅ **Organized requirements/ structure**
2. ❌ **Flask vs FastAPI version conflicts** → ✅ **Compatible versions with clear purposes**

---

## 📁 **New Requirements Structure**

```
requirements/
├── base.txt              # Core dependencies (all systems)
├── polygon_mcp_grpc.txt  # MCP + gRPC production (PRIMARY)
├── development.txt       # Development and testing
└── production.txt        # Production optimizations
```

---

## 🚀 **For MCP + gRPC Systems (PRIMARY USE CASE)**

### **Quick Start:**
```bash
pip install -r requirements/polygon_mcp_grpc.txt
```

### **What This Includes:**
- ✅ **FastAPI** (primary framework for MCP layer)
- ✅ **Flask** (backward compatibility for legacy endpoints)
- ✅ **gRPC** (backend communication)
- ✅ **Mathematical optimizations** (numpy, sortedcontainers)
- ✅ **Async support** (aiohttp, uvicorn)

### **Compatible Systems:**
- `polygon_universal_bridge_server.py` ✅
- `mcp_grpc_polygon_launcher.py` ✅
- All V5+ Polygon interfaces ✅

---

## 🔧 **For Development:**

```bash
pip install -r requirements/development.txt
```

**Includes everything from polygon_mcp_grpc.txt plus:**
- Testing frameworks (pytest, coverage)
- Code quality tools (black, flake8, mypy)
- Documentation tools (sphinx)
- Database development tools

---

## 🏭 **For Production Deployment:**

```bash
pip install -r requirements/production.txt
```

**Includes everything from polygon_mcp_grpc.txt plus:**
- Production server optimizations (gunicorn, uvloop)
- Monitoring and logging (structlog, sentry)
- Enhanced security and performance
- Database connection pooling

---

## 🔄 **Migration from Old Requirements**

### **Before (PROBLEMATIC):**
```bash
# Multiple conflicting files:
pip install -r requirements.txt                        # Development suite
pip install -r requirements_polygon_production.txt     # Basic Flask only
pip install -r universal_bridge_minimal_requirements.txt # FastAPI conflicts
```

### **After (FIXED):**
```bash
# Single command for your use case:
pip install -r requirements/polygon_mcp_grpc.txt       # MCP + gRPC systems
pip install -r requirements/development.txt            # Development
pip install -r requirements/production.txt             # Production
```

---

## 🎯 **System-Specific Recommendations**

### **🔥 MCP + gRPC Production (RECOMMENDED):**
- **Use:** `requirements/polygon_mcp_grpc.txt`
- **Launcher:** `python mcp_grpc_polygon_launcher.py`
- **Server:** `polygon_universal_bridge_server.py`
- **Architecture:** REST → MCP → gRPC → Polygon.io

### **🛠️ Basic HTTP Only (Legacy):**
- **Use:** `requirements/base.txt` + Flask
- **Launcher:** `python reliable_polygon_launcher.py`
- **Server:** `working_polygon_bridge_bulletproof.py`
- **Architecture:** REST → HTTP → Polygon.io

### **🧪 Development & Testing:**
- **Use:** `requirements/development.txt`
- **Includes:** All testing tools + MCP + gRPC

---

## ✅ **Compatibility Matrix**

| System | FastAPI | Flask | gRPC | MCP Layer | Status |
|--------|---------|-------|------|-----------|---------|
| **polygon_mcp_grpc.txt** | ✅ Primary | ✅ Compatible | ✅ Full | ✅ Complete | **RECOMMENDED** |
| **development.txt** | ✅ Primary | ✅ Compatible | ✅ Full | ✅ Complete | Testing |
| **production.txt** | ✅ Primary | ✅ Compatible | ✅ Full | ✅ Complete | Deployment |
| **base.txt** | ❌ | ❌ | ❌ | ❌ | Core only |

---

## 🔧 **Troubleshooting**

### **Version Conflicts Resolved:**
- **Flask 2.3.3** + **FastAPI 0.104.0+** = ✅ **Compatible**
- **gRPC 1.60.0+** + **FastAPI** = ✅ **Optimized for MCP**
- **numpy 1.24.0+** = ✅ **Mathematical optimizations**

### **If You Get Import Errors:**
```bash
# Clean install (recommended):
pip uninstall flask fastapi grpcio -y
pip install -r requirements/polygon_mcp_grpc.txt
```

---

## 📋 **Summary**

**✅ FIXED CRITICAL ISSUES:**
1. **Requirements Conflicts** → Organized structure with clear purposes
2. **Dependency Versions** → Compatible Flask + FastAPI + gRPC stack
3. **Hard Import Dependencies** → Optional imports with fallbacks (numpy, gRPC)

**🎯 FOR MCP + gRPC SYSTEMS:**
```bash
pip install -r requirements/polygon_mcp_grpc.txt
python mcp_grpc_polygon_launcher.py
```

**🏆 RESULT:** Clean, conflict-free dependency management for the Universal API Bridge with full MCP and gRPC capabilities. 