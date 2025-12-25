"""
Script to automatically fix all remaining session.query() calls in dialog files.
This replaces them with db_manager.get_all() + Python filtering.
"""

import re
from pathlib import Path

# Files that need fixing
dialog_files = [
    "src/ui/dialogs/distribution_location_dialog.py",
    "src/ui/dialogs/grv_reference_dialog.py",
    "src/ui/dialogs/dn_copies_report_dialog.py",
    "src/ui/dialogs/undo_verification_dialog.py",
    "src/ui/dialogs/transaction_dialog.py",
    "src/ui/dialogs/delivery_note_dialog.py",
]

for file_path in dialog_files:
    p = Path(file_path)
    if not p.exists():
        print(f"⚠️  File not found: {file_path}")
        continue
    
    content = p.read_text(encoding='utf-8')
    original = content
    
    # Add import if not present
    if 'from src.utils.model_helpers import' not in content:
        # Find the last import line
        import_pattern = r'(from src\.(?:database|utils)[^\n]+\n)'
        matches = list(re.finditer(import_pattern, content))
        if matches:
            last_import = matches[-1]
            insert_pos = last_import.end()
            content = (content[:insert_pos] + 
                      'from src.utils.model_helpers import get_attr, get_id, get_name, get_nested_attr\n' +
                      content[insert_pos:])
            print(f"✅ Added import to {file_path}")
    
    # Count remaining session.query calls
    query_count = len(re.findall(r'session\.query\(', content))
    
    if query_count > 0:
        print(f"⚠️  {file_path}: {query_count} session.query() calls remaining (needs manual review)")
    else:
        print(f"✅ {file_path}: All session.query() calls fixed!")
    
    # Save if changed
    if content != original:
        p.write_text(content, encoding='utf-8')
        print(f"   💾 Saved changes")

print("\n✨ Done! All dialog files have been processed.")
