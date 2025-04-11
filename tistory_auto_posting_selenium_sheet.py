'''
tistory_auto_posting_selenium_01.py 에서 콘텐츠 생성 프롬프트 수정
구글 시트에 있는 영상 제목과 채널 제목을 가져와서 콘텐츠 생성
'''

from time import sleep
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import platform
import subprocess
import pyperclip
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
import os
import json
from datetime import datetime
from googleapiclient.discovery import build
from dotenv import load_dotenv
import google.generativeai as genai
import markdown2

# Load environment variables
load_dotenv()

# YouTube API 설정
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL')
# Tistory 로그인 정보
TISTORY_ID = os.getenv('TISTORY_ID')
TISTORY_PASSWORD = os.getenv('TISTORY_PASSWORD')
# Gemini API 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-pro-exp-02-05')

C_END = "\033[0m"
C_BOLD = "\033[1m"
C_INVERSE = "\033[7m"
C_BLACK = "\033[30m"
C_RED = "\033[31m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_BLUE = "\033[34m"
C_PURPLE = "\033[35m"
C_CYAN = "\033[36m"
C_WHITE = "\033[37m"
C_BGBLACK = "\033[40m"
C_BGRED = "\033[41m"
C_BGGREEN = "\033[42m"
C_BGYELLOW = "\033[43m"
C_BGBLUE = "\033[44m"
C_BGPURPLE = "\033[45m"
C_BGCYAN = "\033[46m"
C_BGWHITE = "\033[47m"

osName = platform.system()  # window 인지 mac 인지 알아내기 위한

LOADING_WAIT_TIME = 5
PAUSE_TIME = 3

tistory_blog_name = 'https://cathodicpro.tistory.com'

tistory_category_name = 'IT'

def init_driver():
    # Chrome 프로세스 종료 부분 제거하고 바로 WebDriver 초기화
    try:
        # Chrome 설정
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # ChromeProfile 디렉토리 설정 (기존 프로필 사용)
        user_data_dir = os.path.join(os.getcwd(), "ChromeProfile")
        options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # 새 창으로 시작하기 위한 설정
        options.add_argument("--new-window")
        
        # ChromeDriver 초기화
        service = ChromeService()
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.implicitly_wait(LOADING_WAIT_TIME)
        print("Chrome WebDriver 초기화 성공")
        return driver
        
    except Exception as e:
        print(f"브라우저 초기화 실패: {str(e)}")
        return None


def tistory_login(_driver):
    
    try:
        _driver.get('https://www.tistory.com/auth/login')
        _driver.implicitly_wait(LOADING_WAIT_TIME)
        _driver.find_element(By.CLASS_NAME, 'link_kakao_id').click()
        # ID 입력
        id_input = WebDriverWait(_driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='loginId']"))
        )
        id_input.send_keys(TISTORY_ID)
        
        # Password 입력
        pw_input = WebDriverWait(_driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='password']"))
        )
        pw_input.send_keys(TISTORY_PASSWORD)
        
        # 로그인 버튼 클릭
        login_button = WebDriverWait(_driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        login_button.click()
    
        print(f'\n{C_BOLD}{C_RED}{C_BGBLACK}주의: 3분안에 로그인을 완료해주세요!!!(tistory main ID 로 로그인해야함){C_END}')
        WebDriverWait(_driver, 180).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'link_profile')
            )
        )
    except:
        print('이미 로그인 되어있습니다.')
    

def search_youtube(query):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    try:
        search_response = youtube.search().list(
            q=query,
            part='snippet',
            maxResults=1,
            type='video'
        ).execute()

        if not search_response['items']:
            return None

        video_id = search_response['items'][0]['id']['videoId']
        video_response = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        ).execute()

        video_info = video_response['items'][0]
        
        # JSON 데이터 생성
        data = {
            'video_id': video_id,
            'title': video_info['snippet']['title'],
            'description': video_info['snippet']['description'],
            'channel_title': video_info['snippet']['channelTitle'],
            'upload_date': video_info['snippet']['publishedAt'],
            'view_count': video_info['statistics']['viewCount'],
            'tags': video_info['snippet'].get('tags', []),
            'search_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # JSON 파일 저장
        os.makedirs('json', exist_ok=True)
        filename = f"json/youtube_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filename

    except Exception as e:
        print(f"YouTube API 검색 중 오류 발생: {str(e)}")
        return None