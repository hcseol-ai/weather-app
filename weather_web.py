import streamlit as st
import requests
from datetime import datetime

# 모바일 웹 화면 설정
st.set_page_config(page_title="모바일 날씨 앱", page_icon="🌤️", layout="centered")

# WMO 날씨 코드 매핑
def get_weather_info(code):
    weather_map = {
        0: ("☀️", "맑음"), 1: ("🌤️", "대체로 맑음"), 2: ("⛅", "구름 조금"), 3: ("☁️", "흐림"),
        45: ("🌫️", "안개"), 48: ("🌫️", "서리 안개"), 51: ("🌦️", "약한 이슬비"), 53: ("🌦️", "이슬비"),
        55: ("🌧️", "강한 이슬비"), 61: ("🌧️", "약한 비"), 63: ("🌧️", "비"), 65: ("🌧️", "강한 비"),
        71: ("🌨️", "약한 눈"), 73: ("🌨️", "눈"), 75: ("❄️", "강한 눈"), 80: ("🌦️", "약한 소나기"),
        81: ("🌧️", "소나기"), 82: ("⛈️", "강한 소나기"), 95: ("🌩️", "뇌우"), 96: ("⛈️", "우박 뇌우")
    }
    return weather_map.get(code, ("🌡️", "정보 없음"))

st.title("🌤️ 주간 날씨 예보")

# 1. 도시/동 검색
query = st.text_input("위치 검색 (예: 서울 역삼동, 상암동, 부산 우동)", value="서울 역삼동")

if query:
    headers = {'User-Agent': 'VibeWeatherWeb/1.0'}
    geo_url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&accept-language=ko&limit=1"
    
    try:
        res = requests.get(geo_url, headers=headers, timeout=5).json()
        if res:
            lat = float(res[0]["lat"])
            lon = float(res[0]["lon"])
            clean_name = res[0].get("display_name", query).split(',')[0].strip()

            # 2. 날씨 데이터 조회
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}&"
                f"current=temperature_2m,relative_humidity_2m,weather_code&"
                f"daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code&"
                f"timezone=auto"
            )
            w_res = requests.get(weather_url, timeout=5).json()

            # 현재 날씨
            curr = w_res['current']
            daily = w_res['daily']
            icon, condition = get_weather_info(curr['weather_code'])

            st.subheader(f"📍 {clean_name}")
            col1, col2 = st.columns(2)
            col1.metric("현재 기온", f"{curr['temperature_2m']} °C", f"{icon} {condition}")
            col2.metric("습도 / 강수확률", f"{curr['relative_humidity_2m']}%", f"☔ 오늘 {daily['precipitation_probability_max'][0]}%")

            st.divider()

            # 7일 예보
            st.write("📅 **7일 주간 예보**")
            for i in range(len(daily['time'])):
                date_obj = datetime.strptime(daily['time'][i], "%Y-%m-%d")
                d_str = date_obj.strftime("%m/%d (%a)")
                d_icon, d_cond = get_weather_info(daily['weather_code'][i])
                max_t = daily['temperature_2m_max'][i]
                min_t = daily['temperature_2m_min'][i]
                rain_p = daily['precipitation_probability_max'][i]

                st.markdown(f"**{d_str}** | {d_icon} {d_cond} | {min_t}° / {max_t}°C | ☔ {rain_p}%")

        else:
            st.error("위치를 찾을 수 없습니다. 정확한 구/동 이름을 입력해주세요.")
    except Exception as e:
        st.error("데이터를 불러오는 중 오류가 발생했습니다.")
