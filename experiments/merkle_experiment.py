
import hashlib


def calculate_hash(data):
    """Calculate SHA-256 hash of input data."""
    return hashlib.sha256(data).hexdigest()


# Four example blocks belonging to one flow
blocks = [
    b"Block 1: Packet 1, Packet 2, Packet 3",
    #b"Block 2: Packet 4, Packet 5, Packet 6",
    b"Block 2: Packet 4, Packet 5 MODIFIED, Packet 6",
    b"Block 3: Packet 7, Packet 8, Packet 9",
    b"Block 4: Packet 10, Packet 11, Packet 12"
]

# Step 1: Calculate leaf hashes
leaf_hashes = []

for block in blocks:
    leaf_hashes.append(calculate_hash(block))

print("LEAF HASHES:")

for i, leaf in enumerate(leaf_hashes):
    print(f"Block {i + 1}: {leaf}")


# Step 2: Build the Merkle Tree
current_level = leaf_hashes

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


# Step 3: Display Merkle Root
merkle_root = current_level[0]

print("\nMERKLE ROOT:")
print(merkle_root)
