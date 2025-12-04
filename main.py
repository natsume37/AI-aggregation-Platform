"""
@File    : main.py
@Author  : Martin
@Time    : 2025/11/5 21:39
@Desc    :
"""

import uvicorn
from app.main import app

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8089)
