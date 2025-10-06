# client/client.py
import socket
import numpy as np
import tenseal as ts
from .encryption import HomomorphicEncryption
from shared.communication import CommunicationProtocol
import logging
import json

class MedicalAIClient:
    def __init__(self, server_host='localhost', server_port=8888):
        self.server_host = server_host
        self.server_port = server_port
        self.encryption = HomomorphicEncryption()
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def connect_to_server(self):
        """连接到服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            self.logger.info(f"已连接到服务器 {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            self.logger.error(f"连接服务器失败: {e}")
            return False
    
    def send_public_key(self):
        """发送公钥到服务器"""
        try:
            # 生成密钥对
            context_bytes = self.encryption.generate_keys()
            
            # 发送公钥
            message = {
                'type': 'public_key',
                'context': context_bytes
            }
            CommunicationProtocol.send_data(self.socket, message, "json")
            
            # 等待响应
            response, _ = CommunicationProtocol.receive_data(self.socket)
            if response and response.get('status') == 'success':
                self.logger.info("公钥发送成功")
                return True
            else:
                self.logger.error("公钥发送失败")
                return False
                
        except Exception as e:
            self.logger.error(f"发送公钥时出错: {e}")
            return False
    
    def process_image(self, image_path):
        """处理图像并发送加密特征"""
        try:
            # 这里应该实现真实的特征提取
            # 暂时使用随机特征代替
            dummy_features = np.random.randn(2048).astype(np.float32)
            
            # 加密特征
            encrypted_features = self.encryption.encrypt_features(dummy_features)
            
            # 发送加密特征
            message = {
                'type': 'encrypted_features',
                'features': encrypted_features
            }
            CommunicationProtocol.send_data(self.socket, message, "json")
            
            # 接收结果
            response, _ = CommunicationProtocol.receive_data(self.socket)
            if response and response.get('status') == 'success':
                # 解密结果
                encrypted_result = response['encrypted_result']
                decrypted_result = self.encryption.decrypt_result(encrypted_result)
                
                self.logger.info(f"检测完成，结果: {decrypted_result}")
                return decrypted_result
            else:
                self.logger.error("处理失败")
                return None
                
        except Exception as e:
            self.logger.error(f"处理图像时出错: {e}")
            return None
    
    def close_connection(self):
        """关闭连接"""
        if hasattr(self, 'socket'):
            self.socket.close()
            self.logger.info("连接已关闭")