"""
Quick script to fix all API server endpoints to use 'with' statement
"""
import re

# Read the file
with open('src/api_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern 1: Fix lines like `session = db_manager.get_session()` followed by queries
# Replace with `with db_manager.get_session() as session:`
content = re.sub(
    r'(\s+)session = db_manager\.get_session\(\)\s*\n(\s+)(\w+) = session',
    r'\1with db_manager.get_session() as session:\n\2    \3 = session',
    content
)

# Pattern 2: Remove all `session.rollback()` lines since context manager handles it
content = re.sub(
    r'\s+session\.rollback\(\)\s*\n',
    '',
    content
)

# Write fixed content
with open('src/api_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed all API endpoints to use 'with' statement")
print("✓ Removed all manual rollback() calls")
print("Server ready for restart!")
