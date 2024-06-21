import subprocess

# 定义要运行的 Streamlit 命令
command = ["streamlit", "run", "Home.py"]

# 使用 subprocess 运行命令
process = subprocess.Popen(command)

# 等待 Streamlit 进程结束
process.wait()