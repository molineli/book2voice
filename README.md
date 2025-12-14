### 如何在本地运行

1.  **创建项目文件夹**，将上述代码按目录结构保存。
2.  **创建虚拟环境并安装依赖**：
    ```bash
    python -m venv venv
    # Windows 激活:
    venv\Scripts\activate
    # Mac/Linux 激活:
    source venv/bin/activate
    
    pip install -r requirements.txt
    ```
3.  **运行程序**：
    ```bash
    streamlit run app.py