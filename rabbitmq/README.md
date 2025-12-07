```bash
python -c "import hashlib, base64, os; salt = os.urandom(4); password = b'admin'; hash = hashlib.sha256(salt + password).digest(); print(base64.b64encode(salt + hash).decode())"
```