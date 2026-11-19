
import hashlib
import hmac

# ChainPatrol configuration
SECRET_KEY = b"chainpatrol_secret_key"

BLOCK_NUM = 1
FLOW_ID = 101

# Generate 33 actual packet payloads
PACKET_COUNT = 33

PACKET_PAYLOADS = [
    f"ChainPatrol data packet {i}".encode("utf-8")
    for i in range(1, PACKET_COUNT + 1)
]


def build_block_data(payloads):
    """
    Build authenticated block data using:
    Packet number + payload length + actual payload.
    """

    block_data = b""

    for packet_number, payload in enumerate(payloads, start=1):

        block_data += (
            packet_number.to_bytes(2, "big")
            + len(payload).to_bytes(2, "big")
            + payload
        )

    return block_data


# Original authenticated block data
BLOCK_DATA = build_block_data(PACKET_PAYLOADS)


def generate_virtual_trailer(block_data=BLOCK_DATA):

    authenticated_data = (
        BLOCK_NUM.to_bytes(1, "big")
        + FLOW_ID.to_bytes(1, "big")
        + block_data
    )

    # Generate HMAC-SHA256
    full_mac = hmac.new(
        SECRET_KEY,
        authenticated_data,
        hashlib.sha256
    ).digest()

    # Truncate MAC to 16 bits
    truncated_mac = full_mac[:2]

    # Convert fields into binary
    block_num_bits = format(BLOCK_NUM, "08b")
    flow_id_bits = format(FLOW_ID, "08b")

    mac_bits = format(
        int.from_bytes(truncated_mac, "big"),
        "016b"
    )

    # Combine all three fields
    vt_bits = (
        block_num_bits
        + flow_id_bits
        + mac_bits
    )

    return vt_bits, truncated_mac.hex()


if __name__ == "__main__":

    vt_bits, mac_hex = generate_virtual_trailer()

    print("====================================")
    print("     CHAINPATROL VIRTUAL TRAILER")
    print("====================================")

    print(f"BlockNum: {BLOCK_NUM}")
    print(f"FlowID: {FLOW_ID}")
    print(f"Authenticated packets: {PACKET_COUNT}")
    print(f"MAC: {mac_hex}")

    print(f"\nVirtual Trailer: {vt_bits}")
    print(f"Total VT length: {len(vt_bits)} bits")

    print("====================================")
