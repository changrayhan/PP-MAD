# server/model.py
import torch
import torch.nn as nn
import torchvision.models as models
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.decomposition import PCA
import logging

class WideResNet101FeatureExtractor:
    """WideResNet101特征提取器"""
    
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self._load_model()
        self.features = {}
        
    def _load_model(self):
        """加载预训练的WideResNet101模型"""
        model = models.wide_resnet101_2(pretrained=True)
        model.fc = nn.Identity()  # 移除最后的全连接层
        model = model.to(self.device)
        model.eval()
        return model
    
    def extract_features(self, image_tensor: torch.Tensor) -> np.ndarray:
        """提取图像特征"""
        with torch.no_grad():
            if image_tensor.dim() == 3:
                image_tensor = image_tensor.unsqueeze(0)
            image_tensor = image_tensor.to(self.device)
            features = self.model(image_tensor)
            return features.cpu().numpy().flatten()

class PaDimModel:
    """PaDim异常检测模型"""
    
    def __init__(self, n_components=10, random_state=42):
        self.gmm = GaussianMixture(
            n_components=n_components, 
            random_state=random_state,
            covariance_type='full'
        )
        self.pca = PCA(n_components=100, random_state=random_state)
        self.is_fitted = False
        self.normal_features = []
        
    def fit(self, features_list):
        """训练GMM模型"""
        if not features_list:
            raise ValueError("特征列表为空")
            
        # 使用PCA降维
        reduced_features = self.pca.fit_transform(features_list)
        self.gmm.fit(reduced_features)
        self.is_fitted = True
        self.normal_features = reduced_features
        
    def calculate_mahalanobis_distance(self, feature: np.ndarray) -> float:
        """计算马氏距离（简化版）"""
        if not self.is_fitted:
            raise RuntimeError("模型尚未训练")
            
        # 降维
        reduced_feature = self.pca.transform(feature.reshape(1, -1))
        
        # 计算到每个高斯分布中心的距离
        distances = []
        for mean, cov in zip(self.gmm.means_, self.gmm.covariances_):
            diff = reduced_feature - mean
            try:
                inv_cov = np.linalg.pinv(cov)
                distance = np.sqrt(diff.dot(inv_cov).dot(diff.T))
                distances.append(distance[0, 0])
            except np.linalg.LinAlgError:
                # 如果协方差矩阵奇异，使用欧氏距离
                distance = np.linalg.norm(diff)
                distances.append(distance)
                
        return min(distances)