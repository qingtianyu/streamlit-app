# 使用官方的 Python 基础镜像
FROM python:3.11.4

# 设置工作目录
WORKDIR /app

# 复制当前目录的内容到工作目录
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 定义环境变量
ENV DATABASE_NAME=village
ENV ENGINE_HOST=http://localhost:8095

# 暴露 Streamlit 默认的运行端口
EXPOSE 8501

# 运行 Streamlit 应用
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
