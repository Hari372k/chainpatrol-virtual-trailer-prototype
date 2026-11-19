
import time
import socket
import hmac
import argparse
import csv
from pathlib import Path

from virtual_trailer import (
    BLOCK_NUM,
    FLOW_ID,
    PACKET_COUNT,
    build_block_data,
    generate_virtual_trailer
)

# ==========================================
# COMMAND-LINE CONFIGURATION
# ==========================================

parser = argparse.ArgumentParser(
    description="ChainPatrol VT Receiver"
)

parser.add_argument(
    "--mode",
    choices=["normal", "watermark"],
    default="watermark"
)

args = parser.parse_args()

# ==========================================
# RECEIVER CONFIGURATION
# ==========================================

HOST = "127.0.0.1"
PORT = 5005

BASELINE_IPD_MS = 50
EXPECTED_BITS = 32

END_MARKER = b"__CHAINPATROL_END__"

receiver = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)

receiver.bind((HOST, PORT))
receiver.settimeout(300)

print("====================================")
print("     CHAINPATROL VT RECEIVER")
print("====================================")

print(f"Listening on {HOST}:{PORT}")
print(f"Mode: {args.mode.upper()}")

# ==========================================
# INITIALIZE COLLECTIONS
# ==========================================

previous_timestamp = None

received_packets = []
payloads_by_number = {}

decoded_bits = []
ipds = []
log_rows = []

end_received = False

# ==========================================
# RECEIVE PACKETS
# ==========================================

while True:

    try:
        data, sender_address = receiver.recvfrom(2048)

    except socket.timeout:
        print("\nERROR: Transmission timed out.")
        break

    if data == END_MARKER:
        end_received = True
        print("\nEnd-of-transmission marker received.")
        break

    current_timestamp = time.monotonic_ns()

    try:
        number_bytes, payload = data.split(b"|", 1)
        packet_number = int(
            number_bytes.decode("utf-8")
        )

    except (ValueError, UnicodeDecodeError):
        print("Malformed packet received.")
        continue

    received_packets.append(packet_number)

    if packet_number not in payloads_by_number:
        payloads_by_number[packet_number] = payload

    message = payload.decode(
        "utf-8",
        errors="replace"
    )

    print(f"\nReceived packet {packet_number}: {message}")

    measured_ipd = None
    decoded_bit = ""

    if previous_timestamp is not None:

        measured_ipd = (
            current_timestamp - previous_timestamp
        ) / 1_000_000

        ipds.append(measured_ipd)

        print(f"Measured IPD: {measured_ipd:.3f} ms")

        # Decode only in watermark mode
        if args.mode == "watermark":

            decoded_bit = (
                "1"
                if measured_ipd > BASELINE_IPD_MS
                else "0"
            )

            decoded_bits.append(decoded_bit)

            print(f"Decoded bit: {decoded_bit}")

    previous_timestamp = current_timestamp

    # Store receiver-side experiment data
    log_rows.append({
        "packet_number": packet_number,
        "mode": args.mode,
        "arrival_timestamp_ns": current_timestamp,
        "measured_ipd_ms": (
            round(measured_ipd, 3)
            if measured_ipd is not None
            else ""
        ),
        "decoded_bit": decoded_bit,
        "payload": message
    })

receiver.close()

# ==========================================
# PACKET ANALYSIS
# ==========================================

expected_numbers = set(
    range(1, PACKET_COUNT + 1)
)

received_numbers = set(received_packets)

missing_packets = sorted(
    expected_numbers - received_numbers
)

unexpected_packets = sorted(
    received_numbers - expected_numbers
)

duplicate_packets = (
    len(received_packets) - len(received_numbers)
)

decoded_vt = "".join(decoded_bits)

print("\n========== PACKET ANALYSIS ==========")

print(f"Expected packets: {PACKET_COUNT}")
print(f"Received packets: {len(received_packets)}")
print(f"Missing packets: {missing_packets}")
print(f"Unexpected packets: {unexpected_packets}")
print(f"Duplicate packets: {duplicate_packets}")

# ==========================================
# WATERMARK ANALYSIS
# ==========================================

print("\n========== WATERMARK ANALYSIS ==========")

if args.mode == "watermark":

    print(f"Decoded binary: {decoded_vt}")
    print(f"Decoded bit count: {len(decoded_bits)}")

else:

    print("Watermark decoding: NOT APPLICABLE")
    print("Normal mode does not encode a timing watermark.")

# ==========================================
# DETECTION AND CLASSIFICATION
# ==========================================

print("\n========== DETECTION DECISION ==========")

if not end_received:

    print("STATUS: UNDECODABLE")
    print("REASON: Transmission did not complete.")

elif unexpected_packets:

    print("STATUS: ATTACKED")
    print("CLASSIFICATION: PACKET INJECTION")
    print("REASON: Unexpected packet number detected.")

elif missing_packets:

    print("STATUS: ATTACKED")
    print("CLASSIFICATION: PACKET DROPPING")
    print("REASON: Expected packet number is missing.")

elif duplicate_packets:

    print("STATUS: ATTACKED")
    print("CLASSIFICATION: DUPLICATE / POSSIBLE REPLAY")
    print("REASON: Repeated packet number detected.")

elif args.mode == "normal":

    print("STATUS: NORMAL")
    print("REASON: Packet sequence is complete.")
    print("NOTE: No timing watermark or MAC verification was performed.")

elif len(decoded_bits) != EXPECTED_BITS:

    print("STATUS: UNDECODABLE")
    print("REASON: Incorrect watermark bit count.")

else:

    # Reconstruct payloads in original packet order
    ordered_payloads = [
        payloads_by_number[i]
        for i in range(1, PACKET_COUNT + 1)
    ]

    received_block_data = build_block_data(
        ordered_payloads
    )

    # Recalculate MAC from received payloads
    expected_vt, expected_mac_hex = (
        generate_virtual_trailer(received_block_data)
    )

    # Extract fields from decoded Virtual Trailer
    received_mac = int(
        decoded_vt[16:32], 2
    ).to_bytes(2, "big")

    expected_mac = bytes.fromhex(
        expected_mac_hex
    )

    recovered_block_num = int(
        decoded_vt[:8], 2
    )

    recovered_flow_id = int(
        decoded_vt[8:16], 2
    )

    print(f"BlockNum: {recovered_block_num}")
    print(f"FlowID: {recovered_flow_id}")
    print(f"Received MAC: {received_mac.hex()}")
    print(f"Expected MAC: {expected_mac.hex()}")

    if (
        recovered_block_num != BLOCK_NUM
        or recovered_flow_id != FLOW_ID
    ):

        print("STATUS: ATTACKED")
        print("REASON: BlockNum or FlowID mismatch.")

    elif hmac.compare_digest(
        received_mac,
        expected_mac
    ):

        print("STATUS: RECOVERED")
        print("RESULT: MAC MATCH")
        print("REASON: Integrity verification successful.")

    else:

        print("STATUS: ATTACKED")
        print("RESULT: MAC MISMATCH")
        print("CLASSIFICATION: PACKET MODIFICATION")
        print("REASON: Received payload differs from authenticated data.")

# ==========================================
# IPD STATISTICS
# ==========================================

print("\n========== IPD STATISTICS ==========")

if ipds:

    average_ipd = sum(ipds) / len(ipds)

    print(f"Number of intervals: {len(ipds)}")
    print(f"Average IPD: {average_ipd:.3f} ms")
    print(f"Minimum IPD: {min(ipds):.3f} ms")
    print(f"Maximum IPD: {max(ipds):.3f} ms")

# ==========================================
# RECEIVER CSV LOGGING
# ==========================================

log_directory = Path("logs")
log_directory.mkdir(exist_ok=True)

log_file = log_directory / (
    f"receiver_timing_{args.mode}.csv"
)

fieldnames = [
    "packet_number",
    "mode",
    "arrival_timestamp_ns",
    "measured_ipd_ms",
    "decoded_bit",
    "payload"
]

with open(log_file, "w", newline="") as csvfile:

    writer = csv.DictWriter(
        csvfile,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(log_rows)

print("\n========== EXPERIMENT LOG ==========")
print(f"Receiver records: {len(log_rows)}")
print(f"CSV saved: {log_file}")

print("\nReceiver stopped.")
