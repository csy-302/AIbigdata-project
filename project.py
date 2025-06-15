from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

# 옵션 설정 (headless 모드 꺼짐)
options = Options()
options.add_argument("--start-maximized")
# options.add_argument("--headless=new")  # <- 이 줄 주석처리
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# 드라이버 실행
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 유튜브 인기 급상승 페이지 열기
driver.get("https://www.youtube.com/feed/trending")
time.sleep(5)

# 스크롤 반복 (천천히 내림)
import math
SCROLL_PAUSE_SEC = 2
NUM_SCROLLS = math.ceil(100 / 5)
for i in range(NUM_SCROLLS):
    driver.execute_script("window.scrollBy(0, 1000);")
    time.sleep(SCROLL_PAUSE_SEC)

# 진단 코드
print("플랫폼:", driver.title)

# 영상 카드 요소 찾기
videos = driver.find_elements(By.TAG_NAME, 'ytd-video-renderer')
print("인기 급상승 동영상 개수:", len(videos))

# 결과 저장
results = []

for video in videos[:98]:  # 상위 10개만
    try:
        # 스크롤을 여러 번 내려서 lazy-load 트리거
        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)  # 로딩 시간 기다림
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        title_el = video.find_element(By.ID, 'video-title')
        title = title_el.text.strip()
        url = title_el.get_attribute('href')

        channel_el = video.find_element(By.XPATH, './/ytd-channel-name//a')
        channel = channel_el.text.strip()

        views_el = video.find_element(By.XPATH, './/div[@id="metadata-line"]/span[1]')
        views = views_el.text.strip()

        img_el = video.find_element(By.TAG_NAME, 'img')
        thumbnail = img_el.get_attribute('src')
        if not thumbnail or thumbnail.startswith('data:image'):
            thumbnail = img_el.get_attribute('srcset')
        if not thumbnail or thumbnail.startswith('data:image'):
            thumbnail = img_el.get_attribute('data-thumb')
        if not thumbnail or thumbnail.startswith('data:image'):
            thumbnail = '썸네일 없음'
        shorts = driver.find_elements(By.TAG_NAME, 'ytd-reel-shelf-renderer')
        for s in shorts:
            driver.execute_script("""
                var element = arguments[0];
                element.parentNode.removeChild(element);
            """, s)

        results.append({
            'title': title,
            'url': url,
            'channel': channel,
            'views': views,
            'thumbnail': thumbnail
        })
    except Exception as e:
        print("오류 발생:", e)

# 드라이버 종료
driver.quit()

# 출력
for idx, item in enumerate(results, 1):
    print(f"{idx}. {item['title']}")
    print(f"   채널: {item['channel']}")
    print(f"   조회수: {item['views']}")
    print(f"   썸네일: {item['thumbnail']}")
    print(f"   링크: {item['url']}\n")


# CSV 저장
if results:
    df = pd.DataFrame(results)
    df.to_csv("youtube_trending.csv", index=False, encoding='utf-8-sig')
    print("✅ CSV 파일 저장 완료: youtube_trending.csv")
else:
    print("⚠️ 저장할 데이터가 없습니다.")