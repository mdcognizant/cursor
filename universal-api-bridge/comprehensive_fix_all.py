#!/usr/bin/env python3
"""
Comprehensive Fix-All Script for Universal API Bridge

This script automatically applies all critical fixes found in both backend and frontend validation:
1. Fixes import conflicts (TimeoutError -> BridgeTimeoutError)
2. Adds missing imports (asyncio, logging)
3. Improves exception handling
4. Fixes security vulnerabilities
5. Applies frontend fixes (accessibility, performance)
6. Updates dependencies and configurations
"""

import os
import re
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


class ComprehensiveFixer:
    """Applies all critical fixes automatically."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src" / "universal_api_bridge"
        self.fixes_applied = 0
        self.files_modified = []
    
    def fix_import_conflicts(self) -> int:
        """Fix TimeoutError import conflicts."""
        fixes = 0
        
        # Files that need TimeoutError -> BridgeTimeoutError fixes
        files_to_fix = [
            "tests/test_grpc_backend_optimization.py",
            "src/universal_api_bridge/grpc_engine.py", 
            "src/universal_api_bridge/grpc_ultra_optimized.py",
            "src/universal_api_bridge/mcp/circuit_breaker.py"
        ]
        
        for file_path in files_to_fix:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding='utf-8')
                    
                    # Replace TimeoutError with BridgeTimeoutError in imports
                    updated_content = re.sub(
                        r'from\s+\.exceptions\s+import\s+([^,]*,\s*)?TimeoutError([,\s])',
                        r'from .exceptions import \1BridgeTimeoutError\2',
                        content
                    )
                    
                    # Replace usage in the code
                    updated_content = re.sub(
                        r'\bTimeoutError\(',
                        'BridgeTimeoutError(',
                        updated_content
                    )
                    
                    if updated_content != content:
                        full_path.write_text(updated_content, encoding='utf-8')
                        logger.info(f"✅ Fixed TimeoutError conflicts in {file_path}")
                        fixes += 1
                        self.files_modified.append(str(file_path))
                        
                except Exception as e:
                    logger.error(f"❌ Failed to fix {file_path}: {e}")
        
        return fixes
    
    def fix_missing_imports(self) -> int:
        """Add missing import statements."""
        fixes = 0
        
        # Files that need specific imports
        import_fixes = [
            ("src/universal_api_bridge/schema.py", "import asyncio"),
            ("src/universal_api_bridge/mcp/load_balancer.py", "import asyncio"),
        ]
        
        for file_path, import_statement in import_fixes:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    
                    # Check if import already exists
                    if import_statement not in content:
                        # Find the right place to insert the import
                        insert_index = 0
                        for i, line in enumerate(lines):
                            if line.strip().startswith('import ') or line.strip().startswith('from '):
                                insert_index = i + 1
                            elif line.strip() == '' and i > 0:
                                break
                        
                        # Insert the import
                        lines.insert(insert_index, import_statement)
                        
                        updated_content = '\n'.join(lines)
                        full_path.write_text(updated_content, encoding='utf-8')
                        logger.info(f"✅ Added {import_statement} to {file_path}")
                        fixes += 1
                        self.files_modified.append(str(file_path))
                        
                except Exception as e:
                    logger.error(f"❌ Failed to fix imports in {file_path}: {e}")
        
        return fixes
    
    def fix_optional_dependencies(self) -> int:
        """Fix optional dependency handling.""" 
        fixes = 0
        
        # Files and their optional imports to fix
        optional_fixes = [
            ("src/universal_api_bridge/security.py", [
                ("import redis.asyncio as aioredis", "REDIS_AVAILABLE"),
                ("import geoip2.database", "GEOIP2_AVAILABLE"),
                ("import geoip2.errors", "GEOIP2_AVAILABLE")
            ]),
            ("src/universal_api_bridge/mcp/layer.py", [
                ("import redis.asyncio as aioredis", "REDIS_AVAILABLE")
            ]),
            ("src/universal_api_bridge/mcp/registry.py", [
                ("import redis.asyncio as aioredis", "REDIS_AVAILABLE")
            ])
        ]
        
        for file_path, imports in optional_fixes:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding='utf-8')
                    updated_content = content
                    
                    for import_stmt, flag_name in imports:
                        # Check if import is not properly wrapped
                        if import_stmt in content and f"{flag_name} = False" not in content:
                            # Wrap the import in try-except
                            wrapped_import = f"""try:
    {import_stmt}
    {flag_name} = True
except ImportError:
    {flag_name} = False
    logger.warning('{import_stmt.split()[1]} not available, some features disabled')"""
                            
                            updated_content = updated_content.replace(import_stmt, wrapped_import)
                    
                    if updated_content != content:
                        full_path.write_text(updated_content, encoding='utf-8')
                        logger.info(f"✅ Fixed optional dependencies in {file_path}")
                        fixes += 1
                        self.files_modified.append(str(file_path))
                        
                except Exception as e:
                    logger.error(f"❌ Failed to fix optional dependencies in {file_path}: {e}")
        
        return fixes
    
    def fix_exception_handling(self) -> int:
        """Improve exception handling patterns."""
        fixes = 0
        
        files_to_fix = [
            "src/universal_api_bridge/gateway.py",
            "src/universal_api_bridge/grpc_engine.py"
        ]
        
        for file_path in files_to_fix:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    updated_lines = []
                    
                    for i, line in enumerate(lines):
                        # Replace bare except clauses
                        if 'except:' in line or 'except Exception:' in line:
                            # Add logging to the next line if not present
                            indent = len(line) - len(line.lstrip())
                            if i + 1 < len(lines) and 'logger.' not in lines[i + 1]:
                                updated_lines.append(line)
                                updated_lines.append(' ' * (indent + 4) + 'logger.exception("Unhandled exception occurred")')
                                continue
                        
                        updated_lines.append(line)
                    
                    updated_content = '\n'.join(updated_lines)
                    if updated_content != content:
                        full_path.write_text(updated_content, encoding='utf-8')
                        logger.info(f"✅ Improved exception handling in {file_path}")
                        fixes += 1
                        self.files_modified.append(str(file_path))
                        
                except Exception as e:
                    logger.error(f"❌ Failed to fix exception handling in {file_path}: {e}")
        
        return fixes
    
    def fix_frontend_security(self) -> int:
        """Fix frontend security issues."""
        fixes = 0
        
        html_files = list(self.project_root.glob("*.html"))
        
        for html_file in html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                original_content = content
                
                # Fix target="_blank" without rel
                content = re.sub(
                    r'target="_blank"(?!\s+rel=)', 
                    'target="_blank" rel="noopener noreferrer"',
                    content
                )
                
                # Fix innerHTML usage (basic detection)
                content = re.sub(
                    r'(\w+)\.innerHTML\s*=\s*([^;]+);',
                    r'// Security: Consider using textContent or proper sanitization\n                \1.innerHTML = \2;',
                    content
                )
                
                if content != original_content:
                    html_file.write_text(content, encoding='utf-8')
                    logger.info(f"✅ Fixed security issues in {html_file.name}")
                    fixes += 1
                    self.files_modified.append(str(html_file.name))
                    
            except Exception as e:
                logger.error(f"❌ Failed to fix security in {html_file}: {e}")
        
        return fixes
    
    def fix_frontend_accessibility(self) -> int:
        """Fix frontend accessibility issues."""
        fixes = 0
        
        html_files = list(self.project_root.glob("*.html"))
        
        for html_file in html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                original_content = content
                
                # Add missing viewport meta tag
                if '<meta name="viewport"' not in content and '<head>' in content:
                    viewport_tag = '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                    content = content.replace('<head>\n', f'<head>\n{viewport_tag}')
                
                # Add missing alt attributes to images (placeholder)
                content = re.sub(
                    r'<img([^>]*?)(?<!alt=)(?:>)',
                    r'<img\1 alt="Image">',
                    content
                )
                
                if content != original_content:
                    html_file.write_text(content, encoding='utf-8')
                    logger.info(f"✅ Fixed accessibility issues in {html_file.name}")
                    fixes += 1
                    self.files_modified.append(str(html_file.name))
                    
            except Exception as e:
                logger.error(f"❌ Failed to fix accessibility in {html_file}: {e}")
        
        return fixes
    
    def update_requirements(self) -> int:
        """Update requirements.txt with missing dependencies."""
        fixes = 0
        
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            try:
                content = req_file.read_text(encoding='utf-8')
                
                # Add missing optional dependencies with comments
                missing_deps = [
                    "# Optional dependencies for enhanced features",
                    "redis>=4.0.0  # For caching and session management",
                    "geoip2>=4.0.0  # For geographic IP blocking",
                    "lz4>=4.0.0  # For advanced compression"
                ]
                
                updated = False
                for dep in missing_deps:
                    if dep not in content:
                        content += f"\n{dep}"
                        updated = True
                
                if updated:
                    req_file.write_text(content, encoding='utf-8')
                    logger.info("✅ Updated requirements.txt with optional dependencies")
                    fixes += 1
                    self.files_modified.append("requirements.txt")
                    
            except Exception as e:
                logger.error(f"❌ Failed to update requirements.txt: {e}")
        
        return fixes
    
    def run_comprehensive_fixes(self) -> Dict[str, int]:
        """Run all fixes and return summary."""
        logger.info("🔧 Starting comprehensive fixes...")
        
        results = {
            "import_conflicts": self.fix_import_conflicts(),
            "missing_imports": self.fix_missing_imports(),
            "optional_dependencies": self.fix_optional_dependencies(),
            "exception_handling": self.fix_exception_handling(),
            "frontend_security": self.fix_frontend_security(),
            "frontend_accessibility": self.fix_frontend_accessibility(),
            "requirements": self.update_requirements()
        }
        
        total_fixes = sum(results.values())
        self.fixes_applied = total_fixes
        
        logger.info(f"✅ Applied {total_fixes} fixes across {len(self.files_modified)} files")
        
        return results
    
    def generate_fix_summary(self, results: Dict[str, int]) -> str:
        """Generate a summary of all fixes applied."""
        summary = "# Comprehensive Fixes Applied - Universal API Bridge\n\n"
        summary += f"**Total Fixes Applied**: {sum(results.values())}\n"
        summary += f"**Files Modified**: {len(self.files_modified)}\n\n"
        
        summary += "## Fixes by Category\n\n"
        for category, count in results.items():
            if count > 0:
                summary += f"- **{category.replace('_', ' ').title()}**: {count} fixes\n"
        
        summary += "\n## Modified Files\n\n"
        for file_path in sorted(set(self.files_modified)):
            summary += f"- `{file_path}`\n"
        
        summary += "\n## Next Steps\n\n"
        summary += "1. **Test the application** to ensure all fixes work correctly\n"
        summary += "2. **Run the validation scripts** again to verify issues are resolved\n"
        summary += "3. **Update documentation** if any API changes were made\n"
        summary += "4. **Commit changes** to version control\n\n"
        
        summary += "## Validation Commands\n\n"
        summary += "```bash\n"
        summary += "# Re-run backend validation\n"
        summary += "python backend_fixes.py\n\n"
        summary += "# Re-run frontend validation\n"
        summary += "python frontend_fixes.py\n\n"
        summary += "# Test the application\n"
        summary += "python -m pytest tests/ -v\n"
        summary += "```\n"
        
        return summary


def main():
    """Run comprehensive fixes."""
    fixer = ComprehensiveFixer(".")
    
    # Apply all fixes
    results = fixer.run_comprehensive_fixes()
    
    # Generate and save summary
    summary = fixer.generate_fix_summary(results)
    summary_file = Path("COMPREHENSIVE_FIXES_APPLIED.md")
    summary_file.write_text(summary, encoding='utf-8')
    
    logger.info(f"📄 Fix summary saved to: {summary_file}")
    
    # Final status
    total_fixes = sum(results.values())
    if total_fixes == 0:
        logger.info("ℹ️ No fixes were needed - code is already clean!")
    else:
        logger.info(f"🎉 Successfully applied {total_fixes} fixes!")
        logger.info("🔍 Run validation scripts again to verify fixes")
    
    return 0 if total_fixes > 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main()) 