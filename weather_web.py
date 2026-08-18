import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="주간 날씨 예보", page_icon="🌤️", layout="centered")

# ==========================================
# 🔑 여기에 OpenWeatherMap API 키를 입력하세요!
OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
# ==========================================

# OpenWeatherMap 날씨 상태 아이콘/한글 매핑
def get_weather_info(icon_code, description):
    icon_map = {
        "01d": "☀️", "01n": "🌙",
        "02d": "🌤️", "02n": "🌤️",
        "03d": "⛅", "03n": "⛅",
        "04d": "☁️", "04n": "☁️",
        "09d": "🌧️", "09n": "🌧️",
        "10d": "🌦️", "10n": "🌦️",
        "11d": "🌩️", "11n": "🌩️",
        "13d": "❄️", "13n": "❄️",
        "50d": "🌫️", "50n": "🌫️"
    }
    icon = icon_map.get(icon_code, "🌡️")
    return icon, description

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

# 10분간 결과를 캐싱하여 무분별한 API 호출 방지
@st.cache_data(ttl=600)
def fetch_owm_weather(lat, lon, api_key):
    # 현재 날씨 API
    curr_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=kr"
    # 5일 / 3시간 예보 API (무료 플랜 전용)
    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=kr"
    
    try:
        curr_res = requests.get(curr_url, timeout=5).json()
        forecast_res = requests.get(forecast_url, timeout=5).json()
        
        if curr_res.get("cod") == 200 and forecast_res.get("cod") == "200":
            return curr_res, forecast_res
    except Exception:
        pass
    return None, None

st.title("🌤️ 주간 날씨 예보")

if OPENWEATHER_API_KEY == "여기에_발급받은_API_키를_입력하세요":
    st.warning("⚠️ `weather_web.py` 파일의 `OPENWEATHER_API_KEY` 변수에 발급받으신 API 키를 입력해 주세요.")
else:
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

            # 지오코딩 (위치 찾기)
            if lat is None:
                try:
                    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={raw_query}&limit=1&appid={OPENWEATHER_API_KEY}"
                    res = requests.get(geo_url, headers=headers, timeout=5)
                    if res.status_code == 200 and res.json():
                        lat, lon = float(res.json()[0]["lat"]), float(res.json()[0]["lon"])
                except Exception:
                    pass

            if lat is not None and lon is not None:
                curr_data, forecast_data = fetch_owm_weather(lat, lon, OPENWEATHER_API_KEY)
                
                if curr_data and forecast_data:
                    # 1. 현재 날씨 정보
                    curr_temp = round(curr_data["main"]["temp"], 1)
                    curr_hum = curr_data["main"]["humidity"]
                    weather_desc = curr_data["weather"][0]["description"]
                    icon_code = curr_data["weather"][0]["icon"]
                    icon, condition = get_weather_info(icon_code, weather_desc)

                    st.subheader(f"📍 {clean_name}")
                    col1, col2 = st.columns(2)
                    col1.metric("현재 기온", f"{curr_temp} °C", f"{icon} {condition}")
                    col2.metric("현재 습도", f"{curr_hum}%")

                    st.divider()

                    # 2. 예보 정보 (일별 데이터로 재구성)
                    st.write("📅 **5일 예보**")
                    weekday_kr = ["월", "화", "수", "목", "금", "토", "일"]
                    
                    # 3시간 단위 예보 데이터를 일별 데이터로 그룹화
                    daily_summary = {}
                    for item in forecast_data["list"]:
                        dt_txt = item["dt_txt"] # "2026-08-19 12:00:00"
                        date_str = dt_txt.split(" ")[0]
                        
                        temp = item["main"]["temp"]
                        pop = item.get("pop", 0) * 100 # 강수확률
                        icon_item = item["weather"][0]["icon"]
                        desc_item = item["weather"][0]["description"]
                        
                        if date_str not in daily_summary:
                            daily_summary[date_str] = {
                                "temps": [temp],
                                "pops": [pop],
                                "icon": icon_item,
                                "desc": desc_item
                            }
                        else:
                            daily_summary[date_str]["temps"].append(temp)
                            daily_summary[date_str]["pops"].append(pop)

                    # 일별 예보 화면 출력
                    for d_str, val in list(daily_summary.items())[:5]:
                        date_obj = datetime.strptime(d_str, "%Y-%m-%d")
                        formatted_date = f"{date_obj.strftime('%m/%d')}({weekday_kr[date_obj.weekday()]})"
                        
                        max_t = round(max(val["temps"]))
                        min_t = round(min(val["temps"]))
                        max_pop = round(max(val["pops"]))
                        d_icon, d_cond = get_weather_info(val["icon"], val["desc"])

                        c1, c2, c3, c4 = st.columns([2.5, 3.0, 2.5, 3.5])
                        c1.markdown(f"**{formatted_date}**")
                        c2.markdown(f"{d_icon} {d_cond}")
                        c3.markdown(f"{min_t}°/{max_t}°C")
                        c4.markdown(f"☔ {max_pop}%")
                else:
                    st.error("날씨 데이터를 불러오지 못했습니다. API 키가 활성화되었는지 확인해 주세요. (발급 후 10분~2시간 소요)")
            else:
                st.error("입력하신 위치를 찾을 수 없습니다. (예: 서울, 강남구, 역삼동, 부산)")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
