# client/encryption.py
import tenseal as ts
import numpy as np
import logging

class HomomorphicEncryption:
    """同态加密处理类"""
    
    def __init__(self):
        self.context = None
        self.public_key = None
        self.private_key = None
        
    def generate_keys(self, poly_modulus_degree=8192, coeff_mod_bit_sizes=[60, 40, 40, 60]):
        """生成同态加密密钥对"""
        # 创建CKKS上下文
        self.context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=poly_modulus_degree,
            coeff_mod_bit_sizes=coeff_mod_bit_sizes
        )
        
        # 设置全局尺度
        self.context.global_scale = 2**40
        self.context.generate_galois_keys()
        
        # 获取密钥
        self.private_key = self.context.secret_key()
        self.public_key = self.context
        
        logging.info("同态加密密钥对生成完成")
        return self.context.serialize()
    
    def encrypt_features(self, features: np.ndarray) -> bytes:
        """加密特征向量"""
        if self.context is None:
            raise RuntimeError("加密上下文未初始化")
            
        # 确保特征数据是浮点数
        features = features.astype(np.float64)
        encrypted_vector = ts.ckks_vector(self.context, features)
        return encrypted_vector.serialize()
    
    def decrypt_result(self, encrypted_data: bytes) -> np.ndarray:
        """解密密文结果"""
        if self.context is None:
            raise RuntimeError("加密上下文未初始化")
            
        encrypted_vector = ts.ckks_vector_from(self.context, encrypted_data)
        return np.array(encrypted_vector.decrypt())