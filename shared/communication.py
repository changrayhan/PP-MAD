# shared/communication.py
import json
import socket
import struct
from typing import Any, Dict

class CommunicationProtocol:
    """客户端和服务器之间的通信协议"""
    
    HEADER_SIZE = 8
    ENCODING = 'utf-8'
    
    @staticmethod
    def send_data(sock: socket.socket, data: bytes, data_type: str = "binary"):
        """发送数据"""
        if data_type == "json":
            data = json.dumps(data).encode(CommunicationProtocol.ENCODING)
        
        # 发送数据长度和类型
        header = struct.pack('!I4s', len(data), data_type.encode('ascii')[:4])
        sock.sendall(header + data)
    
    @staticmethod
    def receive_data(sock: socket.socket) -> tuple:
        """接收数据"""
        # 接收头部信息
        header = sock.recv(CommunicationProtocol.HEADER_SIZE)
        if not header:
            return None, None
            
        data_len, data_type = struct.unpack('!I4s', header)
        data_type = data_type.decode('ascii').rstrip('\x00')
        
        # 接收数据
        received_data = b''
        while len(received_data) < data_len:
            chunk = sock.recv(min(4096, data_len - len(received_data)))
            if not chunk:
                break
            received_data += chunk
        
        if data_type == "json":
            received_data = json.loads(received_data.decode(CommunicationProtocol.ENCODING))
        
        return received_data, data_type
