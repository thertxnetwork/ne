"""
Unit tests for telegram_webapp.py

This test file validates the structure and basic functionality
of the TelegramWebAppLauncher class without requiring actual
Telegram API credentials.
"""

import ast
import os
import sys


def test_file_syntax():
    """Test that the main script has valid Python syntax."""
    print("Testing file syntax...")
    try:
        with open('telegram_webapp.py', 'r') as f:
            code = f.read()
        ast.parse(code)
        print("✅ telegram_webapp.py has valid syntax")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in telegram_webapp.py: {e}")
        return False


def test_example_syntax():
    """Test that the example file has valid Python syntax."""
    print("Testing example file syntax...")
    try:
        with open('example_usage.py', 'r') as f:
            code = f.read()
        ast.parse(code)
        print("✅ example_usage.py has valid syntax")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in example_usage.py: {e}")
        return False


def test_class_structure():
    """Test that the TelegramWebAppLauncher class has expected methods."""
    print("Testing class structure...")
    with open('telegram_webapp.py', 'r') as f:
        code = f.read()
    
    tree = ast.parse(code)
    
    # Find the TelegramWebAppLauncher class
    class_found = False
    required_methods = {
        'connect', 'disconnect', 'get_web_app_url', 
        'generate_init_data', 'fetch_homepage', 'get_bot_info'
    }
    found_methods = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'TelegramWebAppLauncher':
            class_found = True
            for item in node.body:
                if isinstance(item, ast.AsyncFunctionDef) or isinstance(item, ast.FunctionDef):
                    found_methods.add(item.name)
    
    if not class_found:
        print("❌ TelegramWebAppLauncher class not found")
        return False
    
    missing_methods = required_methods - found_methods
    if missing_methods:
        print(f"❌ Missing methods: {missing_methods}")
        return False
    
    print(f"✅ TelegramWebAppLauncher class has all required methods: {required_methods}")
    return True


def test_requirements_file():
    """Test that requirements.txt exists and has necessary dependencies."""
    print("Testing requirements.txt...")
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        required_packages = ['telethon', 'requests', 'python-dotenv']
        missing = []
        
        for package in required_packages:
            if package not in requirements.lower():
                missing.append(package)
        
        if missing:
            print(f"❌ Missing packages in requirements.txt: {missing}")
            return False
        
        print(f"✅ requirements.txt contains all necessary packages: {required_packages}")
        return True
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False


def test_gitignore():
    """Test that .gitignore exists and contains necessary patterns."""
    print("Testing .gitignore...")
    try:
        with open('.gitignore', 'r') as f:
            gitignore = f.read()
        
        required_patterns = ['*.session', '.env', '__pycache__', 'venv']
        missing = []
        
        for pattern in required_patterns:
            if pattern not in gitignore:
                missing.append(pattern)
        
        if missing:
            print(f"❌ Missing patterns in .gitignore: {missing}")
            return False
        
        print(f"✅ .gitignore contains all necessary patterns")
        return True
    except FileNotFoundError:
        print("❌ .gitignore not found")
        return False


def test_env_example():
    """Test that .env.example exists and has necessary variables."""
    print("Testing .env.example...")
    try:
        with open('.env.example', 'r') as f:
            env_example = f.read()
        
        required_vars = ['API_ID', 'API_HASH', 'PHONE']
        missing = []
        
        for var in required_vars:
            if var not in env_example:
                missing.append(var)
        
        if missing:
            print(f"❌ Missing variables in .env.example: {missing}")
            return False
        
        print(f"✅ .env.example contains all necessary variables: {required_vars}")
        return True
    except FileNotFoundError:
        print("❌ .env.example not found")
        return False


def test_documentation():
    """Test that README.md exists and has sufficient content."""
    print("Testing README.md...")
    try:
        with open('README.md', 'r') as f:
            readme = f.read()
        
        required_sections = ['Installation', 'Usage', 'Features', 'Prerequisites']
        missing = []
        
        for section in required_sections:
            if section.lower() not in readme.lower():
                missing.append(section)
        
        if missing:
            print(f"⚠️  Possibly missing sections in README.md: {missing}")
        
        if len(readme) < 500:
            print("⚠️  README.md seems too short")
            return False
        
        print(f"✅ README.md has substantial documentation ({len(readme)} characters)")
        return True
    except FileNotFoundError:
        print("❌ README.md not found")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Running Tests for Telegram Web App Launcher")
    print("="*60)
    print()
    
    tests = [
        test_file_syntax,
        test_example_syntax,
        test_class_structure,
        test_requirements_file,
        test_gitignore,
        test_env_example,
        test_documentation
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print()
    
    print("="*60)
    print("Test Summary")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
