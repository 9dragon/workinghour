"""
应用启动入口
"""
import os
from app import create_app
from config import Config

# 确保必要的目录存在
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs('backups', exist_ok=True)
os.makedirs('instance', exist_ok=True)

app = create_app()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=True
    )
