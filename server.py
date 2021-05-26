import socket
import sys
import time
import hashlib
import random


def get_checksum(message):
    checksum = hashlib.sha1(message.encode("UTF-8")).hexdigest()
    return checksum


def send_ack(addr, ack):
    if ack:
        message = bytes("ACK".encode("UTF-8"))
    else:
        message = bytes("UNACK".encode("UTF-8"))
    server_socket.sendto(message, addr)


def wait_ack():
    try:
        data, addr = server_socket.recvfrom(1024)
        message = data.decode()
        return message == "ACK"
    except socket.timeout as e:
        return False


def receive(seq_flag, addr):
    try:
        checksum_prob = 0
        seq_prob = 0
        if error_simulation:
            checksum_prob = random.randint(0, 100)
            seq_prob = random.randint(0, 100)
        data, addr = server_socket.recvfrom(1024)
        rec_packet = data.decode()
        rec_packet = rec_packet.split(',')
        seq = int(rec_packet[0])
        exp_checksum = rec_packet[1]
        msg = rec_packet[2]
        checksum = get_checksum(msg)
        if checksum_prob > 70:
            print('!!! Attempting Checksum Corruption !!!')
            checksum = 'xxxxxxxxx'
        if seq_prob > 70:
            print('!!! Attempting Order Corruption !!!')
            seq_flag = int(not seq)
        if checksum != exp_checksum:
            send_ack(addr, False)
            print("CHECKSUM ERROR!\nChecksums are different. Please restart the game!")
            sys.exit()
        if seq != seq_flag:
            send_ack(addr, False)
            print("ORDER ERROR!\nSequences are different. Please restart the game!")
            sys.exit()
        send_ack(addr, True)
        seq_flag = not seq_flag
        return int(seq_flag), msg
    except socket.timeout as e:
        print("TIMEOUT ERROR!\nYour rival is not responding!")
        send_ack(addr, False)
        sys.exit()


def send_packet(addr, msg, seq):
    packet = f'{seq},{get_checksum(msg)},{msg}'
    server_socket.sendto(packet.encode("UTF-8"), addr)


server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.settimeout(60)
server_socket.bind(("127.0.0.1", 1234))
seq_flag = 0
words = []
error_simulation = True

# Handshaking:
while True:
    print('Waiting for the client...')
    data, addr = server_socket.recvfrom(1024)
    rec_packet = data.decode()
    rec_packet = rec_packet.split(',')
    seq = int(rec_packet[0])
    exp_checksum = rec_packet[1]
    msg = rec_packet[2]
    checksum = get_checksum(msg)
    if checksum != exp_checksum:
        send_ack(addr, False)
        print("CHECKSUM ERROR!\nChecksums are different. Please restart the game!")
        sys.exit()
    if seq != seq_flag:
        send_ack(addr, False)
        print("ORDER ERROR!\nSequences are different. Please restart the game!")
        sys.exit()
    if msg == 'CONNECT':
        break


send_ack(addr, True)
seq_flag = int(not seq_flag)
print("A client joined your game!")

while True:
    server_message = input('Enter the first word:')
    if len(server_message) > 1:
        send_packet(addr, server_message, seq_flag)
        ack = wait_ack()
        if ack:
            print("ACK RECEIVED: Your word was successfully sent")
            words.append(server_message)
            seq_flag = not seq_flag
        else:
            print("ACK NOT RECEIVED: Your packet was lost. Please restart the game!")
            sys.exit()
        break
    print("Your word should contain at least 2 characters.")

seq_flag, client_message = receive(seq_flag, addr)
exit_msg = "Your rival left the game!"
if (client_message == 'Time is up! You won!') or (client_message == exit_msg):
    print(client_message)
    sys.exit()
words.append(client_message)
print("Your rival: " + client_message)

time_left = 20
while True:

    start_time = time.time()
    server_message = input('Enter your word:')

    if server_message == 'exit':
        message = "Your rival left the game!"
        print("You left the game!")
        send_packet(addr, message, seq_flag)
        ack = wait_ack()
        if ack:
            print("ACK RECEIVED: Your message was successfully sent!")
        else:
            print("ACK NOT RECEIVED: Your packet was lost. Please restart the game!")
        sys.exit()

    elif client_message[-2:] != server_message[0:2]:
        print("The word must start with ", client_message[-2:])
        time_spent = time.time() - start_time
        time_left = time_left - time_spent
        continue
    elif server_message in words:
        print("The word you entered has already been used, try again!")
        time_spent = time.time() - start_time
        time_left = time_left - time_spent
        continue
    else:
        time_spent = time.time() - start_time
        time_left = time_left - time_spent
        if time_left <= 0:
            print("time is up! You lost :/")
            message = "Time is up! You won!"
            send_packet(addr, message, seq_flag)
            ack = wait_ack()
            if ack:
                print("ACK RECEIVED: Your message was successfully sent!")
            else:
                print("ACK NOT RECEIVED: Your packet was lost. Please restart the game!!")
            sys.exit()

        send_packet(addr, server_message, seq_flag)
        ack = wait_ack()
        if ack:
            print(" ACK RECEIVED: Your word was successfully sent")
            words.append(server_message)
            seq_flag = not seq_flag
        else:
            print("ACK NOT RECEIVED: Your packet was lost. Please restart the game!!")
            sys.exit()

    seq_flag, client_message = receive(seq_flag, addr)
    exit_msg = "Your rival left the game!"
    if (client_message == 'Time is up! YOU WON!') or (client_message == exit_msg):
        print(client_message)
        break
    words.append(client_message)
    print("Your rival:", client_message)

    time_left = 20

