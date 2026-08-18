import streamlit as st
import requests
import time
from datetime import datetime

st.set_page_config(page_title="주간 날씨 예보", page_icon="🌤️", layout="centered")

def get_weather_info(code):
    weather_map = {
        0: ("☀️", "맑음"), 1: ("🌤️", "대체로 맑음"), 2: ("⛅", "구름 조금"), 3: ("☁️", "흐림"),
        45: ("🌫️", "안개"), 48: ("🌫️", "서리 안개"), 51: ("🌦️", "약한 이슬비"), 53: ("🌦️", "이슬비"),
        55: ("🌧️", "강한 이슬비"), 61: ("🌧️", "약한 비"), 63: ("🌧️", "비"), 65: ("🌧️", "강한 비"),
        71: ("🌨️", "약한 눈"), 73: ("🌨️", "눈"), 75: ("❄️", "강한 눈"), 80: ("🌦️", "약한 소나기"),
        81: ("🌧️", "소나기"), 82: ("⛈️", "강한 소나기"), 95: ("🌩️", "뇌우"), 96: ("⛈️", "우박 뇌우")
    }
    return weather_map.get(code, ("🌡️", "정보 없음"))

KOREA_LOCATIONS = {
    "서울": (37.5665, 126.9780, "서울특별시"),
    "역삼동": (37.5006, 127.0364, "서울 강남구 역삼동"),
    "역삼": (37.5006, 127.0364, "서울 강남구 역삼동"),
    "강남구": (37.5172, 127.0473, "서울특별시 강남구"),
    "강남": (37.5172, 127.0473, "서울특별시 강남구"),
    "상암동": (37.5778, 126.8914, "서울 마포구 상암동"),
    "상암": (37.5778, 126.8914, "서울 마포구 상암동"),
    "부산": (35.1796, 129.0756, "부산광역시"),
    "우동": (35.1631, 129.1636, "부산 해운대구 우동"),
    "해운대": (35.1631, 129.1636, "부산 해운대구 우동"),
    "대구": (35.8714, 128.6014, "대구광역시"),
    "인천": (37.4563, 126.7052, "인천광역시"),
    "광주": (35.1595, 126.8526, "광주광역시"),
    "대전": (36.3504, 127.3845, "대전광역시"),
    "울산": (35.5384, 129.3114, "울산광역시"),
    "수원": (37.2636, 127.0286, "수원시"),
    "강릉": (37.7519, 128.8760, "강원특별자치도 강릉시"),
    "제주": (33.4996, 126.5312, "제주특별자치도")
}

st.title("🌤️ 주간 날씨 예보")

# 429 에러 대응을 위한 안전한 API 호출 함수 (최대 3회 재시도)
def fetch_weather_safe(url, headers):
    for attempt in range(3):
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 429:
            time.sleep(1.5 * (attempt + 1))  # 429 감지 시 잠시 대기 후 재시도
        else:
            break
    return None

query = st.text_input("위치 검색 (예: 서울, 강남구, 역삼동, 강릉)", value="역삼동")

if query:
    try:
        raw_query = query.strip()
        lat, lon, clean_name = None, None, raw_query
        
        q_key = raw_query.replace(" ", "")
        for key, val in KOREA_LOCATIONS.items():
            if key in q_key:
                lat, lon, clean_name = val
                break

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) WeatherApp/2.0'}

        if lat is None:
            try:
                geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={raw_query}&count=1&language=ko&format=json"
                res = requests.get(geo_url, headers=headers, timeout=5)
                if res.status_code == 200:
                    geo_data = res.json()
                    if "results" in geo_data and len(geo_data["results"]) > 0:
                        loc = geo_data["results"][0]
                        lat, lon = float(loc["latitude"]), float(loc["longitude"])
                        api_name = loc.get("name", "")
                        clean_name = raw_query if api_name.isascii() else api_name
            except Exception:
                pass

        if lat is None:
            try:
                nom_url = f"https://nominatim.openstreetmap.org/search?q={raw_query}&format=json&limit=1"
                res = requests.get(nom_url, headers=headers, timeout=5)
                if res.status_code == 200:
                    nom_data = res.json()
                    if nom_data:
                        lat, lon = float(nom_data[0]["lat"]), float(nom_data[0]["lon"])
            except Exception:
                pass

        if lat is not None and lon is not None:
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}&"
                f"current=temperature_2m,relative_humidity_2m,weather_code&"
                f"daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,relative_humidity_2m_max,weather_code&"
                f"timezone=Asia%2FSeoul"
            )
            
            w_res = fetch_weather_safe(weather_url, headers)
            
            if w_res and 'current' in w_res and 'daily' in w_res:
                curr = w_res['current']
                daily = w_res['daily']

                icon, condition = get_weather_info(curr.get('weather_code', 0))

                st.subheader(f"📍 {clean_name}")
                col1, col2 = st.columns(2)
                
                temp_curr = curr.get('temperature_2m', '-')
                hum_curr = curr.get('relative_humidity_2m', '-')
                rain_today = daily['precipitation_probability_max'][0] if 'precipitation_probability_max' in daily and len(daily['precipitation_probability_max']) > 0 else '-'

                col1.metric("현재 기온", f"{temp_curr} °C", f"{icon} {condition}")
                col2.metric("습도 / 강수확률", f"{hum_curr}%", f"☔ 오늘 {rain_today}%")

                st.divider()

                st.write("📅 **7일 주간 예보**")
                weekday_kr = ["월", "화", "수", "목", "금", "토", "일"]

                for i in range(len(daily['time'])):
                    date_obj = datetime.strptime(daily['time'][i], "%Y-%m-%d")
                    d_str = f"{date_obj.strftime('%m/%d')}({weekday_kr[date_obj.weekday()]})"
                    
                    code = daily['weather_code'][i] if 'weather_code' in daily else 0
                    d_icon, d_cond = get_weather_info(code)
                    
                    max_t = int(round(daily['temperature_2m_max'][i])) if 'temperature_2m_max' in daily else '-'
                    min_t = int(round(daily['temperature_2m_min'][i])) if 'temperature_2m_min' in daily else '-'
                    rain_p = daily['precipitation_probability_max'][i] if 'precipitation_probability_max' in daily else '-'
                    humidity = daily['relative_humidity_2m_max'][i] if 'relative_humidity_2m_max' in daily else '-'

                    c1, c2, c3, c4 = st.columns([2.5, 3.0, 2.5, 3.5])
                    c1.markdown(f"**{d_str}**")
                    c2.markdown(f"{d_icon} {d_cond}")
                    c3.markdown(f"{min_t}°/{max_t}°C")
                    c4.markdown(f"💧{humidity}% ☔{rain_p}%")
            else:
                st.warning("날씨 서버에 요청이 몰려 잠시 지연되고 있습니다. 3초 후 다시 검색해 주세요.")
        else:
            st.error("입력하신 위치를 찾을 수 없습니다. (예: 서울, 강남구, 역삼동, 부산)")

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
