
import hashlib
import hmac

secret_key = b"chainpatrol_secret_key"

# Original message
original_message = b"ChainPatrol Block 1"

# Modified message (simulating tampering)
tampered_message = b"ChainPatrol Block 2"

# Generate MAC for original message
original_mac = hmac.new(
    secret_key,
    original_message,
    hashlib.sha256
).hexdigest()

# Generate MAC for received message
received_mac = hmac.new(
    secret_key,
    tampered_message,
    hashlib.sha256
).hexdigest()

# Verify integrity
if hmac.compare_digest(original_mac, received_mac):
    print("Message is authentic. No tampering detected.")
else:
    print("WARNING: Message tampering detected!")

print("\nOriginal MAC:", original_mac)
print("Received MAC:", received_mac)
