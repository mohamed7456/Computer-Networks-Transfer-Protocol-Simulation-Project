from socket import *
import struct
import random
import time
import matplotlib.pyplot as plt


def read_img(path):
    with open(path, 'rb') as file:
        img = file.read()
    return img


def divide_img(img, file_id, packet_id, HeaderSize):
    packets = []
    chunk_size = MSS - HeaderSize
    for i in range(0, len(img), chunk_size):
        packet_data = img[i:i + chunk_size]
        if i + chunk_size >= len(img):
            trailer = 0xFFFFFFFF
        else:
            trailer = 0x00000000
        packet = struct.pack(f"!HH{len(packet_data)}sI", packet_id, file_id, packet_data, trailer)
        packets.append(packet)
        packet_id += 1
    return packets


HEADER_SIZE = 32
MSS = 1000
N = 15
TIMEOUT = 2
LOSS_RATE = random.uniform(0.05, 0.15)

receiver_ip = '127.0.0.1'
receiver_port = 5200

small_img_path = 'images/small_file.jpeg'
medium_img_path = 'images/medium_file.jpeg'
large_img_path = 'images/large_file.jpeg'

files = [
    (1, small_img_path),
    (2, medium_img_path),
    (3, large_img_path)
]


def send_file(img_id, img_path):
    img = read_img(img_path)
    packets = divide_img(img, img_id, 0, HEADER_SIZE)
    total_packets = len(packets)
    print(f"Total packets: {total_packets}")
    total_bytes = len(img)
    print(f"Total bytes: {total_bytes}")

    with socket(AF_INET, SOCK_DGRAM) as sender:
        sender.sendto(struct.pack("!H", total_packets), (receiver_ip, receiver_port))
        sender.settimeout(TIMEOUT)
        base = 0
        next_seq_num = 0
        retransmissions = 0
        packet_times = []
        packet_ids = []
        retransmission_times = []
        retransmitted_packet_ids = []

        start_time = time.time()

        while base < total_packets:
            while next_seq_num < min(base + N, total_packets):
                packet = packets[next_seq_num]
                current_time = time.time() - start_time
                if random.random() > LOSS_RATE:
                    sender.sendto(packet, (receiver_ip, receiver_port))
                    print(f"[{current_time:.4f}] Sent packet {next_seq_num + 1}")
                    packet_times.append(current_time)
                    packet_ids.append(next_seq_num + 1)
                else:
                    print(f"[{current_time:.4f}] Packet {next_seq_num + 1} lost.")
                    retransmissions += 1
                next_seq_num += 1

            try:
                while True:
                    ack, _ = sender.recvfrom(1024)
                    if len(ack) < 4:
                        print("Received an incomplete ACK packet")
                        continue
                    ack_packet_id, _ = struct.unpack("!HH", ack[:4])
                    if ack_packet_id >= base:
                        base = ack_packet_id + 1
                        break
            except timeout:
                print("Timeout, resending unacknowledged packets")
                next_seq_num = base
                for seq_num in range(base, min(base + N, total_packets)):
                    packet = packets[seq_num]
                    current_time = time.time() - start_time
                    sender.sendto(packet, (receiver_ip, receiver_port))
                    retransmission_times.append(current_time)
                    retransmitted_packet_ids.append(seq_num + 1)
                    print(f"[{current_time:.4f}] Retransmitted packet {seq_num + 1}")
                    retransmissions += 1

        end_time = time.time()
        elapsed_time = end_time - start_time

        average_transfer_rate_bytes = total_bytes / elapsed_time
        average_transfer_rate_packets = total_packets / elapsed_time
        print()
        print("File transfer information:")
        print(f"Start time: {start_time}")
        print(f"End time: {end_time}")
        print(f"Elapsed time: {elapsed_time} seconds")
        print(f"Number of packets: {total_packets}")
        print(f"Number of bytes: {total_bytes}")
        print(f"Number of retransmissions (sender): {retransmissions}")
        print(f"Average transfer rate (bytes/sec): {average_transfer_rate_bytes}")
        print(f"Average transfer rate (packets/sec): {average_transfer_rate_packets}")

        print("All packets sent and acknowledged. Sender terminated.")

        plt.figure(figsize=(10, 6))
        plt.plot(packet_times, packet_ids, 'bo-', label='Sent packets')
        if retransmission_times:
            plt.plot(retransmission_times, retransmitted_packet_ids, 'ro', label='Retransmitted packets')
        plt.xlabel('Time (s)')
        plt.ylabel('Packet ID')
        plt.title(f'Packet Transmission for File {img_id}')
        plt.legend()
        plt.figtext(0.15, 0.85,
                    f'Loss Rate: {LOSS_RATE:.2%}\nWindow Size: {N}\nTimeout: {TIMEOUT}s\nRetransmissions: {retransmissions}')
        plt.grid(True)
        plt.savefig(f'images/file_{img_id}_transmission_plot.png')
        plt.show()


for img_id, img_path in files:
    input(f"Press Enter to start transferring file {img_id}")
    send_file(img_id, img_path)
    print(f"Finished transferring file {img_id}\n")
