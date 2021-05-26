import hashlib
import socket
import struct
from datetime import time
from random import random

#checksum değerleri alınır#
def get_checksum(ack, seq, data):
    value = (ack, seq, data)
    UDP_Data = struct.Struct('I I 8s')
    packed_data = UDP_Data.pack(*value)
    checksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")
    return checksum
# checksumların karşılaştırılması gerekir#
def compare_checksum(ack, seq, data, received_checksum):
    checksum = get_checksum(ack, seq, data)
    if received_checksum == checksum:
        return True
    else:
        return False
#UDP oluşturup ack,seq ve data inputları ile çalışır#
def create_UDP_Packet(ack, seq, data):
    checksum = get_checksum(ack, seq, data)
    values = (ack, seq, data, checksum)
    UDP_Packet_Data = struct.Struct('I I 8s 32s')
    UDP_Packet = UDP_Packet_Data.pack(*values)
    values = (ack, seq, data.decode("utf-8"), checksum.decode("utf-8"))
    return UDP_Packet, values
#Network gecikebilir#
def Network_Delay():
    if True and random.choice([0, 1, 0]) == 1:
        time.sleep(.01)
        print("Paket gecikti")
#paket yolda kaybolabilir bu yüzden ack değeri olmaz#
def Network_Loss():
    if True and random.choice([0, 1, 1, 0]) == 1:
        print("Paket kayboldu bu yüzden ACK yok.")
        return(1)
    else:
        return(0)

def Packet_Checksum_Corrupter(packet):
    if True and random.choice([0, 1, 0, 1]) == 1:
        print('Packet corruption!')
        UDP_PacketData = unpacker.unpack(packet)
        packet_data = (UDP_PacketData[0], UDP_PacketData[1], b'Corrupt!', UDP_PacketData[3])
        UDP_Packet_Data = struct.Struct('I I 8s 32s')
        UDP_Packet = UDP_Packet_Data.pack(*packet_data)
        return True, UDP_Packet
    else:
        return False, packet
#data gönderir#
def sendPacket(UDP_Packet, addr):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(UDP_Packet, addr)

##
host = "127.0.0.1"  #calışmaz ise 0.0.0.0 deneyiniz#
port = 8080
unpacker = struct.Struct('I I 8s 32s')
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverSocket.bind((host, port))
expectedSeq = 0
kelimeler = []

while True:
    request, addr = serverSocket.recvfrom(1024)
    UDP_Packet = unpacker.unpack(request)
    values = (UDP_Packet[0], UDP_Packet[1], UDP_Packet[2].decode("utf-8"), UDP_Packet[3].decode("utf-8"))
    print("Alınan adres:", addr)
    print("Alınan değer:", values)
    # eğer checksumda bir problem yoksa ve network kaybedilmediyse word-letter oyununda istenilen conditionları yerine getirir
    if compare_checksum(UDP_Packet[0], UDP_Packet[1], UDP_Packet[2], UDP_Packet[3]):
        print('Checksumlar eşleşti.')

        if UDP_Packet[1] == expectedSeq:
            print('Beklenen checksuma erişildi')
            expectedSeq = (expectedSeq + 1) % 2
        else:
            print('Aynı checksum geldi.')

        UDPResponse, values = create_UDP_Packet(1, UDP_Packet[1], UDP_Packet[2])
        if not Network_Loss():
            Network_Delay()
            corrupt, UDPResponse = Packet_Checksum_Corrupter(UDPResponse)
            if corrupt:
                values = (values[0], values[1],'Corrupt!',  values[3])
            sendPacket(UDPResponse, addr)
            print('Packet sent: ', values,"\n")

    else:
        print('Checksumlar eşleşmedi')

        UDPResponse, values = create_UDP_Packet(1, (UDP_Packet[1] + 1) % 2, UDP_Packet[2])
        if not Network_Loss():
            Network_Delay()
            corrupt, UDPResponse = Packet_Checksum_Corrupter(UDPResponse)

            if corrupt:
                values = (values[0], values[1], 'Corrupt!', values[3])
            sendPacket(UDPResponse, addr)
            print('Gönderilen: ', values)
    # paketi aldıktan sonra paket alındı mesajı gönderip bilgilendiriyor
    message, addr = serverSocket.recvfrom(1024)
    client_message = message.decode('utf-8')
    if client_message:
        send_confirm_message = "Paket alındı"
        serverSocket.sendto(send_confirm_message.encode(), (host, port))

    server_message = input("Mesajınızı giriniz.")
    a = len(client_message)
    if client_message not in kelimeler:
        if client_message[a - 2:a] == server_message[0:2]:
            serverSocket.sendto(server_message.encode(), (host, port))
            print(server_message)
            kelimeler.append(server_message)
        elif client_message == 'Çıkış':
            print(host, 'terk etti!')
        else:
            print('Gönderemezsiniz.')
    else:
        print("Daha önce kullanılmamış bir kelime seçiniz.")

    client_confirm_message, address = serverSocket.recvfrom(2024)
    receive_confirm_message = client_confirm_message.decode('utf-8')