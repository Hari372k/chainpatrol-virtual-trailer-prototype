
import hashlib
import hmac


# Function to calculate SHA-256 hash
def calculate_hash(data):
    return hashlib.sha256(data).hexdigest()


# Function to calculate Merkle Root
def calculate_merkle_root(blocks):

    # Generate leaf hashes
    current_level = []

    for block in blocks:
        current_level.append(calculate_hash(block))

    # Build the Merkle Tree
    while len(current_level) > 1:

        next_level = []

        for i in range(0, len(current_level), 2):

            left = current_level[i]

            if i + 1 < len(current_level):
                right = current_level[i + 1]
            else:
                right = left

            combined = (left + right).encode("utf-8")

            parent_hash = calculate_hash(combined)

            next_level.append(parent_hash)

        current_level = next_level

    return current_level[0]


# Original SuperBlock
original_blocks = [
    b"Block 1: Packet 1, Packet 2, Packet 3",
    b"Block 2: Packet 4, Packet 5, Packet 6",
    b"Block 3: Packet 7, Packet 8, Packet 9",
    b"Block 4: Packet 10, Packet 11, Packet 12"
]


# Simulate received SuperBlock
received_blocks = original_blocks.copy()

# Attacker modifies Packet 5
received_blocks[1] = (
    b"Block 2: Packet 4, Packet 5 MODIFIED, Packet 6"
)


# Calculate both Merkle Roots
expected_root = calculate_merkle_root(original_blocks)

received_root = calculate_merkle_root(received_blocks)


# Compare the Merkle Roots
print("EXPECTED MERKLE ROOT:")
print(expected_root)

print("\nRECEIVED MERKLE ROOT:")
print(received_root)

print("\nATTACK DETECTION RESULT:")

if hmac.compare_digest(expected_root, received_root):
    print("No tampering detected. SuperBlock is intact.")
else:
    print("WARNING: Tampering detected!")
    print("SuperBlock integrity verification FAILED.")
