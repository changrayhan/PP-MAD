# client/client.py
import socket
import numpy as np
import tenseal as ts
from PIL import Image
import torchvision.transforms as transforms
from .encryption import HomomorphicEncryption
from shared.communication import CommunicationProtocol
from server.model import WideResNet101FeatureExtractor  # 导入特征提取器
import logging
import json

class MedicalAIClient:
    def __init__(self, server_host='localhost', server_port=8888):
        self.server_host = server_host
        self.server_port = server_port
        self.encryption = HomomorphicEncryption()
        self.feature_extractor = WideResNet101FeatureExtractor()  # 初始化特征提取器
        self.pca_components = None  # 存储PCA组件
        self.pca_mean = None  # 存储PCA均值
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
    
    def get_pca_parameters(self):
        """从服务器获取PCA参数"""
        try:
            message = {'type': 'get_pca_params'}
            CommunicationProtocol.send_data(self.socket, message, "json")
            
            response, _ = CommunicationProtocol.receive_data(self.socket)
            if response and response.get('status') == 'success':
                self.pca_components = np.array(response['pca_components'])
                self.pca_mean = np.array(response['pca_mean'])
                self.logger.info("成功获取PCA参数")
                return True
            else:
                self.logger.error(f"获取PCA参数失败: {response.get('message', '未知错误')}")
                return False
        except Exception as e:
            self.logger.error(f"获取PCA参数时出错: {e}")
            return False
    
    def process_image(self, image_path):
        """处理图像并发送加密特征"""
        try:
            # 检查是否已获取PCA参数
            if self.pca_components is None or self.pca_mean is None:
                if not self.get_pca_parameters():
                    self.logger.error("无法获取PCA参数，无法继续处理")
                    return None
            
            # 图像预处理
            preprocess = transforms.Compose([
                transforms.Resize((224, 224)),  # WideResNet默认输入尺寸
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],  # ImageNet均值
                    std=[0.229, 0.224, 0.225]   # ImageNet标准差
                )
            ])
            
            # 加载并预处理图像
            image = Image.open(image_path).convert('RGB')
            image_tensor = preprocess(image)
            
            # 使用WideResNet101提取真实特征
            features = self.feature_extractor.extract_features(image_tensor)
            
            # 在客户端进行PCA降维（明文状态）
            self.logger.info("在客户端进行PCA降维")
            reduced_features = features.dot(self.pca_components.T) + self.pca_mean
            
            # 加密降维后的特征
            encrypted_features = self.encryption.encrypt_features(reduced_features)
            
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
