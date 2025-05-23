import hashlib

def md5_hash(text: str) -> str:
    data = text.encode('utf-8')
    md5 = hashlib.md5()
    md5.update(data)
    return md5.hexdigest()

plain = "password"
digest = md5_hash(plain)
print(f"원문: {plain}")
print(f"MD5:  {digest}")