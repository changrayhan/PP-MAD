# server/server_ui.py
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QWidget, QTextEdit, QPushButton, QLabel, QProgressBar,
                           QFileDialog, QListWidget, QSplitter, QFrame)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QDateTime
from PyQt6.QtGui import QFont
import sys
import os

# 添加路径以便导入本地模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class ServerThread(QThread):
    """服务器线程"""
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    
    def __init__(self, server):
        super().__init__()
        self.server = server
    
    def run(self):
        self.log_signal.emit("服务器线程启动...")
        try:
            self.server.start_server()
        except Exception as e:
            self.log_signal.emit(f"服务器错误: {str(e)}")

class ServerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.server = None
        self.server_thread = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("医学影像异常检测系统 - 服务器")
        self.setGeometry(100, 100, 1000, 700)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧面板
        left_frame = QFrame()
        # 修复：使用正确的枚举值
        left_frame.setFrameShape(QFrame.Shape.StyledPanel)
        left_layout = QVBoxLayout(left_frame)
        
        # 标题
        title_label = QLabel("服务器控制面板")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        left_layout.addWidget(title_label)
        
        # 服务器控制按钮
        self.start_btn = QPushButton("启动服务器")
        self.start_btn.clicked.connect(self.start_server)
        left_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止服务器")
        self.stop_btn.clicked.connect(self.stop_server)
        self.stop_btn.setEnabled(False)
        left_layout.addWidget(self.stop_btn)
        
        # 训练数据选择
        train_btn = QPushButton("选择训练数据")
        train_btn.clicked.connect(self.select_training_data)
        left_layout.addWidget(train_btn)
        
        self.train_list = QListWidget()
        left_layout.addWidget(QLabel("训练数据文件:"))
        left_layout.addWidget(self.train_list)
        
        # 训练按钮
        self.train_btn = QPushButton("训练模型")
        self.train_btn.clicked.connect(self.train_model)
        self.train_btn.setEnabled(False)
        left_layout.addWidget(self.train_btn)
        
        # 状态显示
        left_layout.addWidget(QLabel("服务器状态:"))
        self.status_label = QLabel("未启动")
        left_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        left_layout.addWidget(self.progress_bar)
        
        left_layout.addStretch()
        
        # 右侧日志面板
        right_frame = QFrame()
        # 修复：使用正确的枚举值
        right_frame.setFrameShape(QFrame.Shape.StyledPanel)
        right_layout = QVBoxLayout(right_frame)
        
        right_layout.addWidget(QLabel("系统日志:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        right_layout.addWidget(self.log_text)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_frame)
        splitter.addWidget(right_frame)
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter)
        
    def start_server(self):
        """启动服务器"""
        try:
            from server.server import MedicalAIServer
            
            self.server = MedicalAIServer()
            self.server_thread = ServerThread(self.server)
            self.server_thread.log_signal.connect(self.log_message)
            self.server_thread.status_signal.connect(self.update_status)
            self.server_thread.start()
            
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("运行中")
            self.log_message("服务器启动成功")
        except Exception as e:
            self.log_message(f"启动服务器失败: {str(e)}")
        
    def stop_server(self):
        """停止服务器"""
        if self.server_thread and self.server_thread.isRunning():
            self.server_thread.terminate()
            self.server_thread.wait()
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("已停止")
        self.log_message("服务器已停止")
        
    def select_training_data(self):
        """选择训练数据"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择训练图像", "", 
            "Image Files (*.png *.jpg *.jpeg *.tif *.tiff)"
        )
        
        if files:
            self.train_list.clear()
            self.train_list.addItems(files)
            self.train_btn.setEnabled(True)
            self.log_message(f"已选择 {len(files)} 个训练文件")
            
    def train_model(self):
        """训练模型"""
        if self.server and self.train_list.count() > 0:
            file_paths = [self.train_list.item(i).text() 
                         for i in range(self.train_list.count())]
            self.server.train_normal_model(file_paths)
            self.log_message("模型训练完成")
            
    def log_message(self, message):
        """记录日志消息"""
        self.log_text.append(f"[{QDateTime.currentDateTime().toString()}] {message}")
        
    def update_status(self, status):
        """更新状态"""
        self.status_label.setText(status)

def main():
    app = QApplication(sys.argv)
    
    # 应用Material Design样式
    try:
        from qt_material import apply_stylesheet
        apply_stylesheet(app, theme='dark_teal.xml')
    except ImportError:
        print("qt-material未安装，使用默认样式")
    
    window = ServerUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()