import streamlit as st
import numpy as np
import plotly.graph_objects as ob
import time

# 페이지 설정
st.set_page_config(page_title="지구과학II 천구 시뮬레이터", layout="wide")

st.title("🌌 천체 좌표계 변환 및 관측 시뮬레이터")
st.markdown("** 적도 좌표계(적경, 적위)를 지평 좌표계(방위각, 고도)로 변환하고 일주운동을 시각화합니다.")

# --- 사이드바: 사용자 입력 컨트롤러 ---
st.sidebar.header("⚙️ 관측 및 천체 설정")

lat_deg = st.sidebar.slider("관측자 위도 (N)", min_value=0.0, max_value=90.0, value=37.5, step=0.5)
dec_deg = st.sidebar.slider("천체의 적위 (δ)", min_value=-90.0, max_value=90.0, value=20.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("⏰ 시간 및 재생 제어")

# 1. 세션 상태 변수들 변동 제어
if "lha_hour" not in st.session_state:
    st.session_state.lha_hour = 0.0
if "is_playing" not in st.session_state:
    st.session_state.is_playing = False

# 슬라이더: 사용자가 직접 바꿀 수도 있게 설정
lha_hour = st.sidebar.slider("지방시각 (Hour Angle)", min_value=0.0, max_value=24.0, value=st.session_state.lha_hour, step=0.1)
st.session_state.lha_hour = lha_hour

# 버튼 이벤트 처리
play_col1, play_col2 = st.sidebar.columns(2)
with play_col1:
    if st.button("▶️ 일주운동 재생"):
        st.session_state.is_playing = True
with play_col2:
    if st.button("⏱️ 정지/리셋"):
        st.session_state.is_playing = False
        st.session_state.lha_hour = 0.0
        st.rerun()

# 핵심: 재생 상태(is_playing)가 True이면 한 프레임(0.2시간)을 증가시키고 앱을 강제로 즉시 재실행(st.rerun)시킵니다.
if st.session_state.is_playing:
    time.sleep(0.05) # 프레임 속도 지연 (초)
    st.session_state.lha_hour = (st.session_state.lha_hour + 0.2) % 24.0
    st.rerun() # 이 함수가 호출되면 화면이 처음부터 다시 그려지며 바뀐 별 위치를 실시간 렌더링합니다.

# --- 좌표 변환 수학 연산 ---
phi = np.radians(lat_deg)
delta = np.radians(dec_deg)
H = np.radians(st.session_state.lha_hour * 15.0)

# 1. 고도(h) 계산
sin_alt = np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.cos(H)
sin_alt = np.clip(sin_alt, -1.0, 1.0)
alt_rad = np.arcsin(sin_alt)
alt_deg = np.degrees(alt_rad)

# 2. 방위각(A) 계산
cos_alt = np.cos(alt_rad)
if cos_alt == 0:
    az_deg = 0.0
else:
    cos_az = (np.sin(delta) - np.sin(phi) * sin_alt) / (np.cos(phi) * cos_alt)
    cos_az = np.clip(cos_az, -1.0, 1.0)
    az_rad = np.arccos(cos_az)
    az_deg = np.degrees(az_rad)
    if np.sin(H) > 0: 
        az_deg = 360.0 - az_deg

# --- 결과 디스플레이 ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 실시간 계산 결과")
    st.metric(label="현재 천체의 고도 (Altitude)", value=f"{alt_deg:.2f}°")
    st.metric(label="현재 천체의 방위각 (Azimuth)", value=f"{az_deg:.2f}° (북점 기준)")
    st.metric(label="현재 지방시각 (LHA)", value=f"{st.session_state.lha_hour:.2f}시")
    
    st.markdown("---")
    st.markdown("""
    ### 
    * `▶️ 일주운동 재생` 버튼을 누르면 시간이 자동으로 계속 흐릅니다.
    * 멈추거나 처음 상태로 돌리려면 `⏱️ 정지/리셋` 버튼을 누르세요.
    """)

# --- Plotly 3D 천구 시각화 ---
with col2:
    st.subheader("🔮 3D 천구 및 천체 위치")
    
    fig = ob.Figure()
    
    # 1. 지평선
    theta = np.linspace(0, 2*np.pi, 100)
    fig.add_trace(ob.Scatter3d(x=np.cos(theta), y=np.sin(theta), z=np.zeros(100),
                               mode='lines', line=dict(color='green', width=3), name='지평선'))
    
    # 2. 천구 가이드선
    for phi_g in np.linspace(0, np.pi/2, 5):
        fig.add_trace(ob.Scatter3d(x=np.cos(phi_g)*np.cos(theta), y=np.cos(phi_g)*np.sin(theta), z=np.sin(phi_g)*np.ones(100),
                                   mode='lines', line=dict(color='gray', width=1, dash='dash'), showlegend=False))
        
    # 3. 방위 표시
    fig.add_trace(ob.Scatter3d(x=[1, -1, 0, 0, 0], y=[0, 0, 1, -1, 0], z=[0, 0, 0, 0, 1],
                               mode='text', text=['N(북)', 'S(남)', 'E(동)', 'W(서)', 'Z(천정)'],
                               textfont=dict(size=14, color='black'), showlegend=False))

    # 4. 천체의 일주운동 전체 궤적 계산
    hours = np.linspace(0, 24, 100)
    traj_x, traj_y, traj_z = [], [], []
    for h_t in hours:
        H_t = np.radians(h_t * 15.0)
        sin_alt_t = np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.cos(H_t)
        alt_rad_t = np.arcsin(np.clip(sin_alt_t, -1.0, 1.0))
        
        cos_alt_t = np.cos(alt_rad_t)
        if cos_alt_t == 0: cos_az_t = 1.0
        else: cos_az_t = (np.sin(delta) - np.sin(phi) * sin_alt_t) / (np.cos(phi) * cos_alt_t)
        az_rad_t = np.arccos(np.clip(cos_az_t, -1.0, 1.0))
        if np.sin(H_t) > 0: az_rad_t = 2*np.pi - az_rad_t
        
        if alt_rad_t >= 0:
            traj_x.append(np.cos(alt_rad_t) * np.cos(az_rad_t))
            traj_y.append(np.cos(alt_rad_t) * np.sin(az_rad_t))
            traj_z.append(np.sin(alt_rad_t))
            
    fig.add_trace(ob.Scatter3d(x=traj_x, y=traj_y, z=traj_z,
                               mode='lines', line=dict(color='yellow', width=4), name='일주운동 궤적'))

    # 5. 현재 천체의 위치 (빨간 점)
    if alt_deg >= 0:
        current_x = np.cos(alt_rad) * np.cos(np.radians(az_deg))
        current_y = np.cos(alt_rad) * np.sin(np.radians(az_deg))
        current_z = np.sin(alt_rad)
        
        fig.add_trace(ob.Scatter3d(x=[current_x], y=[current_y], z=[current_z],
                                   mode='markers', marker=dict(color='red', size=10), name='현재 천체 위치'))
        fig.add_trace(ob.Scatter3d(x=[0, current_x], y=[0, current_y], z=[0, current_z],
                                   mode='lines', line=dict(color='red', width=2), showlegend=False))
    else:
        st.warning("⚠️ 현재 설정된 시각에는 천체가 지평선 아래에 있어 보이지 않습니다!")

    # 레이아웃 설정
    fig.update_layout(
        scene=dict(
            xaxis=dict(title='북(-) / 남(+)', range=[-1.2, 1.2]),
            yaxis=dict(title='서(-) / 동(+)', range=[-1.2, 1.2]),
            zaxis=dict(title='고도', range=[0, 1.2]),
            aspectmode='cube'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    
    st.plotly_chart(fig, use_container_width=True)
