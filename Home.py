import requests
import streamlit as st
import webbrowser
import time
import os

from pathlib import Path

# 获取环境变量
DATABASE_NAME = os.getenv('DATABASE_NAME')
ENGINE_HOST = os.getenv('ENGINE_HOST')

LOGO_PATH = Path(__file__).parent / "images" / "logo.png"
DEFAULT_DATABASE = DATABASE_NAME or 'village'

# 定义可用的模型列表
AVAILABLE_MODELS = ["gpt-4o", "gpt-3.5-turbo", "qwen-plus", "Qwen-72B-Chat"]

def get_all_database_connections(api_url):
    try:
        response = requests.get(api_url)
        response_data = response.json()
        return {entry["alias"]: entry["id"] for entry in response_data} if response.status_code == 200 else {}  # noqa: E501
    except requests.exceptions.RequestException:
        return {}

def add_database_connection(api_url, connection_data):
    try:
        response = requests.post(api_url, json=connection_data)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def answer_question(api_url, db_connection_id, question, llm_config):
    request_body = {
        "llm_config": {
            "llm_name": llm_config['llm_name']
        },
        "prompt": {
            "text": question,
            "db_connection_id": db_connection_id,
        }
    }
    try:
        with requests.post(api_url, json=request_body, stream=True) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=2048):
                if chunk:
                    response = chunk.decode("utf-8", "replace")
                    yield response + "\n"
                    time.sleep(0.1)
                    
    except requests.exceptions.RequestException as e:
        st.error(f"Connection failed due to {e}.")

def test_connection(url):
    try:
        response = requests.get(url)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def create_button_link(text, url):
    button_clicked = st.sidebar.button(text)
    if button_clicked:
        webbrowser.open_new_tab(url)

def find_key_by_value(dictionary, target_value):
    for key, value in dictionary.items():
        if value == target_value:
            return key
    return None


WAITING_TIME_TEXTS = [
    ":wave: Hello. Please, give me a few moments and I'll be back with your answer.",  # noqa: E501
]

INTRODUCTION_TEXT = """
This app is a proof of concept using the Dataherald NL-2-SQL engine using a streamlit front-end and a dataset of US real estate data.
The data available includes: rents, sales prices, listing prices, price per square foot, number of homes sold, inventory and number of pending sales up to June 2023.
"""  # noqa: E501
INTRO_EXAMPLE = """
查询示例：查询枫桥镇2024年所有村书记的任务签收及时率
"""

st.set_page_config(
    page_title="Dataherald",
    page_icon="./images/logo.png",
    layout="wide"
)

# Setup environment settings
st.sidebar.title("Dataherald")
st.sidebar.write("使用自然语言查询结构化数据库")
# 在侧边栏添加一个下拉框供用户选择模型
selected_model = st.sidebar.selectbox("选择模型", AVAILABLE_MODELS, index=0)

# 更新llm_config中的llm_name值
llm_config = {
    "llm_name": selected_model
}

# st.sidebar.write("Enable business users to get answers to ad hoc data questions in seconds.")  # noqa: E501
# st.sidebar.page_link("https://www.dataherald.com/", label="Visit our website", icon="🌐")
st.sidebar.subheader("连接引擎")
HOST = st.sidebar.text_input("引擎地址", value=ENGINE_HOST or "http://localhost:8095")
st.session_state["HOST"] = HOST
if st.sidebar.button("测试连接"):
    url = HOST + '/api/v1/heartbeat'
    if test_connection(url):
        st.sidebar.success("连接成功.")
    else:
        st.sidebar.error("连接失败.")

# Setup main page
st.image("images/dataherald.png", width=500)
if not test_connection(HOST + '/api/v1/heartbeat'):
    st.error("无法连接到引擎。")  # noqa: E501
    st.stop()
else:
    database_connections = get_all_database_connections(HOST + '/api/v1/database-connections')  # noqa: E501
    if st.session_state.get("database_connection_id", None) is None:
        st.session_state["database_connection_id"] = database_connections[DEFAULT_DATABASE]  # noqa: E501
    db_name = find_key_by_value(database_connections, st.session_state["database_connection_id"])  # noqa: E501
    st.warning(f"连接到【 {db_name} 】数据库.")
    # st.info(INTRODUCTION_TEXT)  # noqa: E501
    st.info(INTRO_EXAMPLE)

output_container = st.empty()
user_input = st.chat_input("提问")
output_container = output_container.container()
if user_input:
    output_container.chat_message("user").write(user_input)
    answer_container = output_container.chat_message("assistant")
    with st.spinner("Agent starts..."):
        st.write_stream(answer_question(HOST + '/api/v1/stream-sql-generation', st.session_state["database_connection_id"], user_input, llm_config))