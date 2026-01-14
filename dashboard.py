# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import time
import subprocess
import os
import shutil

# --- CẤU HÌNH (SỬA LẠI TÊN POD CỦA BẠN NẾU KHÁC) ---
# NAMENODE_POD = "namenode-67b855c45b-vqr2c" 
# HDFS_PATH = "/data/air_quality_v2"           # Đường dẫn file trong HDFS
# POD_TEMP_PATH = "/tmp/export_data"           # Đường dẫn tạm trong Pod
# LOCAL_DATA_PATH = "temp_data_air_quality"    # Đường dẫn trên Windows (dùng đường dẫn tương đối)

# st.set_page_config(page_title="Air Quality Monitor", layout="wide")
# st.title("🏭 Real-time Air Quality Dashboard (Windows Version)")

CONTAINER_KEYWORD = "namenode"               # Từ khóa để tìm container (thường là 'namenode')
HDFS_PATH = "/data/air_quality_v2"           # Đường dẫn file trong HDFS
DOCKER_TEMP_PATH = "/tmp/export_data"        # Đường dẫn tạm TRONG container
LOCAL_DATA_PATH = "temp_data_air_quality"    # Đường dẫn trên Windows

st.set_page_config(page_title="Air Quality Monitor", layout="wide")
st.title("🏭 Real-time Air Quality Dashboard (Docker Version)")

def get_docker_container_id():
    """
    Tìm ID của container dựa trên tên.
    Ví dụ: tìm container có tên chứa 'namenode'.
    """
    try:
        # Liệt kê các container đang chạy: ID và Names
        cmd = "docker ps --format \"{{.ID}} {{.Names}}\""
        
        # Lưu ý: Cần thêm encoding='utf-8' để tránh lỗi ký tự lạ trên Windows
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode != 0:
            return None
        
        # Duyệt qua từng dòng để tìm container namenode
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if CONTAINER_KEYWORD in line:
                # Trả về ID (phần đầu tiên của dòng)
                return line.split(' ')[0]
        return None
    except Exception as e:
        print(f"Lỗi tìm container: {e}")
        return None

# --- HÀM ĐỒNG BỘ DỮ LIỆU ---
def sync_data_windows():
    status_text.text("🔍 Đang tìm Docker Container...")
    
    # 1. Tìm Container ID tự động
    container_id = get_docker_container_id()
    
    if not container_id:
        status_text.error("❌ Không tìm thấy Container 'namenode'.")
        st.error("Hãy kiểm tra lại: Bạn đã chạy 'docker-compose up' chưa? Tên container có chứa chữ 'namenode' không?")
        return False
        
    status_text.text(f"🔗 Đã kết nối tới Container ID: {container_id}")
    time.sleep(0.5) 

    # Tạo folder trên Windows nếu chưa có
    if not os.path.exists(LOCAL_DATA_PATH):
        os.makedirs(LOCAL_DATA_PATH)

    try:
        # BƯỚC 1: Dọn dẹp thư mục tạm bên trong Container
        # docker exec <id> rm -rf <path>
        cmd_clean = f"docker exec {container_id} rm -rf {DOCKER_TEMP_PATH}"
        subprocess.run(cmd_clean, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # BƯỚC 2: Copy từ HDFS ra thư mục tạm của Container (Local Filesystem của Container)
        status_text.text("⬇️ Đang trích xuất dữ liệu từ HDFS...")
        
        # Lệnh hdfs dfs -copyToLocal
        cmd_export = f"docker exec {container_id} hdfs dfs -copyToLocal {HDFS_PATH} {DOCKER_TEMP_PATH}"
        result_export = subprocess.run(cmd_export, shell=True, capture_output=True, text=True, encoding='utf-8')
        
        if result_export.returncode != 0:
            # Đôi khi lỗi do folder đã tồn tại hoặc không tìm thấy lệnh hdfs
            st.error(f"Lỗi lệnh HDFS trong Docker: {result_export.stderr}")
            return False

        # BƯỚC 3: Copy từ Container về Windows
        status_text.text("📦 Đang tải về máy Windows...")
        
        # Xóa file cũ trên Windows trước khi copy mới
        for f in os.listdir(LOCAL_DATA_PATH):
            file_path = os.path.join(LOCAL_DATA_PATH, f)
            try:
                if os.path.isfile(file_path): os.unlink(file_path)
            except Exception: pass

        # Lệnh docker cp <container_id>:<path_container> <path_windows>
        cmd_cp = f"docker cp {container_id}:{DOCKER_TEMP_PATH} {LOCAL_DATA_PATH}"
        subprocess.run(cmd_cp, shell=True, check=True)
        
        status_text.success(f"✅ Đã lấy dữ liệu thành công từ Container {container_id}!")
        return True

    except subprocess.CalledProcessError as e:
        status_text.error("❌ Lỗi khi copy file (docker cp). Kiểm tra quyền truy cập.")
        return False
    except Exception as e:
        status_text.error(f"❌ Có lỗi xảy ra: {str(e)}")
        return False
# --- HÀM ĐỒNG BỘ DỮ LIỆU ---
# def sync_data_windows():
#     status_text.text("🔄 Đang kết nối Kubernetes...")
    
#     # Tạo folder trên Windows nếu chưa có
#     if not os.path.exists(LOCAL_DATA_PATH):
#         os.makedirs(LOCAL_DATA_PATH)

#     try:
#         # BƯỚC 1: Dọn dẹp thư mục tạm bên trong Pod (Gửi lệnh Linux vào Pod)
#         # Windows gửi lệnh -> Pod thực thi lệnh 'rm -rf'
#         cmd_clean = f"kubectl exec {NAMENODE_POD} -- rm -rf {POD_TEMP_PATH}"
#         subprocess.run(cmd_clean, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

#         # BƯỚC 2: Lấy dữ liệu từ HDFS ra thư mục thường trong Pod
#         # Lệnh này bắt Pod chép dữ liệu từ hệ thống ảo HDFS ra ổ đĩa của Pod
#         status_text.text("⬇️ Đang trích xuất dữ liệu từ HDFS...")
#         cmd_export = f"kubectl exec {NAMENODE_POD} -- hdfs dfs -copyToLocal {HDFS_PATH} {POD_TEMP_PATH}"
#         result_export = subprocess.run(cmd_export, shell=True, capture_output=True, text=True)
        
#         if result_export.returncode != 0:
#             # Nếu lỗi, in ra để debug
#             st.error(f"Lỗi khi trích xuất HDFS: {result_export.stderr}")
#             return False

#         # BƯỚC 3: Copy từ Pod về Windows
#         status_text.text("📦 Đang tải về máy Windows...")
#         # Lưu ý: Windows dùng đường dẫn ngược (\) nhưng kubectl dùng xuôi (/)
#         # cmd_cp = f"kubectl cp {NAMENODE_POD}:{POD_TEMP_PATH} {LOCAL_DATA_PATH}"
        
#         # Cách an toàn nhất trên Windows: Dùng subprocess gọi trực tiếp
#         subprocess.run(f"kubectl cp {NAMENODE_POD}:{POD_TEMP_PATH} {LOCAL_DATA_PATH}", shell=True, check=True)
        
#         status_text.success("✅ Đã lấy dữ liệu thành công!")
#         return True

#     except Exception as e:
#         status_text.error(f"❌ Có lỗi xảy ra: {str(e)}")
#         return False

# --- HÀM ĐỌC DỮ LIỆU ---
@st.cache_data(ttl=5) # Giảm cache xuống 5s để cập nhật nhanh hơn
def load_data():
    all_files = []
    # Quét tìm file parquet (bỏ qua các file hệ thống)
    for root, dirs, files in os.walk(LOCAL_DATA_PATH):
        for file in files:
            if file.endswith(".parquet") and not file.startswith("."):
                all_files.append(os.path.join(root, file))
    
    if not all_files:
        return pd.DataFrame()

    try:
        df_list = [pd.read_parquet(f) for f in all_files]
        if not df_list: return pd.DataFrame()
        
        full_df = pd.concat(df_list, ignore_index=True)
        
        if 'processed_time' in full_df.columns:
            full_df['processed_time'] = pd.to_datetime(full_df['processed_time'])
            full_df = full_df.sort_values(by='processed_time', ascending=False)
            
        return full_df
    except Exception as e:
        return pd.DataFrame()

# --- GIAO DIỆN ---

col1, col2 = st.columns([1, 5])
with col1:
    if st.button('🔄 Cập nhật ngay'):
        st.cache_data.clear()
        st.rerun()

with col2:
    status_text = st.empty()

# Chạy đồng bộ
if sync_data_windows():
    df = load_data()
    
    if not df.empty:
        # Lấy dòng mới nhất
        latest = df.iloc[0]
        
        st.markdown("### 📊 Chỉ số không khí (Real-time)")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("AQI", f"{latest.get('aqi', 0)}")
        m2.metric("PM2.5", f"{latest.get('pm2_5', 0):.1f}")
        m3.metric("CO", f"{latest.get('co', 0):.1f}")
        m4.metric("Thời gian", str(latest.get('processed_time', ''))[11:19])

        st.line_chart(df.set_index('processed_time')[['aqi', 'pm2_5']])
        
        with st.expander("Xem bảng dữ liệu"):
            st.dataframe(df.head(20))
    else:
        st.warning("Đã tải thư mục về nhưng chưa thấy file .parquet. Có thể Spark chưa kịp ghi file.")

from streamlit_autorefresh import st_autorefresh

# Auto refresh UI mỗi 15s (KHÔNG BLOCK)
st_autorefresh(interval=15000, key="refresh")

# Session state
if "last_sync" not in st.session_state:
    st.session_state.last_sync = 0

# Chỉ sync mỗi 60s
if time.time() - st.session_state.last_sync > 60:
    sync_data_windows()
    st.session_state.last_sync = time.time()

df = load_data()