import hashlib

text = "Hello"
data = text.encode("utf-8")

fingerprint = hashlib.sha256(data).hexdigest()

print(data)
print(fingerprint)
print(len(fingerprint))
