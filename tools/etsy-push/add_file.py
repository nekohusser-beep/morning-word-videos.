#!/usr/bin/env python3
"""Encrypt a product file (PDF, image) into tools/etsy-push/files/<name>.enc so jobs can use it.
  VAULT_KEY=$(cat ../kingdom-brain/tools/etsy/VAULT_KEY.txt) python3 tools/etsy-push/add_file.py <path> [<path>...]
The key lives only in private kingdom-brain (tools/etsy/VAULT_KEY.txt) and the VAULT_KEY Actions secret."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etsy_push import fernet, FILES
os.makedirs(FILES, exist_ok=True)
for p in sys.argv[1:]:
    out = os.path.join(FILES, os.path.basename(p) + ".enc")
    open(out, "wb").write(fernet().encrypt(open(p, "rb").read()))
    print(os.path.relpath(out))
