# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import time
import subprocess
import os
import plotly.express as px
import plotly.graph_objects as go

# --- CẤU HÌNH ---
CONTAINER_KEYWORD = "namenode"
HDFS_PATH = "/data/air_quality_v2"
DOCKER_TEMP_PATH = "/tmp/export_data"
LOCAL_DATA_PATH = "temp_data_air_quality"

st.set_page_config(
    page_title="Air Quality Monitor",
    layout="wide",
    page_icon="🏭",
    initial_sidebar_state="collapsed"
)


st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stMetric {
        background-color: #0E1117;
        border: 1px solid #262730;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏭 Real-time Air Quality Dashboard")

# --- HÀM HỖ TRỢ DOCKER (Giữ nguyên logic của bạn) ---
def get_docker_container_id():
    try:
        cmd = "docker ps --format \"{{.ID}} {{.Names}}\""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0: return None
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if CONTAINER_KEYWORD in line:
                return line.split(' ')[0]
        return None
    except Exception: return None

def sync_data_windows():
    container_id = get_docker_container_id()
    if not container_id: return False, "Không tìm thấy Container"

    if not os.path.exists(LOCAL_DATA_PATH): os.makedirs(LOCAL_DATA_PATH)

    try:
        # Dọn dẹp & Copy trong im lặng (không in log ra UI để tránh rối)
        subprocess.run(f"docker exec {container_id} rm -rf {DOCKER_TEMP_PATH}", shell=True)
        subprocess.run(f"docker exec {container_id} hdfs dfs -copyToLocal {HDFS_PATH} {DOCKER_TEMP_PATH}", shell=True)
        
        # Xóa file cũ local
        for f in os.listdir(LOCAL_DATA_PATH):
            try: os.unlink(os.path.join(LOCAL_DATA_PATH, f))
            except: pass
            
        # Copy về
        subprocess.run(f"docker cp {container_id}:{DOCKER_TEMP_PATH} {LOCAL_DATA_PATH}", shell=True, check=True)
        return True, "Đã đồng bộ"
    except Exception as e:
        return False, str(e)

# --- HÀM LOAD DATA ---
def load_data():
    all_files = []
    for root, dirs, files in os.walk(LOCAL_DATA_PATH):
        for file in files:
            if file.endswith(".parquet") and not file.startswith("."):
                all_files.append(os.path.join(root, file))
    
    if not all_files: return pd.DataFrame()

    try:
        df_list = [pd.read_parquet(f) for f in all_files]
        if not df_list: return pd.DataFrame()
        full_df = pd.concat(df_list, ignore_index=True)
        
        if 'processed_time' in full_df.columns:
            full_df['processed_time'] = pd.to_datetime(full_df['processed_time'])
            full_df = full_df.sort_values(by='processed_time') # Sắp xếp tăng dần theo thời gian để vẽ biểu đồ
            
        return full_df
    except Exception: return pd.DataFrame()

# --- KHU VỰC HIỂN THỊ CHÍNH ---

# Tạo 2 placeholder cố định: 1 cho thông báo trạng thái nhỏ, 1 cho nội dung chính
status_placeholder = st.empty()
main_placeholder = st.empty()

# Vòng lặp cập nhật liên tục (Thay thế cho st_autorefresh)
while True:
    # 1. Đồng bộ dữ liệu
    success, msg = sync_data_windows()
    
    # Cập nhật trạng thái nhỏ gọn
    if success:
        status_placeholder.markdown(f"<p style='color:green; font-size:12px'>🟢 System Status: Connected | {msg} | Last update: {time.strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)
    else:
        status_placeholder.markdown(f"<p style='color:red; font-size:12px'>🔴 System Status: Disconnected | {msg}</p>", unsafe_allow_html=True)

    # 2. Đọc dữ liệu
    df = load_data()

    # 3. Vẽ giao diện vào main_placeholder
    with main_placeholder.container():
        if not df.empty:
            # Lấy dữ liệu mới nhất
            latest = df.iloc[-1] # Lấy dòng cuối cùng (mới nhất theo thời gian)
            
            # --- PHẦN METRIC (Thẻ chỉ số) ---
            m1, m2, m3, m4 = st.columns(4)
            
            # Tô màu chỉ số dựa trên mức độ nguy hại (Ví dụ đơn giản)
            aqi_val = latest.get('aqi', 0)
            aqi_delta = aqi_val - df.iloc[-2]['aqi'] if len(df) > 1 else 0
            
            m1.metric("AQI (Chất lượng)", f"{aqi_val}", f"{aqi_delta:.1f}", delta_color="inverse")
            m2.metric("PM2.5 (Bụi mịn)", f"{latest.get('pm2_5', 0):.1f} µg/m³")
            m3.metric("CO (Khí thải)", f"{latest.get('co', 0):.1f} ppm")
            m4.metric("Cập nhật lúc", str(latest.get('processed_time', ''))[11:19])

            # --- PHẦN BIỂU ĐỒ (PLOTLY) ---
            st.markdown("---")
            
            # Biểu đồ kết hợp AQI và PM2.5
            fig = go.Figure()

            # Đường AQI (Vùng màu đỏ nhạt)
            fig.add_trace(go.Scatter(
                x=df['processed_time'], 
                y=df['aqi'],
                mode='lines',
                name='AQI',
                line=dict(width=3, color='#FF4B4B', shape='spline'), # shape='spline' làm đường cong mềm
                fill='tozeroy', # Tô màu dưới đường
                fillcolor='rgba(255, 75, 75, 0.1)'
            ))

            # Đường PM2.5 (Vùng màu xanh nhạt)
            fig.add_trace(go.Scatter(
                x=df['processed_time'], 
                y=df['pm2_5'],
                mode='lines',
                name='PM2.5',
                line=dict(width=3, color='#00CC96', shape='spline'),
                fill='tozeroy',
                fillcolor='rgba(0, 204, 150, 0.1)'
            ))

            # Tinh chỉnh giao diện biểu đồ
            fig.update_layout(
                title="📈 Diễn biến chất lượng không khí theo thời gian thực",
                xaxis_title="Thời gian",
                yaxis_title="Giá trị",
                template="plotly_dark", # Giao diện tối chuyên nghiệp
                hovermode="x unified",  # Hiển thị tooltip gộp
                height=450,
                margin=dict(l=0, r=0, t=40, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig, use_container_width=True, key=f"chart_{time.time()}") # Key unique để tránh lỗi render
            
            # Hiển thị bảng dữ liệu (chỉ hiện 5 dòng cuối)
            with st.expander("Show Raw Data (Last 5 records)"):
                st.dataframe(df.tail(5).sort_values(by='processed_time', ascending=False), use_container_width=True)

        else:
            st.warning("⏳ Đang chờ dữ liệu từ Spark/Kafka... (Chưa có file parquet)")
            time.sleep(1) # Chờ 1 chút để không spam vòng lặp khi không có data

    # 4. Ngủ 5 giây rồi lặp lại (Thay đổi số này nếu muốn nhanh/chậm hơn)
    time.sleep(5)