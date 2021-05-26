import socket
import time
import hashlib
import sys


def get_checksum(message):
    checksum = hashlib.sha1(message.encode("UTF-8")).hexdigest()
    return checksum


def send_ack(addr, ack):
    if ack:
        message = bytes("ACK".encode("UTF-8"))
    else:
        message = bytes("UNACK".encode("UTF-8"))
    client_socket.sendto(message, addr)


def wait_ack():
    try:
        data, addr = client_socket.recvfrom(1024)
        message = data.decode()
        return message == "ACK"
    except socket.timeout as e:
        return False


def receive(seq_flag):
    try:
        data, addr = client_socket.recvfrom(1024)
        rec_packet = data.decode()
        rec_packet = rec_packet.split(',')
        seq = int(rec_packet[0])
        exp_checksum = rec_packet[1]
        server_message = rec_packet[2]
        checksum = get_checksum(server_message)
        if checksum != exp_checksum:
            send_ack(SERVER, False)
            print("CHECKSUM ERROR!\nChecksums are different. Please restart the game!")
            sys.exit()
        if seq_flag != seq:
            send_ack(SERVER, False)
            print("ORDER ERROR!\nSequences are different. Please restart the game!")
            sys.exit()
        send_ack(SERVER, True)
        seq_flag = not seq_flag
        return int(seq_flag), server_message
    except socket.timeout as e:
        print("TIMEOUT ERROR! Your rival is not responding!")
        send_ack(SERVER, False)


def send_packet(msg, seq):
    pkt = f'{seq},{get_checksum(msg)},{msg}'
    client_socket.sendto(pkt.encode('UTF-8'), SERVER)


client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(60)
SERVER = ('127.0.0.1', 1234)
words = []
seq_flag = 0

msg = "CONNECT"
send_packet(msg, seq_flag)
ack = wait_ack()
if ack:
    print("ACK RECEIVED: You successfully joined the game")
    seq_flag = not seq_flag
else:
    print("ACK NOT RECEIVED: Your packet was lost\nPlease try again!")
    sys.exit()

seq_flag, server_message = receive(seq_flag)
words.append(server_message)
print("Rival: " + server_message)

time_left = 20
while True:
    start_time = time.time()
    client_message = input("Enter your word:")

    if client_message == 'exit':
        message = "Your rival left the game!"
        print("You left the game!")
        send_packet(message, seq_flag)
        ack = wait_ack()
        if ack:
            print("ACK RECEIVED: Your message was successfully sent!")
        else:
            print("ACK NOT RECEIVED! Your packet was lost!\n")
        sys.exit()

    elif server_message[-2:] != client_message[0:2]:
        print("The word must start with ", server_message[-2:])
        time_spent = time.time() - start_time
        time_left = time_left - time_spent
        continue

    elif client_message in words:
        print("The word you entered has already been used, try again!")
        time_spent = time.time() - start_time
        time_left = time_left - time_spent
        continue

    else:
        time_spent = time.time() - start_time
        time_left = time_left - time_spent
        if time_left <= 0:
            print("time is up! you lost :/")
            message = "Time is up! You won!"
            send_packet(message, seq_flag)
            ack = wait_ack()
            if ack:
                print("ACK RECEIVED: Your message was successfully sent!")
            else:
                print("ACK NOT RECEIVED: Your packet was lost!")
            sys.exit()

        send_packet(client_message, seq_flag)
        ack = wait_ack()
        if ack:
            print("ACK RECEIVED: Your word was successfully sent")
            words.append(client_message)
            seq_flag = not seq_flag
        else:
            print("ACK NOT RECEIVED\nYour packet was lost. Please restart the game!")
            sys.exit()

    seq_flag, server_message = receive(seq_flag)
    exit_msg = "Your rival left the game!"
    if (server_message == 'Time is up! YOU WON!') or (server_message == exit_msg):
        print(server_message)
        break
    words.append(server_message)
    print("Your rival:", server_message)

    time_left = 20
