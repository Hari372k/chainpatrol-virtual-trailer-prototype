# ChainPatrol: Virtual-Trailer Security Prototype

A simplified proof of concept inspired by the research paper **"ChainPatrol: Balancing Attack Detection and Classification with Performance Overhead for Service Function Chains Using Virtual Trailers"** by Momen Oqaily et al.

## 1. Project Overview

Traditional cryptographic trailers add integrity-related information to packet data, increasing communication overhead.

ChainPatrol explores an alternative approach: encoding integrity-related information into inter-packet delays (IPDs), rather than appending a physical trailer to every packet.

This project implements a simplified prototype to explore:

- UDP packet transmission and reception.
- IPD-based watermark encoding and decoding.
- Virtual Trailer generation and reconstruction.
- HMAC-based integrity verification.
- Packet attack simulation and detection.
- Performance comparison between normal and watermark traffic.

**Note:** This is an educational proof of concept, not a complete reproduction of the original ChainPatrol research implementation.

## 2. Architecture

The prototype contains three components:

```text
+------------------+
|   UDP Sender     |
|                  |
| Normal /         |
| Watermark Mode   |
+--------+---------+
         |
         | UDP :5006
         v
+------------------+
| Forwarder /      |
| Attacker         |
|                  |
| Drop / Inject /  |
| Modify           |
+--------+---------+
         |
         | UDP :5005
         v
+------------------+
|   UDP Receiver   |
|                  |
| IPD Decoding     |
| Packet Analysis  |
| MAC Verification|
+------------------+
```

All components run locally using UDP sockets on `127.0.0.1`.

## 3. Virtual Trailer Design

The prototype uses a 32-bit Virtual Trailer:

| Field | Size | Purpose |
|---|---:|---|
| BlockNum | 8 bits | Identifies the block |
| FlowID | 8 bits | Identifies the traffic flow |
| MAC | 16 bits | Provides a truncated integrity value |
| **Total** | **32 bits** | |

The MAC is generated using HMAC-SHA256 and truncated to 16 bits.

The authenticated data includes BlockNum, FlowID and packet payload data.

The prototype uses a simplified HMAC construction rather than implementing the complete Merkle-tree HMAC mechanism described in the research paper.

**Security note:** The HMAC secret key is hardcoded in the source code for demonstration purposes only. In a real-world implementation, the key should be securely generated, stored and managed. The hardcoded key used in this prototype must not be used in production.

## 4. IPD Watermark Encoding

The sender supports two transmission modes.

| Parameter | Value |
|---|---:|
| Baseline IPD | 50 ms |
| Watermark amplitude | 10 ms |
| Bit 0 | 40 ms target interval |
| Bit 1 | 60 ms target interval |
| Packets | 33 |
| Encoded bits | 32 |

The encoding rule is:

```text
Bit 1: IPD = 50 + 10 = 60 ms
Bit 0: IPD = 50 - 10 = 40 ms
```

Normal mode uses a fixed target interval of 50 ms.

Watermark mode changes the target interval according to the Virtual Trailer bit sequence.

The receiver measures packet arrival timestamps and estimates each bit by comparing the measured IPD with the 50 ms baseline.

## 5. Attack Simulation

The intermediate forwarder supports three selectable attack modes.

| Attack | Implementation | Expected detection |
|---|---|---|
| Packet dropping | Drops a selected packet | Missing packet |
| Packet injection | Injects unauthorized packet 999 | Unexpected packet |
| Packet modification | Changes a selected payload | Integrity verification failure |

The receiver analyses packet numbers, missing packets, unexpected packets, duplicates and integrity values.

The prototype has demonstrated successful packet-drop and injection detection, and a MAC mismatch in a packet-tampering experiment.

Attack classification is simplified and based on observable packet and integrity symptoms.

## 6. Technology Stack

- Python 3
- UDP sockets
- HMAC and SHA-256
- Python `argparse`
- CSV experiment logging
- Matplotlib
- Ubuntu on Windows Subsystem for Linux (WSL)

## 7. Project Structure

```text
chainpatrol/
|
|-- src/
|   |-- analyze_performance.py
|   |-- forwarder.py
|   |-- udp_receiver.py
|   |-- udp_sender.py
|   |-- virtual_trailer.py
|
|-- experiments/
|   |-- crypto_foundation.py
|   |-- hello_chainpatrol.py
|   |-- ipd_calculator.py
|   |-- merkle_experiment.py
|   |-- merkle_tamper_detection.py
|
|-- logs/
|   |-- receiver_timing_normal.csv
|   |-- receiver_timing_watermark.csv
|   |-- sender_timing.csv
|   |-- sender_timing_normal.csv
|   |-- sender_timing_watermark.csv
|
|-- results/
|   |-- average_ipd_comparison.png
|   |-- ipd_standard_deviation.png
|   |-- ipd_variation.png
|   |-- performance_summary.csv
|
|-- requirements.txt
|-- .gitignore
|-- README.md
```

The `experiments/` directory contains preliminary implementations developed to understand cryptographic integrity, IPD calculation, and Merkle-tree concepts before building the main prototype.

## 8. Installation

Clone the repository:

```bash
git clone https://github.com/Hari372k/chainpatrol-virtual-trailer-prototype.git
cd chainpatrol-virtual-trailer-prototype
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 9. Running the Prototype

Open three separate WSL terminal windows.

Activate the virtual environment in each:

```bash
cd ~/chainpatrol
source .venv/bin/activate
```

### Terminal 1: Receiver

Normal mode:

```bash
python3 src/udp_receiver.py --mode normal
```

Watermark mode:

```bash
python3 src/udp_receiver.py --mode watermark
```

### Terminal 2: Forwarder

No attack:

```bash
python3 src/forwarder.py --attack none
```

Packet dropping:

```bash
python3 src/forwarder.py --attack drop --drop-index 10
```

Packet injection:

```bash
python3 src/forwarder.py --attack inject --inject-after 10
```

Packet modification:

```bash
python3 src/forwarder.py --attack modify --modify-index 10
```

### Terminal 3: Sender

Normal transmission:

```bash
python3 src/udp_sender.py --mode normal
```

Watermark transmission:

```bash
python3 src/udp_sender.py --mode watermark
```

Start the receiver first, then the forwarder, and finally the sender.

For attack experiments, use watermark mode on both sender and receiver.

## 10. Performance Evaluation

The prototype compares normal and watermark traffic using recorded IPD measurements.

The following results were obtained in a local test run:

| Metric | Normal | Watermark |
|---|---:|---:|
| Packets | 33 | 33 |
| IPD intervals | 32 | 32 |
| Average IPD | 50.346 ms | 50.326 ms |
| Minimum IPD | 50.052 ms | 39.908 ms |
| Maximum IPD | 50.607 ms | 60.505 ms |
| IPD standard deviation | 0.109 ms | 10.042 ms |

Watermark extraction results from the same experiment:

```text
Intended bits:       32
Decoded bits:        32
Compared bits:       32
Correct bits:        32

Extraction accuracy: 100.00%
```

These measurements demonstrate successful watermark extraction under the controlled local test conditions.

The experiment is small-scale and does not establish accuracy under real network conditions or substantial jitter.

## 11. Experiment Outputs

Timing records are saved under `logs/`.

Performance analysis can be executed using:

```bash
python3 src/analyze_performance.py
```

Generated graphs and the performance summary are stored under `results/`.

The included visualizations compare:

- Average IPD.
- IPD standard deviation.
- Inter-packet delay variation.

## 12. Limitations and Future Improvements

This implementation is a simplified prototype. The following aspects remain incomplete or require further investigation:

1. The full Merkle-tree HMAC mechanism from the research paper has not been reproduced.
2. The prototype uses a single block and flow configuration rather than multiple SuperBlocks and flows.
3. The paper's next-SuperBlock trailer-embedding mechanism is not fully implemented.
4. Packet reordering and replay attacks have not been implemented.
5. Flow injection and flow dropping have not been implemented.
6. Jitter tolerance and adaptive watermark decoding require further testing.
7. Performance evaluation is currently based on local UDP communication.
8. CPU usage, encoding/decoding time and detection/classification time have not been comprehensively benchmarked.
9. The current 16-bit truncated MAC is suitable for demonstrating the concept, not for production security.

Future work could include multi-block authentication, improved jitter handling, additional attack simulations, network namespaces or container-based testbeds, and more extensive performance evaluation.

## 13. Conclusion

This project demonstrates a simplified implementation of the central ChainPatrol concept: using packet timing as a carrier for integrity-related information.

It establishes a working UDP sender-forwarder-receiver architecture, implements timing-based watermark transmission and decoding, reconstructs a Virtual Trailer, verifies a truncated HMAC, simulates three packet-level attacks, and evaluates IPD behaviour using experimental data.

The implementation provides a foundation for further investigation into timing-based integrity verification and attack detection in service function chains.

**Research reference:** Momen Oqaily et al., *ChainPatrol: Balancing Attack Detection and Classification with Performance Overhead for Service Function Chains Using Virtual Trailers*.
