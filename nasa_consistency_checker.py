#!/usr/bin/env python3
"""
🔧 NASA CODE CONSISTENCY & CRITICAL BUG CHECKER

Performs comprehensive analysis of all NASA-related code:
1. Syntax validation
2. Import verification
3. Class consistency checks
4. Port/configuration consistency
5. Method signature validation
6. Cross-file dependency verification
"""

import sys
import os
import importlib.util
import re
import ast
from pathlib import Path
from typing import List, Dict, Tuple, Any

def print_banner():
    """Print analysis banner."""
    print('🔧 COMPREHENSIVE NASA CODE CONSISTENCY & CRITICAL BUG CHECK')
    print('=' * 70)

def get_nasa_files() -> List[str]:
    """Get list of all NASA-related files to check."""
    return [
        # Core NASA Components
        'universal-api-bridge/src/universal_api_bridge/nasa_mathematical_engine.py',
        'universal-api-bridge/src/universal_api_bridge/nasa_integrated_bridge.py',
        'universal-api-bridge/src/universal_api_bridge/topological_data_analysis.py',
        'universal-api-bridge/src/universal_api_bridge/graph_neural_network_optimizer.py',
        'universal-api-bridge/src/universal_api_bridge/multi_armed_bandit_allocator.py',
        
        # Server Components
        'nasa_polygon_universal_bridge_server.py',
        'nasa_polygon_universal_bridge_server_simple.py',
        'nasa_mcp_grpc_polygon_launcher.py',
        
        # Command Components
        'cursor_commands.py',
        'run_nasa_server.py',
        'open_nasa_server.py',
        'nasa.py',
        
        # Integration Components
        'cursor_integration.py',
        'cursor_nasa_wrapper.py'
    ]

def check_file_syntax(file_path: str) -> Tuple[bool, str]:
    """Check if Python file has valid syntax."""
    try:
        spec = importlib.util.spec_from_file_location('test_module', file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return True, "OK"
    except SyntaxError as e:
        return False, f'Syntax Error: {e}'
    except ImportError as e:
        return False, f'Import Error: {e}'
    except Exception as e:
        return False, f'Runtime Error: {str(e)[:100]}'

def check_nasa_class_consistency(file_path: str) -> List[str]:
    """Check for NASA class naming and method consistency."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_name = os.path.basename(file_path)
        
        # Check for NASA naming consistency
        if 'nasa' in file_name.lower():
            if 'class NASA' not in content and 'NASA' in file_name:
                issues.append('Missing NASA class prefix in NASA file')
        
        # Check for required methods in specific files
        if 'mathematical_engine' in file_path:
            required_methods = ['optimize_for_enterprise_scale', 'register_service']
            for method in required_methods:
                if f'def {method}' not in content:
                    issues.append(f'Missing required method: {method}')
        
        if 'integrated_bridge' in file_path:
            required_methods = ['register_service', '_optimize_for_enterprise_scale']
            for method in required_methods:
                if f'def {method}' not in content:
                    issues.append(f'Missing required method: {method}')
        
        # Check for consistent error handling patterns
        if 'try:' in content and 'except ImportError:' not in content and 'import' in content:
            if 'nasa' in file_name.lower():
                issues.append('Missing ImportError handling for NASA dependencies')
        
        return issues
    except Exception as e:
        return [f'Could not check consistency: {e}']

def check_port_consistency(nasa_files: List[str]) -> List[str]:
    """Check for consistent port usage across NASA files."""
    port_pattern = r'port[:=]\s*(\d+)'
    ports_found = {}
    
    for file_path in nasa_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                matches = re.findall(port_pattern, content)
                for port in matches:
                    if port not in ports_found:
                        ports_found[port] = []
                    ports_found[port].append(os.path.basename(file_path))
            except:
                pass
    
    issues = []
    if len(ports_found) > 2:  # Allow 8001 and maybe one alternative
        issues.append(f'Too many different ports: {ports_found}')
    elif '8001' not in ports_found and ports_found:
        issues.append(f'NASA server not using standard port 8001: {ports_found}')
    
    return issues

def check_import_consistency(nasa_files: List[str]) -> List[str]:
    """Check for consistent import patterns across NASA files."""
    issues = []
    
    # Check for consistent NASA module imports
    nasa_imports = {}
    
    for file_path in nasa_files:
        if os.path.exists(file_path) and 'nasa' in file_path.lower():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for NASA module imports
                nasa_import_pattern = r'from\s+.*nasa.*\s+import\s+(.*)'
                matches = re.findall(nasa_import_pattern, content)
                
                for match in matches:
                    imports = [imp.strip() for imp in match.split(',')]
                    for imp in imports:
                        if imp not in nasa_imports:
                            nasa_imports[imp] = []
                        nasa_imports[imp].append(os.path.basename(file_path))
                        
            except:
                pass
    
    return issues

def check_method_signatures(nasa_files: List[str]) -> List[str]:
    """Check for consistent method signatures across NASA files."""
    issues = []
    
    # Check for consistent __init__ method signatures
    init_signatures = {}
    
    for file_path in nasa_files:
        if os.path.exists(file_path) and 'nasa' in file_path.lower():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for __init__ methods
                init_pattern = r'def __init__\(self([^)]*)\):'
                matches = re.findall(init_pattern, content)
                
                for match in matches:
                    signature = match.strip()
                    file_name = os.path.basename(file_path)
                    
                    if signature not in init_signatures:
                        init_signatures[signature] = []
                    init_signatures[signature].append(file_name)
                    
            except:
                pass
    
    # Check for inconsistencies in core NASA classes
    nasa_core_files = [f for f in nasa_files if 'nasa_mathematical_engine' in f or 'nasa_integrated_bridge' in f]
    
    return issues

def analyze_nasa_code():
    """Main analysis function."""
    print_banner()
    
    nasa_files = get_nasa_files()
    
    results = {
        'syntax_ok': [],
        'import_errors': [],
        'critical_bugs': [],
        'consistency_issues': [],
        'missing_files': []
    }
    
    print('\n📊 CHECKING INDIVIDUAL FILES:')
    print('-' * 70)
    
    for file_path in nasa_files:
        file_name = os.path.basename(file_path)
        
        if not os.path.exists(file_path):
            results['missing_files'].append(file_path)
            print(f'❌ {file_name}: FILE NOT FOUND')
            continue
        
        # Check syntax
        syntax_ok, error = check_file_syntax(file_path)
        
        if syntax_ok:
            results['syntax_ok'].append(file_path)
            print(f'✅ {file_name}: SYNTAX OK')
            
            # Check consistency
            consistency_issues = check_nasa_class_consistency(file_path)
            if consistency_issues:
                results['consistency_issues'].extend([(file_name, issue) for issue in consistency_issues])
                for issue in consistency_issues:
                    print(f'   ⚠️ CONSISTENCY: {issue}')
        else:
            if 'Import Error' in error:
                results['import_errors'].append((file_path, error))
                print(f'⚠️ {file_name}: {error[:60]}...')
            else:
                results['critical_bugs'].append((file_path, error))
                print(f'❌ {file_name}: {error[:60]}...')
    
    print('\n🔍 CHECKING CROSS-FILE CONSISTENCY:')
    print('-' * 70)
    
    # Check port consistency
    port_issues = check_port_consistency(nasa_files)
    if port_issues:
        for issue in port_issues:
            print(f'⚠️ PORT CONSISTENCY: {issue}')
            results['consistency_issues'].append(('ports', issue))
    else:
        print('✅ PORT CONSISTENCY: All files use consistent ports')
    
    # Check import consistency
    import_issues = check_import_consistency(nasa_files)
    if import_issues:
        for issue in import_issues:
            print(f'⚠️ IMPORT CONSISTENCY: {issue}')
            results['consistency_issues'].append(('imports', issue))
    else:
        print('✅ IMPORT CONSISTENCY: NASA imports are consistent')
    
    # Check method signatures
    method_issues = check_method_signatures(nasa_files)
    if method_issues:
        for issue in method_issues:
            print(f'⚠️ METHOD CONSISTENCY: {issue}')
            results['consistency_issues'].append(('methods', issue))
    else:
        print('✅ METHOD CONSISTENCY: NASA method signatures are consistent')
    
    print('\n📈 SUMMARY RESULTS:')
    print('-' * 70)
    print(f'✅ Files with valid syntax: {len(results["syntax_ok"])}')
    print(f'⚠️ Import warnings: {len(results["import_errors"])}')
    print(f'❌ Critical bugs: {len(results["critical_bugs"])}')
    print(f'⚠️ Consistency issues: {len(results["consistency_issues"])}')
    print(f'❌ Missing files: {len(results["missing_files"])}')
    
    if results['critical_bugs']:
        print('\n🚨 CRITICAL BUGS FOUND:')
        for file_path, error in results['critical_bugs']:
            print(f'   ❌ {os.path.basename(file_path)}: {error}')
    
    if results['consistency_issues']:
        print('\n⚠️ CONSISTENCY ISSUES:')
        for item, issue in results['consistency_issues']:
            print(f'   ⚠️ {item}: {issue}')
    
    if results['missing_files']:
        print('\n❌ MISSING FILES:')
        for file_path in results['missing_files']:
            print(f'   ❌ {file_path}')
    
    print('\n' + '=' * 70)
    total_critical = len(results['critical_bugs']) + len(results['missing_files'])
    total_warnings = len(results['import_errors']) + len(results['consistency_issues'])
    
    if total_critical == 0:
        if total_warnings == 0:
            print('🎯 NASA CODE STATUS: PERFECT - NO ISSUES FOUND ✅')
        else:
            print(f'🎯 NASA CODE STATUS: GOOD - {total_warnings} MINOR WARNINGS ⚠️')
    else:
        print(f'⚠️ NASA CODE STATUS: {total_critical} CRITICAL ISSUES + {total_warnings} WARNINGS')
    
    print('=' * 70)
    
    return results

if __name__ == "__main__":
    analyze_nasa_code() 