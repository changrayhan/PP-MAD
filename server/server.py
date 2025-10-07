# server/server.py
import socket
import threading
import numpy as np
import tenseal as ts
from .model import WideResNet101FeatureExtractor, PaDimModel
from shared.communication import CommunicationProtocol
import logging

class MedicalAIServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.feature_extractor = WideResNet101FeatureExtractor()
        self.padim_model = PaDimModel()
        self.normal_features = []
        self.context = None
        self.preprocess = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_tenseal_context(self, context_bytes):
        """设置TenSEAL上下文"""
        self.context = ts.context_from(context_bytes)
        self.logger.info("TenSEAL上下文设置完成")
    
    def train_normal_model(self, image_paths):
        """训练正常样本模型"""
        self.logger.info("开始训练正常样本模型...")
        
        for path in image_paths:
            try:
                # 加载并预处理图像
                image = Image.open(path).convert('RGB')
                image_tensor = self.preprocess(image)
                
                # 使用特征提取器提取真实特征（替换随机特征）
                features = self.feature_extractor.extract_features(image_tensor)
                self.normal_features.append(features)
            except Exception as e:
                self.logger.error(f"处理图像 {path} 时出错: {e}")
        
        if self.normal_features:
            self.padim_model.fit(self.normal_features)
            self.logger.info(f"模型训练完成，共处理 {len(self.normal_features)} 个样本")
        else:
            self.logger.warning("没有有效的训练数据")
    
    def process_encrypted_features(self, encrypted_features):
        """处理加密的特征"""
        if not self.context or not self.padim_model.is_fitted:
            raise RuntimeError("服务器未就绪")
        
        # 这里实现加密状态下的特征比对
        # 由于同态加密计算复杂，这里返回模拟结果
        encrypted_result = ts.ckks_vector(self.context, [0.5, 0.3, 0.8])
        return encrypted_result.serialize()
    
    def handle_client(self, client_socket, address):
        """处理客户端连接"""
        self.logger.info(f"处理来自 {address} 的连接")
        
        try:
            while True:
                # 接收数据
                data, data_type = CommunicationProtocol.receive_data(client_socket)
                if data is None:
                    break
                
                if data_type == "json":
                    if data.get('type') == 'public_key':
                        self.setup_tenseal_context(data['context'])
                        response = {'status': 'success', 'message': '公钥接收成功'}
                        CommunicationProtocol.send_data(client_socket, response, "json")
                    
                    elif data.get('type') == 'encrypted_features':
                        encrypted_result = self.process_encrypted_features(data['features'])
                        response = {
                            'status': 'success', 
                            'encrypted_result': encrypted_result
                        }
                        CommunicationProtocol.send_data(client_socket, response, "json")
                        
        except Exception as e:
            self.logger.error(f"处理客户端 {address} 时出错: {e}")
        finally:
            client_socket.close()
    
    def start_server(self):
        """启动服务器"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            self.logger.info(f"服务器启动在 {self.host}:{self.port}")
            
            while True:
                client_socket, address = server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except Exception as e:
            self.logger.error(f"服务器错误: {e}")
        finally:
            server_socket.close()
