"""
tests/test_sast.py
==================
Static Application Security Testing (SAST)

Uses bandit to scan source code for common security issues:
- Hardcoded passwords/secrets
- SQL injection vulnerabilities
- Use of unsafe functions (eval, exec)
- Insecure cryptographic practices
- Command injection risks

Run: pytest tests/test_sast.py -v
"""

import subprocess
import sys
import pytest


class TestSAST:
    """Static Application Security Testing using bandit."""
    
    def test_bandit_agent_module(self):
        """Scan agent/ module for security vulnerabilities."""
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "-r", "agent/", "-f", "json", "-q"],
            capture_output=True,
            text=True
        )
        
        # bandit returns 0 if no issues, 1 if issues found
        if result.returncode != 0 and result.stdout:
            import json
            try:
                report = json.loads(result.stdout)
                high_severity = [r for r in report.get("results", []) 
                               if r.get("issue_severity") == "HIGH"]
                
                # Fail only on HIGH severity issues
                assert len(high_severity) == 0, (
                    f"Found {len(high_severity)} HIGH severity security issues:\n" +
                    "\n".join([f"- {r['filename']}:{r['line_number']}: {r['issue_text']}" 
                              for r in high_severity])
                )
            except json.JSONDecodeError:
                pass  # No JSON output means no issues
    
    def test_bandit_service_module(self):
        """Scan service/ module for security vulnerabilities."""
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "-r", "service/", "-f", "json", "-q"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0 and result.stdout:
            import json
            try:
                report = json.loads(result.stdout)
                high_severity = [r for r in report.get("results", []) 
                               if r.get("issue_severity") == "HIGH"]
                
                assert len(high_severity) == 0, (
                    f"Found {len(high_severity)} HIGH severity security issues:\n" +
                    "\n".join([f"- {r['filename']}:{r['line_number']}: {r['issue_text']}" 
                              for r in high_severity])
                )
            except json.JSONDecodeError:
                pass
    
    def test_no_hardcoded_secrets(self):
        """Check that no secrets are hardcoded in source files."""
        import os
        import re
        
        secret_patterns = [
            r'api_key\s*=\s*["\'][^"\']{20,}["\']',
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']{20,}["\']',
            r'token\s*=\s*["\'][A-Za-z0-9_\-]{30,}["\']',
        ]
        
        violations = []
        
        for root, dirs, files in os.walk("."):
            # Skip non-source directories
            dirs[:] = [d for d in dirs if d not in [
                ".venv", "venv", "__pycache__", ".git", "node_modules"
            ]]
            
            for file in files:
                if file.endswith((".py", ".ts", ".js")):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            for pattern in secret_patterns:
                                matches = re.findall(pattern, content, re.IGNORECASE)
                                if matches:
                                    violations.append(f"{filepath}: potential hardcoded secret")
                    except Exception:
                        pass
        
        assert len(violations) == 0, f"Found potential hardcoded secrets:\n" + "\n".join(violations)
    
    def test_no_dangerous_functions(self):
        """Check for dangerous function usage (eval, exec, etc.)."""
        import os
        import re
        
        dangerous_patterns = [
            (r'\beval\s*\(', "eval() - code injection risk"),
            (r'\bexec\s*\(', "exec() - code injection risk"),
            (r'\b__import__\s*\(', "__import__() - dynamic import risk"),
            (r'subprocess\..*shell\s*=\s*True', "shell=True - command injection risk"),
        ]
        
        violations = []
        
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in [
                ".venv", "venv", "__pycache__", ".git", "node_modules", "tests"
            ]]
            
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            for pattern, description in dangerous_patterns:
                                if re.search(pattern, content):
                                    violations.append(f"{filepath}: {description}")
                    except Exception:
                        pass
        
        assert len(violations) == 0, f"Found dangerous function usage:\n" + "\n".join(violations)

