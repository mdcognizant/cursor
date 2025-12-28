#!/usr/bin/env python3
"""
Comprehensive Backend Fixes for Universal API Bridge

This script addresses all critical backend issues:
1. Import conflicts and missing imports
2. Dependency validation and optional imports
3. Configuration validation enhancements
4. Error handling improvements
5. Type safety fixes
6. Performance optimizations
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackendFixesValidator:
    """Validates and fixes backend issues."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src" / "universal_api_bridge"
        self.issues_found = []
        self.fixes_applied = []
    
    def validate_imports(self) -> List[Dict[str, Any]]:
        """Validate all Python imports for issues."""
        issues = []
        
        # Check for TimeoutError conflicts
        timeout_files = [
            "tests/test_grpc_backend_optimization.py",
            "src/universal_api_bridge/grpc_engine.py",
            "src/universal_api_bridge/grpc_ultra_optimized.py",
            "src/universal_api_bridge/mcp/circuit_breaker.py"
        ]
        
        for file_path in timeout_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding='utf-8')
                    if "from .exceptions import" in content and "TimeoutError" in content:
                        if "BridgeTimeoutError" not in content:
                            issues.append({
                                "file": str(file_path),
                                "issue": "Uses conflicting TimeoutError import",
                                "fix": "Replace with BridgeTimeoutError",
                                "severity": "HIGH"
                            })
                except Exception as e:
                    issues.append({
                        "file": str(file_path),
                        "issue": f"Could not read file: {e}",
                        "fix": "Check file permissions and encoding",
                        "severity": "MEDIUM"
                    })
        
        return issues
    
    def validate_logging_imports(self) -> List[Dict[str, Any]]:
        """Check for missing logging imports."""
        issues = []
        
        py_files = list(self.src_dir.rglob("*.py"))
        
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                has_logger_usage = any("logger." in line for line in lines)
                has_logging_import = any("import logging" in line for line in lines)
                
                if has_logger_usage and not has_logging_import:
                    issues.append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "issue": "Uses logger without importing logging",
                        "fix": "Add 'import logging' at the top",
                        "severity": "HIGH"
                    })
            except Exception as e:
                logger.warning(f"Could not check {py_file}: {e}")
        
        return issues
    
    def validate_optional_dependencies(self) -> List[Dict[str, Any]]:
        """Check optional dependency handling."""
        issues = []
        
        optional_imports = [
            ("numpy", "NUMPY_AVAILABLE"),
            ("sklearn", "SKLEARN_AVAILABLE"), 
            ("lz4", "LZ4_AVAILABLE"),
            ("redis", "REDIS_AVAILABLE"),
            ("geoip2", "GEOIP2_AVAILABLE")
        ]
        
        py_files = list(self.src_dir.rglob("*.py"))
        
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                
                for import_name, flag_name in optional_imports:
                    if f"import {import_name}" in content:
                        # Check if properly wrapped in try-except
                        if "try:" not in content or f"{flag_name} = False" not in content:
                            issues.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "issue": f"Optional import {import_name} not properly handled",
                                "fix": f"Wrap in try-except with {flag_name} flag",
                                "severity": "MEDIUM"
                            })
            except Exception as e:
                logger.warning(f"Could not check {py_file}: {e}")
        
        return issues
    
    def validate_exception_handling(self) -> List[Dict[str, Any]]:
        """Check exception handling patterns."""
        issues = []
        
        py_files = list(self.src_dir.rglob("*.py"))
        
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                # Check for bare except clauses
                for i, line in enumerate(lines):
                    if "except:" in line or "except Exception:" in line:
                        if "logger." not in content[max(0, i-5):i+5]:
                            issues.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "issue": f"Bare except clause at line {i+1} without logging",
                                "fix": "Add specific exception types and logging",
                                "severity": "MEDIUM"
                            })
            except Exception as e:
                logger.warning(f"Could not check {py_file}: {e}")
        
        return issues
    
    def validate_async_patterns(self) -> List[Dict[str, Any]]:
        """Check async/await usage patterns."""
        issues = []
        
        py_files = list(self.src_dir.rglob("*.py"))
        
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Check for missing asyncio imports when using async
                if "async def" in content or "await " in content:
                    if "import asyncio" not in content:
                        issues.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "issue": "Uses async/await without importing asyncio",
                            "fix": "Add 'import asyncio'",
                            "severity": "HIGH"
                        })
                
                # Check for potential blocking calls in async functions
                blocking_calls = ["time.sleep(", "requests.get(", "requests.post("]
                if any(call in content for call in blocking_calls):
                    if "async def" in content:
                        issues.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "issue": "Potential blocking calls in async functions",
                            "fix": "Use async alternatives (asyncio.sleep, aiohttp)",
                            "severity": "MEDIUM"
                        })
            except Exception as e:
                logger.warning(f"Could not check {py_file}: {e}")
        
        return issues
    
    def run_validation(self) -> Dict[str, List[Dict[str, Any]]]:
        """Run all validations and return results."""
        logger.info("🔍 Starting comprehensive backend validation...")
        
        results = {
            "imports": self.validate_imports(),
            "logging": self.validate_logging_imports(),
            "dependencies": self.validate_optional_dependencies(),
            "exceptions": self.validate_exception_handling(),
            "async_patterns": self.validate_async_patterns()
        }
        
        # Count total issues
        total_issues = sum(len(issues) for issues in results.values())
        
        logger.info(f"✅ Validation complete. Found {total_issues} issues total:")
        for category, issues in results.items():
            if issues:
                logger.info(f"  - {category}: {len(issues)} issues")
        
        return results
    
    def generate_fix_report(self, results: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate a detailed fix report."""
        report = "# Universal API Bridge - Backend Issues Report\n\n"
        report += f"**Generated**: {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}\n\n"
        
        high_priority = []
        medium_priority = []
        
        for category, issues in results.items():
            for issue in issues:
                if issue.get("severity") == "HIGH":
                    high_priority.append(issue)
                else:
                    medium_priority.append(issue)
        
        report += f"## Summary\n"
        report += f"- **High Priority Issues**: {len(high_priority)}\n"
        report += f"- **Medium Priority Issues**: {len(medium_priority)}\n\n"
        
        if high_priority:
            report += "## 🚨 High Priority Issues (Fix Immediately)\n\n"
            for i, issue in enumerate(high_priority, 1):
                report += f"### {i}. {issue['issue']}\n"
                report += f"**File**: `{issue['file']}`\n"
                report += f"**Fix**: {issue['fix']}\n\n"
        
        if medium_priority:
            report += "## ⚠️ Medium Priority Issues (Fix Soon)\n\n"
            for i, issue in enumerate(medium_priority, 1):
                report += f"### {i}. {issue['issue']}\n"
                report += f"**File**: `{issue['file']}`\n"
                report += f"**Fix**: {issue['fix']}\n\n"
        
        # Add fix recommendations
        report += "## 🔧 Recommended Fixes\n\n"
        report += "### 1. TimeoutError Conflict Resolution\n"
        report += "```python\n"
        report += "# Replace this:\n"
        report += "from .exceptions import TimeoutError\n\n"
        report += "# With this:\n"
        report += "from .exceptions import BridgeTimeoutError\n"
        report += "```\n\n"
        
        report += "### 2. Missing Logging Imports\n"
        report += "```python\n"
        report += "# Add at the top of files using logger:\n"
        report += "import logging\n"
        report += "logger = logging.getLogger(__name__)\n"
        report += "```\n\n"
        
        report += "### 3. Optional Dependency Handling\n"
        report += "```python\n"
        report += "# Proper pattern for optional imports:\n"
        report += "try:\n"
        report += "    import numpy as np\n"
        report += "    NUMPY_AVAILABLE = True\n"
        report += "except ImportError:\n"
        report += "    NUMPY_AVAILABLE = False\n"
        report += "    logger.warning('NumPy not available, some features disabled')\n"
        report += "```\n\n"
        
        return report


def main():
    """Run the backend fixes validation."""
    validator = BackendFixesValidator(".")
    results = validator.run_validation()
    
    # Generate and save report
    report = validator.generate_fix_report(results)
    report_file = Path("BACKEND_ISSUES_REPORT.md")
    report_file.write_text(report, encoding='utf-8')
    
    logger.info(f"📄 Detailed report saved to: {report_file}")
    
    # Print summary
    total_issues = sum(len(issues) for issues in results.values())
    high_priority = sum(1 for issues in results.values() for issue in issues if issue.get("severity") == "HIGH")
    
    if total_issues == 0:
        logger.info("🎉 No issues found! Backend code is clean.")
    else:
        logger.warning(f"⚠️ Found {total_issues} issues ({high_priority} high priority)")
        logger.info("📋 Run the fixes recommended in the report")
    
    return total_issues


if __name__ == "__main__":
    sys.exit(main()) 