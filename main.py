import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

# 한글 깨짐 방지 설정 (시스템 기본 폰트 사용)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

# 페이지 설정
st.set_page_config(page_title="지구과학II 천구 시뮬레이터", layout="wide")

st.title("🌌 천체 좌표계 변환 및 관측 시뮬레이터")
st.markdown("**지구과학II 천문 단원:** 적도 좌표계(적경, 적위)를 지평 좌표계(방위각, 고도)로 변환하고 일주운동을 시각화합니다.")

# --- 사이드바: 사용자 입력 컨트롤러 ---
st.sidebar.header("⚙️ 관측 및 천체 설정")

lat_deg = st.sidebar.slider("관측자 위도 (N)", min_value=0.0, max_value=90.0, value=37.5, step=0.5)
dec_deg = st.sidebar.slider("천체의 적위 (δ)", min_value=-90.0, max_value=90.0, value=20.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("⏰ 시간 및 재생 제어")

# 세션 상태 변수 초기화
if "lha_hour" not in st.session_state:
    st.session_state.lha_hour = 0.0
if "is_playing" not in st.session_state:
    st.session_state.is_playing = False

# 슬라이더 구성
lha_hour = st.sidebar.slider("지방시각 (Hour Angle)", min_value=0.0, max_value=24.0, value=st.session_state.lha_hour, step=0.1)
st.session_state.lha_hour = lha_hour

# 버튼 제어
play_col1, play_col2 = st.sidebar.columns(2)
with play_col1:
    if st.button("▶️ 일주운동 재생"):
        st.session_state.is_playing = True
with play_col2:
    if st.button("⏱️ 정지/리셋"):
        st.session_state.is_playing = False
        st.session_state.lha_hour = 0.0
        st.rerun()

# 애니메이션 상태일 때 시간 변화 로직 (0.4시간씩 증가하여 속도감 부여)
if st.session_state.is_playing:
    time.sleep(0.01)
    st.session_state.lha_hour = (st.session_state.lha_hour + 0.4) % 24.0
    st.rerun()

# --- 좌표 변환 수학 함수 ---
def get_az_alt(lha_h, lat_d, dec_d):
    phi = np.radians(lat_d)
    delta = np.radians(dec_d)
    H = np.radians(lha_h * 15.0)

    # 고도 계산
    sin_alt = np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.cos(H)
    sin_alt = np.clip(sin_alt, -1.0, 1.0)
    alt_r = np.arcsin(sin_alt)
    alt_d = np.degrees(alt_r)

    # 방위각 계산
    cos_alt = np.cos(alt_r)
    if cos_alt == 0:
        az_d = 0.0
    else:
        cos_az = (np.sin(delta) - np.sin(phi) * sin_alt) / (np.cos(phi) * cos_alt)
        cos_az = np.clip(cos_az, -1.0, 1.0)
        az_r = np.arccos(cos_az)
        az_d = np.degrees(az_r)
        if np.sin(H) > 0: 
            az_d = 360.0 - az_d
    return az_d, alt_d

# 현재 위치 계산
az_deg, alt_deg = get_az_alt(st.session_state.lha_hour, lat_deg, dec_deg)

# --- 결과 디스플레이 ---
col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("📊 실시간 계산 결과")
    st.metric(label="현재 천체의 고도 (Altitude)", value=f"{alt_deg:.2f}°")
    st.metric(label="현재 천체의 방위각 (Azimuth)", value=f"{az_deg:.2f}° (북점 기준)")
    st.metric(label="현재 지방시각 (LHA)", value=f"{st.session_state.lha_hour:.1f}시")
    
    st.markdown("---")
    st.markdown("""
    ### 💡 일주운동 관측 포인트
    * **동(E, 90°)** 쪽에서 별이 떠올라 고도가 높아집니다.
    * **지방시각이 0시**일 때 정확히 **남(S, 180°)** 자오선을 통과하며 남중고도에 도달합니다.
    * 이후 **서(W, 270°)** 쪽으로 고도가 낮아지며 지평선 아래로 집니다.
    """)

# --- Matplotlib 기반 2D 평면 천구도 시각화 ---
with col2:
    st.subheader("🔮 관측자 중심 지평좌표계 투영도 (하늘 뷰)")
    
    # Polar (극좌표계) 그래프 생성 -> 반지름은 (90 - 고도), 각도는 방위각
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'projection': 'polar'})
    
    # Matplotlib 극좌표계는 기본적으로 0도가 오른쪽(동쪽)이므로, 북쪽(90도)이 위로 오도록 회전하고 시계방향 회전 설정
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    
    # 지평선 가이드라인 및 밤하늘 배경색 설정
    ax.set_facecolor('#0B1D3A') 
    ax.set_ylim(0, 90)
    ax.set_yticks([30, 60, 90])
    ax.set_yticklabels(['60°', '30°', '0°(지평선)'], color='gray', size=9) # 반지름이 클수록 고도가 낮음
    ax.set_xticklabels(['N(북)', 'NE', 'E(동)', 'SE', 'S(남)', 'SW', 'W(서)', 'NW'], color='black', size=11)
    ax.grid(True, color='#1E3A60', linestyle='--')

    # 1. 전체 24시간 일주운동 고정 궤적 계산 및 그리기
    hours = np.linspace(0, 24, 200)
    traj_theta = []
    traj_r = []
    
    for h_t in hours:
        az_t, alt_t = get_az_alt(h_t, lat_deg, dec_deg)
        if alt_t >= 0: # 지평선 위에 있을 때만 기록
            traj_theta.append(np.radians(az_t))
            traj_r.append(90 - alt_t) # 중심(0)이 천정(고도90), 가장자리(90)가 지평선(고도0)
            
    if traj_theta:
        ax.plot(traj_theta, traj_r, color='gold', linewidth=2.5, linestyle='-', label='일주운동 궤적')

    # 2. 현재 실시간 천체의 위치 표시 (빛나는 노란색 별 모양 마커)
    if alt_deg >= 0:
        ax.scatter(np.radians(az_deg), 90 - alt_deg, color='#FFDD00', s=200, marker='*', 
                   edgecolors='orange', linewidths=1.5, zorder=5, label='현재 천체')
        
        # 천정과 천체를 잇는 선 (고도 파악 용도)
        ax.plot([0, np.radians(az_deg)], [0, 90 - alt_deg], color='red', linestyle=':', linewidth=1.5)
    else:
        # 지평선 아래로 내려갔을 때는 밤하늘 중앙에 안내 문구 표시
        ax.text(0, 0, "천체가 지평선 아래에 있습니다\n(관측 불가)", color='white', 
                ha='center', va='center', fontsize=12, fontweight='bold', bbox=dict(facecolor='black', alpha=0.6))

    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
    
    # 🌟 Matplotlib 그래프는 캐싱 버그 없이 streamlit에서 60fps에 준하게 즉시 동적 새로고침됩니다.
    st.pyplot(fig, use_container_width=True)
