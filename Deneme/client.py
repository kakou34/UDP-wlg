import hashlib
import socket
import struct

unpacker = struct.Struct('I I 8s 32s')
interval = 0.009
expected_seq = 0
UDP_IP = "127.0.0.1"
UDP_PORT = 8080
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dataList = (b'NCC-1010', b'NCC-1011', b'NCC-1012')
kelimeler = []
seq = 0

# Client için checksum alıyor
def get_checksum(ack, seq, data):
    values = (ack, seq, data)
    UDP_Data = struct.Struct('I I 8s')
    packed_data = UDP_Data.pack(*values)
    checksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")
    return checksum
# Server ve Client checksumlarının kontrol edilmesi gerekiyor
def compare_checksum(ack, seq, data, checksum_received):
    checksum = get_checksum(ack, seq, data)
    if checksum_received == checksum:
        return True
    else:
        return False
#UDP oluşturup, ack seq ve data inputları kontrol ediliyor
def create_UDP_Packet(ack, seq, data):
    checksum = get_checksum(ack, seq, data)
    values = (ack, seq, data, checksum)
    UDP_Packet_Data = struct.Struct('I I 8s 32s')
    UDP_Packet = UDP_Packet_Data.pack(*values)
    values = (ack, seq, data.decode("utf-8"), checksum.decode("utf-8"))
    return UDP_Packet, values
#data gönderimi


def sendPacket(UDP_Packet) :
    unpacker = struct.Struct('I I 8s 32s')
    UDP_Packet_Data = unpacker.unpack(UDP_Packet)
    valueSent = (
    UDP_Packet_Data[0], UDP_Packet_Data[1], UDP_Packet_Data[2].decode("utf-8"), UDP_Packet_Data[3].decode("utf-8"))
    print('Packet sent: ', valueSent)
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientSocket.sendto(UDP_Packet, (UDP_IP, UDP_PORT))
    clientSocket.settimeout(0.009)

    try :
        retData, addr = clientSocket.recvfrom(1024)  # buffer size = 1024
        UDP_PacketRet = unpacker.unpack(retData)
        values = (UDP_PacketRet[0], UDP_PacketRet[1], UDP_PacketRet[2].decode("utf-8"), UDP_PacketRet[3].decode("utf-8"))
        print("Alınan", addr)
        print("Alınan mesaj", values)
        if compare_checksum(UDP_PacketRet[0], UDP_PacketRet[1], UDP_PacketRet[2], UDP_PacketRet[3]) :
            print('Checksumlar eşleşti')
            if UDP_PacketRet[1] == UDP_Packet_Data[1] :
                print('Beklenen sıra numarası alındı.')
            else :
                print("Beklenen sıra numarası alınamadı.")

                sendPacket(UDP_Packet)

        else :
            print('Checksumlar eşleşmedi, paket tekrar gönderiliyor.')
            sendPacket(UDP_Packet)

    except socket.timeout as e :
        print("Gönderim sırasında zaman aşımı görüldü")
        sendPacket(UDP_Packet)


while True:
    for data in dataList:
        UDP_Packet, values = create_UDP_Packet(0, seq, data)
        sendPacket(UDP_Packet)
        seq = (seq + 1) % 2

    client_message = input("Kelime giriniz:")
    if client_message not in kelimeler:
        client_message.sendto(client_message.encode(), (UDP_IP, UDP_PORT))
        kelimeler.append(client_message)
    elif client_message == "çıkış":
        print("client terk etti.")
    else:
        print("Başka bir kelime seçiniz.")

    message, address = clientSocket.recvfrom(2048)
    receive_confirmed_message = message.decode('utf-8')

    message, addr = clientSocket.recvfrom(2048)
    server_message = message.decode('utf-8')
    print(server_message)

    if server_message:
        send_confirm_message = "Paket alındı"
        clientSocket.sendto(send_confirm_message.encode(), (UDP_IP, UDP_PORT))