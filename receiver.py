from socket import *
import struct
import time

RECEIVER_PORT = 5200
file_paths = ['images/received_file1.jpeg', 'images/received_file2.jpeg', 'images/received_file3.jpeg']


def receive_file(file_path):
    with socket(AF_INET, SOCK_DGRAM) as receiver:
        receiver.bind(('127.0.0.1', RECEIVER_PORT))

        while True:
            received_data = {}
            expected_packet_id = 0
            total_packets = None
            start_time = time.time()

            print("Waiting for packets......")

            while True:
                packet, sender_addr = receiver.recvfrom(1024)
                if len(packet) < 2:
                    continue

                if total_packets is None:
                    total_packets = struct.unpack("!H", packet[:2])[0]
                    print(f"Expecting total packets: {total_packets}")
                    continue

                packet_id, file_id, chunk, trailer = struct.unpack(f"!HH{len(packet) - 8}sI", packet)

                print(f"Received packet {packet_id + 1}/{total_packets}")

                if packet_id == expected_packet_id:
                    received_data[packet_id] = chunk
                    ack_packet = struct.pack("!HH", packet_id, file_id)
                    receiver.sendto(ack_packet, sender_addr)
                    print(f"Acknowledgment sent for packet {packet_id + 1}")
                    expected_packet_id += 1

                    if expected_packet_id == total_packets:
                        break
                else:
                    print(f"Packet {packet_id + 1} discarded. Waiting for packet {expected_packet_id + 1}")

            end_time = time.time()  # Record end time
            elapsed_time = end_time - start_time
            total_bytes = sum(len(chunk) for chunk in received_data.values())

            average_transfer_rate_bytes = total_bytes / elapsed_time
            average_transfer_rate_packets = total_packets / elapsed_time

            print()
            print("File transfer information:")
            print(f"Start time: {start_time}")
            print(f"End time: {end_time}")
            print(f"Elapsed time: {elapsed_time} seconds")
            print(f"Number of packets: {total_packets}")
            print(f"Number of bytes: {total_bytes}")
            print(f"Average transfer rate (bytes/sec): {average_transfer_rate_bytes}")
            print(f"Average transfer rate (packets/sec): {average_transfer_rate_packets}")

            with open(file_path, 'wb') as file:
                for packet_id in range(total_packets):
                    file.write(received_data[packet_id])

            print(f"File saved as '{file_path}'")
            print("File reception complete.")
            break


for file_path in file_paths:
    receive_file(file_path)
    print(f"Finished receiving {file_path}\n")
