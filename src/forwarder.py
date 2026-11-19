
import socket
import argparse

FORWARDER_HOST = "127.0.0.1"
FORWARDER_PORT = 5006

RECEIVER_HOST = "127.0.0.1"
RECEIVER_PORT = 5005

PACKET_COUNT = 33
END_MARKER = b"__CHAINPATROL_END__"

parser = argparse.ArgumentParser(
    description="ChainPatrol Attack Simulator"
)

parser.add_argument(
    "--attack",
    choices=["none", "drop", "inject", "modify"],
    default="none"
)

parser.add_argument("--drop-index", type=int, default=10)
parser.add_argument("--inject-after", type=int, default=10)
parser.add_argument("--modify-index", type=int, default=10)

args = parser.parse_args()

for value, name in [
    (args.drop_index, "drop-index"),
    (args.inject_after, "inject-after"),
    (args.modify_index, "modify-index")
]:
    if not 1 <= value <= PACKET_COUNT:
        parser.error(f"--{name} must be between 1 and 33")

forwarder = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)

forwarder.bind((FORWARDER_HOST, FORWARDER_PORT))

print("====================================")
print("       CHAINPATROL FORWARDER")
print("====================================")
print(f"Attack mode: {args.attack.upper()}")

received_count = 0
forwarded_count = 0
dropped_count = 0
injected_count = 0
modified_count = 0

for i in range(PACKET_COUNT):

    data, sender_address = forwarder.recvfrom(2048)
    received_count += 1

    number_bytes, payload = data.split(b"|", 1)
    packet_number = int(number_bytes.decode("utf-8"))

    print(f"\nReceived packet {packet_number}")

    # Packet dropping
    if (
        args.attack == "drop"
        and packet_number == args.drop_index
    ):
        dropped_count += 1
        print(f"ATTACK: Dropped packet {packet_number}")
        continue

    # Packet modification
    if (
        args.attack == "modify"
        and packet_number == args.modify_index
    ):
        payload = b"TAMPERED DATA - " + payload
        data = number_bytes + b"|" + payload

        modified_count += 1
        print(f"ATTACK: Modified packet {packet_number}")

    # Forward packet
    forwarder.sendto(
        data,
        (RECEIVER_HOST, RECEIVER_PORT)
    )

    forwarded_count += 1
    print(f"Forwarded packet {packet_number}")

    # Packet injection
    if (
        args.attack == "inject"
        and packet_number == args.inject_after
    ):
        injected_packet = (
            b"999|UNAUTHORIZED INJECTED PACKET"
        )

        forwarder.sendto(
            injected_packet,
            (RECEIVER_HOST, RECEIVER_PORT)
        )

        injected_count += 1
        print("ATTACK: Injected packet 999")

# Signal end of transmission
forwarder.sendto(
    END_MARKER,
    (RECEIVER_HOST, RECEIVER_PORT)
)

forwarder.close()

print("\n========== FORWARDER SUMMARY ==========")
print(f"Original packets received: {received_count}")
print(f"Original packets forwarded: {forwarded_count}")
print(f"Packets dropped: {dropped_count}")
print(f"Packets injected: {injected_count}")
print(f"Packets modified: {modified_count}")
print("=======================================")
