#!/usr/bin/env python3
"""
个人记账本系统 - 主程序入口
"""
import sys
import os
from pathlib import Path
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.main_window import MainWindow


def main():
    """主函数"""
    # 创建QApplication实例
    app = QApplication(sys.argv)
    # 配置基础日志（如果调用方未配置）
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    
    # 设置应用程序信息
    app.setApplicationName("个人记账本系统")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("PersonalAccounting")
    app.setOrganizationDomain("personal-accounting.com")
    
    # 注意：在较新版本的PySide6中，高DPI缩放已默认启用，无需手动设置
    # app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    # app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    try:
        # 创建主窗口
        window = MainWindow()
        
        # 显示窗口
        window.show()
        
        # 运行应用程序
        sys.exit(app.exec())
        
    except Exception as e:
        logging.getLogger(__name__).exception("应用程序启动失败: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()