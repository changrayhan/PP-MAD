# client/client_ui.py
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QWidget, QTextEdit, QPushButton, QLabel, QProgressBar,
                           QFileDialog, QFrame, QSplitter, QGroupBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QDateTime
from PyQt6.QtGui import QFont, QPixmap
import sys
import os
import numpy as np

# 添加路径以便导入本地模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class ClientThread(QThread):
    """客户端处理线程"""
    log_signal = pyqtSignal(str)
    result_signal = pyqtSignal(dict)
    progress_signal = pyqtSignal(int)
    
    def __init__(self, client, image_path):
        super().__init__()
        self.client = client
        self.image_path = image_path
    
    def run(self):
        self.log_signal.emit("开始处理图像...")
        
        try:
            # 连接服务器
            if not self.client.connect_to_server():
                self.log_signal.emit("连接服务器失败")
                return
                
            self.progress_signal.emit(25)
            
            # 发送公钥
            if not self.client.send_public_key():
                self.log_signal.emit("发送公钥失败")
                return
                
            self.progress_signal.emit(50)
            self.log_signal.emit("公钥发送成功")
            
            # 处理图像
            result = self.client.process_image(self.image_path)
            self.progress_signal.emit(75)
            
            if result is not None:
                # 模拟异常检测结果
                anomaly_score = float(np.mean(result))
                is_anomaly = anomaly_score > 0.5
                
                self.result_signal.emit({
                    'anomaly_score': anomaly_score,
                    'is_anomaly': is_anomaly,
                    'image_path': self.image_path
                })
                self.log_signal.emit(f"异常检测完成，分数: {anomaly_score:.3f}")
            else:
                self.log_signal.emit("图像处理失败")
                
            self.progress_signal.emit(100)
            self.client.close_connection()
        except Exception as e:
            self.log_signal.emit(f"处理过程中出错: {str(e)}")

class ClientUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = None
        self.current_image = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("医学影像异常检测系统 - 客户端")
        self.setGeometry(100, 100, 1200, 800)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧面板
        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.Shape.StyledPanel)
        left_layout = QVBoxLayout(left_frame)
        
        # 标题
        title_label = QLabel("客户端控制面板")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        left_layout.addWidget(title_label)
        
        # 服务器连接
        server_group = QGroupBox("服务器连接")
        server_layout = QVBoxLayout(server_group)
        
        self.connect_btn = QPushButton("连接服务器")
        self.connect_btn.clicked.connect(self.connect_server)
        server_layout.addWidget(self.connect_btn)
        
        self.connection_status = QLabel("未连接")
        server_layout.addWidget(self.connection_status)
        
        left_layout.addWidget(server_group)
        
        # 图像处理
        image_group = QGroupBox("图像处理")
        image_layout = QVBoxLayout(image_group)
        
        self.select_btn = QPushButton("选择图像")
        self.select_btn.clicked.connect(self.select_image)
        self.select_btn.setEnabled(False)
        image_layout.addWidget(self.select_btn)
        
        self.process_btn = QPushButton("开始检测")
        self.process_btn.clicked.connect(self.process_image)
        self.process_btn.setEnabled(False)
        image_layout.addWidget(self.process_btn)
        
        # 图像预览
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(300, 300)
        self.image_label.setStyleSheet("border: 1px solid gray;")
        self.image_label.setText("无图像")
        image_layout.addWidget(self.image_label)
        
        left_layout.addWidget(image_group)
        
        # 结果显示
        result_group = QGroupBox("检测结果")
        result_layout = QVBoxLayout(result_group)
        
        self.result_label = QLabel("等待检测...")
        self.result_label.setFont(QFont("Arial", 12))
        result_layout.addWidget(self.result_label)
        
        self.score_label = QLabel("异常分数: -")
        result_layout.addWidget(self.score_label)
        
        left_layout.addWidget(result_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        left_layout.addWidget(self.progress_bar)
        
        left_layout.addStretch()
        
        # 右侧日志面板
        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.Shape.StyledPanel)
        right_layout = QVBoxLayout(right_frame)
        
        right_layout.addWidget(QLabel("处理日志:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        right_layout.addWidget(self.log_text)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_frame)
        splitter.addWidget(right_frame)
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)
        
    def connect_server(self):
        """连接服务器"""
        try:
            from client.client import MedicalAIClient
            
            self.client = MedicalAIClient()
            # 实际执行连接操作并检查结果
            if self.client.connect_to_server():
                self.connect_btn.setEnabled(False)
                self.select_btn.setEnabled(True)
                self.connection_status.setText("已连接")
                self.log_message("服务器连接成功")
            else:
                self.connection_status.setText("连接失败")
                self.log_message("服务器连接失败: 无法建立网络连接")
                self.client = None  # 连接失败则清除客户端对象
        except Exception as e:
            self.log_message(f"连接服务器失败: {str(e)}")
            self.connection_status.setText("连接出错")
        
    def select_image(self):
        """选择图像"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择医学影像", "", 
            "Image Files (*.png *.jpg *.jpeg *.tif *.tiff)"
        )
        
        if file_path:
            self.current_image = file_path
            # 显示图像预览
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio)
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("图像加载失败")
                self.current_image = None
                return
                
            self.process_btn.setEnabled(True)
            self.log_message(f"已选择图像: {file_path}")
            
    def process_image(self):
        """处理图像"""
        if self.client and self.current_image:
            self.process_btn.setEnabled(False)
            
            # 启动处理线程
            self.client_thread = ClientThread(self.client, self.current_image)
            self.client_thread.log_signal.connect(self.log_message)
            self.client_thread.result_signal.connect(self.show_result)
            self.client_thread.progress_signal.connect(self.progress_bar.setValue)
            self.client_thread.start()
            
    def show_result(self, result):
        """显示检测结果"""
        score = result['anomaly_score']
        is_anomaly = result['is_anomaly']
        
        self.score_label.setText(f"异常分数: {score:.3f}")
        
        if is_anomaly:
            self.result_label.setText("检测结果: ❌ 异常")
            self.result_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.result_label.setText("检测结果: ✅ 正常")
            self.result_label.setStyleSheet("color: green; font-weight: bold;")
            
        self.process_btn.setEnabled(True)
        
    def log_message(self, message):
        """记录日志消息"""
        self.log_text.append(f"[{QDateTime.currentDateTime().toString()}] {message}")

def main():
    app = QApplication(sys.argv)
    
    # 应用Material Design样式
    try:
        from qt_material import apply_stylesheet
        apply_stylesheet(app, theme='dark_teal.xml')
    except ImportError:
        print("qt-material未安装，使用默认样式")
    
    window = ClientUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
