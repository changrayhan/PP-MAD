# main_client.py - 修改版
import sys
import os
import subprocess

def check_qt_dependencies():
    """检查Qt依赖是否完整"""
    required_libs = [
        'libxcb-cursor0', 'libxcb-xinerama0', 'libxcb-randr0',
        'libxcb-icccm4', 'libxcb-image0', 'libxcb-keysyms1'
    ]
    
    missing = []
    for lib in required_libs:
        try:
            result = subprocess.run(['dpkg', '-l', lib], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                missing.append(lib)
        except:
            missing.append(lib)
    
    return missing

def main():
    # 设置环境变量
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    os.environ['QT_DEBUG_PLUGINS'] = '0'
    
    # 检查依赖
    missing_libs = check_qt_dependencies()
    if missing_libs:
        print("缺少必要的Qt依赖库:")
        for lib in missing_libs:
            print(f"  - {lib}")
        print("\n请运行以下命令安装:")
        print("sudo apt update && sudo apt install -y " + " ".join(missing_libs))
        return 1
    
    # 添加项目路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    
    try:
        from client.client_ui import main as client_main
        client_main()
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保所有依赖已正确安装")
        return 1
    except Exception as e:
        print(f"启动错误: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())