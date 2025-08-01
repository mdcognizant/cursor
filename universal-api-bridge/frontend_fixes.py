#!/usr/bin/env python3
"""
Comprehensive Frontend Fixes for Universal API Bridge

This script validates and fixes all HTML frontend interfaces:
1. HTML validation and syntax issues
2. JavaScript error handling and security
3. CSS issues and responsiveness
4. Accessibility improvements
5. Performance optimizations
6. Security vulnerabilities (XSS, etc.)
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class HTMLIssue:
    """Represents an HTML issue found."""
    file: str
    line_number: int
    issue_type: str
    description: str
    severity: str
    fix_suggestion: str


class FrontendValidator:
    """Validates and fixes frontend HTML/CSS/JS issues."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.html_files = list(self.project_root.glob("*.html"))
        self.issues: List[HTMLIssue] = []
    
    def validate_html_structure(self) -> List[HTMLIssue]:
        """Validate basic HTML structure and syntax."""
        issues = []
        
        required_elements = [
            ("<!DOCTYPE html>", "Missing DOCTYPE declaration"),
            ("<html", "Missing html element"),
            ("<head>", "Missing head element"),
            ("<title>", "Missing title element"),
            ("<meta charset=", "Missing charset meta tag"),
            ("<meta name=\"viewport\"", "Missing viewport meta tag")
        ]
        
        for html_file in self.html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                # Check required elements
                for element, description in required_elements:
                    if element not in content:
                        issues.append(HTMLIssue(
                            file=str(html_file.name),
                            line_number=1,
                            issue_type="HTML_STRUCTURE",
                            description=description,
                            severity="HIGH",
                            fix_suggestion=f"Add {element} to the document"
                        ))
                
                # Check for unclosed tags
                tag_pattern = r'<(\w+)(?:\s[^>]*)?(?<!/)>'
                closing_tag_pattern = r'</(\w+)>'
                
                open_tags = []
                for i, line in enumerate(lines, 1):
                    # Find opening tags
                    for match in re.finditer(tag_pattern, line):
                        tag = match.group(1).lower()
                        if tag not in ['img', 'br', 'hr', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr']:
                            open_tags.append((tag, i))
                    
                    # Find closing tags
                    for match in re.finditer(closing_tag_pattern, line):
                        tag = match.group(1).lower()
                        if open_tags and open_tags[-1][0] == tag:
                            open_tags.pop()
                        else:
                            issues.append(HTMLIssue(
                                file=str(html_file.name),
                                line_number=i,
                                issue_type="HTML_SYNTAX",
                                description=f"Mismatched closing tag: </{tag}>",
                                severity="MEDIUM",
                                fix_suggestion="Check tag nesting and ensure proper closing"
                            ))
                
                # Check for remaining unclosed tags
                for tag, line_num in open_tags:
                    issues.append(HTMLIssue(
                        file=str(html_file.name),
                        line_number=line_num,
                        issue_type="HTML_SYNTAX",
                        description=f"Unclosed tag: <{tag}>",
                        severity="MEDIUM",
                        fix_suggestion=f"Add closing tag </{tag}>"
                    ))
                    
            except Exception as e:
                logger.warning(f"Could not validate {html_file}: {e}")
        
        return issues
    
    def validate_javascript_security(self) -> List[HTMLIssue]:
        """Check for JavaScript security issues."""
        issues = []
        
        security_patterns = [
            (r'innerHTML\s*=', "innerHTML assignment", "Use textContent or proper sanitization"),
            (r'document\.write\s*\(', "document.write usage", "Use safer DOM manipulation methods"),
            (r'eval\s*\(', "eval() usage", "Avoid eval() - use JSON.parse() or other safe alternatives"),
            (r'setTimeout\s*\(\s*["\']', "setTimeout with string", "Use function references instead of strings"),
            (r'setInterval\s*\(\s*["\']', "setInterval with string", "Use function references instead of strings"),
            (r'window\.location\s*=\s*[^;]+\+', "Dynamic location assignment", "Validate and sanitize URLs before assignment"),
        ]
        
        for html_file in self.html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern, issue_desc, fix in security_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            issues.append(HTMLIssue(
                                file=str(html_file.name),
                                line_number=i,
                                issue_type="SECURITY",
                                description=f"Security issue: {issue_desc}",
                                severity="HIGH",
                                fix_suggestion=fix
                            ))
                            
            except Exception as e:
                logger.warning(f"Could not check security in {html_file}: {e}")
        
        return issues
    
    def validate_accessibility(self) -> List[HTMLIssue]:
        """Check for accessibility issues."""
        issues = []
        
        for html_file in self.html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Check for missing alt attributes on images
                    if '<img' in line and 'alt=' not in line:
                        issues.append(HTMLIssue(
                            file=str(html_file.name),
                            line_number=i,
                            issue_type="ACCESSIBILITY",
                            description="Image missing alt attribute",
                            severity="MEDIUM",
                            fix_suggestion="Add alt attribute for screen readers"
                        ))
                    
                    # Check for missing labels on form inputs
                    if '<input' in line and 'type=' in line:
                        if 'aria-label=' not in line and 'id=' not in line:
                            issues.append(HTMLIssue(
                                file=str(html_file.name),
                                line_number=i,
                                issue_type="ACCESSIBILITY",
                                description="Form input missing label or aria-label",
                                severity="MEDIUM",
                                fix_suggestion="Add label element or aria-label attribute"
                            ))
                    
                    # Check for low contrast issues (basic check)
                    if 'color:' in line and '#' in line:
                        # Basic check for potentially low contrast colors
                        color_match = re.search(r'color:\s*#([a-fA-F0-9]{3,6})', line)
                        if color_match:
                            color_hex = color_match.group(1)
                            if len(color_hex) == 3:
                                color_hex = ''.join([c*2 for c in color_hex])
                            
                            # Simple brightness check
                            if len(color_hex) == 6:
                                r = int(color_hex[0:2], 16)
                                g = int(color_hex[2:4], 16)
                                b = int(color_hex[4:6], 16)
                                brightness = (r * 299 + g * 587 + b * 114) / 1000
                                
                                if brightness < 50:  # Very dark colors
                                    issues.append(HTMLIssue(
                                        file=str(html_file.name),
                                        line_number=i,
                                        issue_type="ACCESSIBILITY",
                                        description="Potentially low contrast color",
                                        severity="LOW",
                                        fix_suggestion="Check color contrast ratio (WCAG 2.1 AA: 4.5:1)"
                                    ))
                        
            except Exception as e:
                logger.warning(f"Could not check accessibility in {html_file}: {e}")
        
        return issues
    
    def validate_performance(self) -> List[HTMLIssue]:
        """Check for performance issues."""
        issues = []
        
        for html_file in self.html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                # Check file size
                file_size = len(content.encode('utf-8'))
                if file_size > 500 * 1024:  # 500KB
                    issues.append(HTMLIssue(
                        file=str(html_file.name),
                        line_number=1,
                        issue_type="PERFORMANCE",
                        description=f"Large file size: {file_size / 1024:.1f}KB",
                        severity="MEDIUM",
                        fix_suggestion="Consider splitting into smaller files or optimizing content"
                    ))
                
                # Check for inline styles (should be in CSS)
                inline_style_count = content.count('style=')
                if inline_style_count > 10:
                    issues.append(HTMLIssue(
                        file=str(html_file.name),
                        line_number=1,
                        issue_type="PERFORMANCE",
                        description=f"Many inline styles: {inline_style_count}",
                        severity="LOW",
                        fix_suggestion="Move inline styles to CSS classes"
                    ))
                
                # Check for missing compression attributes
                for i, line in enumerate(lines, 1):
                    if '<script' in line and 'src=' in line:
                        if 'defer' not in line and 'async' not in line:
                            issues.append(HTMLIssue(
                                file=str(html_file.name),
                                line_number=i,
                                issue_type="PERFORMANCE",
                                description="Script without defer or async",
                                severity="LOW",
                                fix_suggestion="Add defer or async attribute to external scripts"
                            ))
                            
            except Exception as e:
                logger.warning(f"Could not check performance in {html_file}: {e}")
        
        return issues
    
    def validate_modern_standards(self) -> List[HTMLIssue]:
        """Check compliance with modern web standards."""
        issues = []
        
        for html_file in self.html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                
                # Check for deprecated elements
                deprecated_elements = [
                    ('<center>', "Use CSS text-align instead"),
                    ('<font', "Use CSS font properties instead"),
                    ('<table', "Consider CSS Grid or Flexbox for layout"),
                    ('target="_blank"', "Add rel=\"noopener noreferrer\" for security")
                ]
                
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    for element, suggestion in deprecated_elements:
                        if element in line.lower():
                            if element == 'target="_blank"' and 'rel=' not in line:
                                issues.append(HTMLIssue(
                                    file=str(html_file.name),
                                    line_number=i,
                                    issue_type="MODERN_STANDARDS",
                                    description="target=\"_blank\" without rel attribute",
                                    severity="MEDIUM",
                                    fix_suggestion=suggestion
                                ))
                            elif element != 'target="_blank"':
                                issues.append(HTMLIssue(
                                    file=str(html_file.name),
                                    line_number=i,
                                    issue_type="MODERN_STANDARDS",
                                    description=f"Deprecated element: {element}",
                                    severity="LOW",
                                    fix_suggestion=suggestion
                                ))
                
                # Check for responsive design
                if 'viewport' not in content:
                    issues.append(HTMLIssue(
                        file=str(html_file.name),
                        line_number=1,
                        issue_type="MODERN_STANDARDS",
                        description="Missing responsive viewport meta tag",
                        severity="MEDIUM",
                        fix_suggestion="Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"
                    ))
                
                # Check for CSS Grid/Flexbox usage
                if 'display: grid' not in content and 'display: flex' not in content:
                    if '<table' in content and 'role="presentation"' not in content:
                        issues.append(HTMLIssue(
                            file=str(html_file.name),
                            line_number=1,
                            issue_type="MODERN_STANDARDS",
                            description="Consider modern layout methods (CSS Grid/Flexbox)",
                            severity="LOW",
                            fix_suggestion="Use CSS Grid or Flexbox for layout instead of tables"
                        ))
                        
            except Exception as e:
                logger.warning(f"Could not check standards in {html_file}: {e}")
        
        return issues
    
    def run_validation(self) -> Dict[str, List[HTMLIssue]]:
        """Run all frontend validations."""
        logger.info("🔍 Starting comprehensive frontend validation...")
        
        results = {
            "html_structure": self.validate_html_structure(),
            "javascript_security": self.validate_javascript_security(),
            "accessibility": self.validate_accessibility(),
            "performance": self.validate_performance(),
            "modern_standards": self.validate_modern_standards()
        }
        
        # Store all issues
        self.issues = []
        for issues_list in results.values():
            self.issues.extend(issues_list)
        
        # Count issues by severity
        high_count = sum(1 for issue in self.issues if issue.severity == "HIGH")
        medium_count = sum(1 for issue in self.issues if issue.severity == "MEDIUM")
        low_count = sum(1 for issue in self.issues if issue.severity == "LOW")
        
        logger.info(f"✅ Frontend validation complete:")
        logger.info(f"  - High priority: {high_count} issues")
        logger.info(f"  - Medium priority: {medium_count} issues")
        logger.info(f"  - Low priority: {low_count} issues")
        logger.info(f"  - Total: {len(self.issues)} issues")
        
        return results
    
    def generate_fix_report(self, results: Dict[str, List[HTMLIssue]]) -> str:
        """Generate a detailed frontend fixes report."""
        report = "# Universal API Bridge - Frontend Issues Report\n\n"
        
        # Summary
        high_issues = [issue for issue in self.issues if issue.severity == "HIGH"]
        medium_issues = [issue for issue in self.issues if issue.severity == "MEDIUM"]
        low_issues = [issue for issue in self.issues if issue.severity == "LOW"]
        
        report += f"## Summary\n"
        report += f"- **Total Files Checked**: {len(self.html_files)}\n"
        report += f"- **High Priority Issues**: {len(high_issues)}\n"
        report += f"- **Medium Priority Issues**: {len(medium_issues)}\n"
        report += f"- **Low Priority Issues**: {len(low_issues)}\n\n"
        
        # Group issues by file
        issues_by_file = {}
        for issue in self.issues:
            if issue.file not in issues_by_file:
                issues_by_file[issue.file] = []
            issues_by_file[issue.file].append(issue)
        
        # High priority issues first
        if high_issues:
            report += "## 🚨 High Priority Issues (Fix Immediately)\n\n"
            for issue in high_issues:
                report += f"### {issue.file}:{issue.line_number}\n"
                report += f"**Type**: {issue.issue_type}\n"
                report += f"**Issue**: {issue.description}\n"
                report += f"**Fix**: {issue.fix_suggestion}\n\n"
        
        # Medium priority issues
        if medium_issues:
            report += "## ⚠️ Medium Priority Issues\n\n"
            for issue in medium_issues:
                report += f"### {issue.file}:{issue.line_number}\n"
                report += f"**Type**: {issue.issue_type}\n"
                report += f"**Issue**: {issue.description}\n"
                report += f"**Fix**: {issue.fix_suggestion}\n\n"
        
        # Add common fixes section
        report += "## 🔧 Common Fixes\n\n"
        
        report += "### Security Fixes\n"
        report += "```javascript\n"
        report += "// Replace innerHTML with safer alternatives\n"
        report += "// Bad:\n"
        report += "element.innerHTML = userInput;\n\n"
        report += "// Good:\n"
        report += "element.textContent = userInput;\n"
        report += "// Or use DOMPurify for HTML content\n"
        report += "```\n\n"
        
        report += "### Accessibility Fixes\n"
        report += "```html\n"
        report += "<!-- Add alt attributes to images -->\n"
        report += "<img src=\"image.jpg\" alt=\"Descriptive text\">\n\n"
        report += "<!-- Add labels to form inputs -->\n"
        report += "<label for=\"email\">Email:</label>\n"
        report += "<input type=\"email\" id=\"email\" name=\"email\">\n"
        report += "```\n\n"
        
        report += "### Performance Fixes\n"
        report += "```html\n"
        report += "<!-- Add defer to external scripts -->\n"
        report += "<script src=\"script.js\" defer></script>\n\n"
        report += "<!-- Add proper meta tags -->\n"
        report += "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        report += "```\n\n"
        
        return report
    
    def auto_fix_issues(self) -> int:
        """Automatically fix some common issues where possible."""
        fixes_applied = 0
        
        for html_file in self.html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                original_content = content
                
                # Fix missing viewport meta tag
                if '<meta name="viewport"' not in content and '<head>' in content:
                    viewport_tag = '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                    content = content.replace('<head>\n', f'<head>\n{viewport_tag}')
                    fixes_applied += 1
                
                # Fix target="_blank" without rel
                content = re.sub(
                    r'target="_blank"(?!\s+rel=)', 
                    'target="_blank" rel="noopener noreferrer"',
                    content
                )
                
                # Save if changes were made
                if content != original_content:
                    html_file.write_text(content, encoding='utf-8')
                    logger.info(f"✅ Applied automatic fixes to {html_file.name}")
                    
            except Exception as e:
                logger.warning(f"Could not auto-fix {html_file}: {e}")
        
        return fixes_applied


def main():
    """Run frontend validation and fixes."""
    validator = FrontendValidator(".")
    
    # Run validation
    results = validator.run_validation()
    
    # Generate report
    report = validator.generate_fix_report(results)
    report_file = Path("FRONTEND_ISSUES_REPORT.md")
    report_file.write_text(report, encoding='utf-8')
    
    logger.info(f"📄 Frontend report saved to: {report_file}")
    
    # Apply automatic fixes
    fixes_applied = validator.auto_fix_issues()
    if fixes_applied > 0:
        logger.info(f"🔧 Applied {fixes_applied} automatic fixes")
    
    # Summary
    total_issues = len(validator.issues)
    high_priority = sum(1 for issue in validator.issues if issue.severity == "HIGH")
    
    if total_issues == 0:
        logger.info("🎉 No frontend issues found!")
    else:
        logger.warning(f"⚠️ Found {total_issues} frontend issues ({high_priority} high priority)")
    
    return total_issues


if __name__ == "__main__":
    import sys
    sys.exit(main()) 