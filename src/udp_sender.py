
import socket
import time
import argparse
import csv
from pathlib import Path

from virtual_trailer import (
    PACKET_PAYLOADS,
    BLOCK_NUM,
    FLOW_ID,
    generate_virtual_trailer
)

# Network configuration
HOST = "127.0.0.1"
PORT = 5006

# Watermark configuration
BASELINE_IPD_MS = 50
AMPLITUDE_MS = 10

# Command-line mode selection
parser = argparse.ArgumentParser(
    description="ChainPatrol Sender"
)

parser.add_argument(
    "--mode",
    choices=["normal", "watermark"],
    default="watermark",
    help="Select normal or watermark transmission"
)

args = parser.parse_args()

# Generate Virtual Trailer
vt_bits, mac_hex = generate_virtual_trailer()

# Create UDP socket
sender = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)

# Prepare logging directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "sender_timing.csv"

print("====================================")
print("       CHAINPATROL SENDER")
print("====================================")

print(f"Mode: {args.mode.upper()}")
print(f"BlockNum: {BLOCK_NUM}")
print(f"FlowID: {FLOW_ID}")
print(f"Virtual Trailer: {vt_bits}")
print(f"MAC: {mac_hex}")
print(f"Packets to send: {len(PACKET_PAYLOADS)}")

# Calculate the target interval after each packet
target_intervals = []

for bit in vt_bits:

    if args.mode == "watermark":

        if bit == "1":
            target = BASELINE_IPD_MS + AMPLITUDE_MS
        else:
            target = BASELINE_IPD_MS - AMPLITUDE_MS

    else:
        # Normal mode: fixed baseline interval
        target = BASELINE_IPD_MS

    target_intervals.append(target)

# CSV logging fields
fieldnames = [
    "packet_number",
    "mode",
    "intended_bit",
    "original_ipd_ms",
    "modified_ipd_ms",
    "measured_sender_ipd_ms",
    "block_num",
    "flow_id",
    "virtual_trailer"
]

previous_timestamp = None
log_rows = []

# Send all packets
for i, payload in enumerate(PACKET_PAYLOADS):

    packet_number = i + 1

    # Application-level sequence label for attack detection
    packet = (
        str(packet_number).encode("utf-8")
        + b"|"
        + payload
    )

    sender.sendto(packet, (HOST, PORT))

    current_timestamp = time.monotonic_ns()

    print(f"\nSent packet {packet_number}")

    # Measure actual sender-side IPD
    if previous_timestamp is not None:

        measured_ipd = (
            current_timestamp - previous_timestamp
        ) / 1_000_000

        interval_index = i - 1

        intended_bit = (
            vt_bits[interval_index]
            if args.mode == "watermark"
            else ""
        )

        original_ipd = BASELINE_IPD_MS
        modified_ipd = target_intervals[interval_index]

        log_rows.append({
            "packet_number": interval_index + 1,
            "mode": args.mode,
            "intended_bit": intended_bit,
            "original_ipd_ms": original_ipd,
            "modified_ipd_ms": modified_ipd,
            "measured_sender_ipd_ms": round(measured_ipd, 3),
            "block_num": BLOCK_NUM,
            "flow_id": FLOW_ID,
            "virtual_trailer": vt_bits
        })

        print(f"Measured sender IPD: {measured_ipd:.3f} ms")

    # Wait before sending the next packet
    if i < len(target_intervals):

        target = target_intervals[i]

        if args.mode == "watermark":
            print(
                f"Encoding bit {vt_bits[i]} "
                f"| Target IPD: {target} ms"
            )
        else:
            print(f"Normal mode | Target IPD: {target} ms")

        time.sleep(target / 1000)

    previous_timestamp = current_timestamp

sender.close()

# Write experiment log
with open(LOG_FILE, "w", newline="") as csvfile:

    writer = csv.DictWriter(
        csvfile,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(log_rows)

print("\n====================================")
print("Transmission completed.")
print(f"Mode: {args.mode.upper()}")
print(f"Packets sent: {len(PACKET_PAYLOADS)}")
print(f"Timing records: {len(log_rows)}")
print(f"CSV log saved: {LOG_FILE}")
print("====================================")
