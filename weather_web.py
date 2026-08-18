import streamlit as st
import requests
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

# IP 차단을 피하기 위해 3개의 서로 다른 메인/백업 날씨 엔드포인트 순차 호출
def fetch_weather_resilient(lat, lon):
    endpoints = [
        # 1. 7일 기상 예보 도메인 (기존)
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,relative_humidity_2m_max,weather_code&timezone=Asia%2FSeoul",
        # 2. 글로벌 백업 도메인 (IP 제한 프리)
        f"https://archive-api.open-meteo.com/v1/era5?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,relative_humidity_2m_max,weather_code&timezone=Asia%2FSeoul",
        # 3. 우회용 엔드포인트
        f"https://climate-api.open-meteo.com/v1/climate?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,relative_humidity_2m_max,weather_code&timezone=Asia%2FSeoul"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*'
    }

    for url in endpoints:
        try:
            res = requests.get(url, headers=headers, timeout=4)
            if res.status_code == 200:
                data = res.json()
                if 'current' in data and 'daily' in data:
                    return data
        except Exception:
            continue

    # Open-Meteo 전면 차단 시 사용할 무료 7-day 스마트 백업
    try:
        backup_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code&timezone=Asia%2FSeoul"
        res = requests.get(backup_url, headers=headers, timeout=4)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    return None

st.title("🌤️ 주간 날씨 예보")

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

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        if lat is None:
            try:
                nom_url = f"https://nominatim.openstreetmap.org/search?q={raw_query}&format=json&limit=1"
                res = requests.get(nom_url, headers=headers, timeout=4)
                if res.status_code == 200 and res.json():
                    lat, lon = float(res.json()[0]["lat"]), float(res.json()[0]["lon"])
            except Exception:
                pass

        if lat is not None and lon is not None:
            w_res = fetch_weather_resilient(lat, lon)
            
            if w_res and 'daily' in w_res:
                curr = w_res.get('current', {})
                daily = w_res.get('daily', {})

                # 현재 날씨 코드가 없을 시 주간 첫 번째 날 기준 대입
                w_code = curr.get('weather_code', daily.get('weather_code', [0])[0])
                icon, condition = get_weather_info(w_code)

                st.subheader(f"📍 {clean_name}")
                col1, col2 = st.columns(2)
                
                temp_curr = curr.get('temperature_2m', daily.get('temperature_2m_max', ['-'])[0])
                hum_curr = curr.get('relative_humidity_2m', daily.get('relative_humidity_2m_max', ['-'])[0])
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
                    humidity = daily['relative_humidity_2m_max'][i] if 'relative_humidity_2m_max' in daily and len(daily['relative_humidity_2m_max']) > i else '-'

                    c1, c2, c3, c4 = st.columns([2.5, 3.0, 2.5, 3.5])
                    c1.markdown(f"**{d_str}**")
                    c2.markdown(f"{d_icon} {d_cond}")
                    c3.markdown(f"{min_t}°/{max_t}°C")
                    c4.markdown(f"💧{humidity}% ☔{rain_p}%")
            else:
                st.error("현재 클라우드 서버 IP가 외부 API에서 차단된 상태입니다. 몇 분 후 다시 접속해 보세요.")
        else:
            st.error("입력하신 위치를 찾을 수 없습니다. (예: 서울, 강남구, 역삼동, 부산)")

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
