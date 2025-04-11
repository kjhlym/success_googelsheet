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

def generate_content_with_gemini(video_data):
    try:
        # Gemini에 전달할 프롬프트 생성
        prompt = f"""
        다음 YouTube 영상에 대한 블로그 포스트를 작성해주세요:

        제목: {video_data['title']}
        채널: {video_data['channel_title']}
        설명: {video_data['description']}

# 전문가급 블로그 글 작성 프롬프트

## 기본 정보 입력
- **주제**: [모든 사람이 즐길 수 있는 내용]
- **목표 독자층**: [전문가와 일반 사용자]
- **글의 목적**: [정보 제공 및 교육]
- **원하는 글 길이**: [1500]
- **글의 성격**: [객관적이고 교육적인 내용]

## 중요 지침
- 특정 상품이나 브랜드를 직접적으로 홍보하거나 광고하지 않습니다
- 구매 링크나 제품 추천은 포함하지 않습니다
- 객관적인 정보와 교육적인 내용에 중점을 둡니다
- 가격 정보나 구매처 정보는 제외합니다
- "추천", "구매", "할인" 등의 홍보성 단어 사용을 피합니다

## 글 구조 지침
- 객관적인 정보 전달을 우선으로 합니다
- 실제 데이터와 연구 결과를 바탕으로 설명합니다
- 교육적이고 유익한 내용을 중심으로 구성합니다
- 특정 제품이나 브랜드에 치우치지 않고 카테고리 전반적인 정보를 다룹니다
- 리스트 형식으로 자연스럽게 작성합니다

## 포함해야 할 내용
- 주제에 대한 기본적인 이해와 배경
- 관련된 기술적/과학적 설명
- 객관적인 장단점 분석
- 실제 사용 시 고려해야 할 요소들
- 관련 통계나 연구 결과
- 향후 발전 방향이나 트렌드

## 스타일 지침
- **전문성**: 해당 분야의 전문가처럼 객관적인 어조 유지
- **교육적**: 독자가 이해하기 쉽게 설명
- **중립성**: 특정 제품이나 브랜드를 홍보하지 않음
- **가독성**: 
  * 글을 폭 100% 전체 화면에 작성
  * 짧은 문단 (2-3문장)
  * 적절한 여백과 단락 구분
  * 중요 내용은 **굵게** 또는 *기울임체*로 강조
- **일관성**: 처음부터 끝까지 객관적이고 교육적인 톤 유지

## 결론
- 핵심 내용 요약
- 객관적인 관점에서의 시사점
- 추가 학습이나 연구를 위한 방향 제시

## 참고자료
- 신뢰할 수 있는 학술 자료나 연구 결과
- 공신력 있는 기관의 통계 자료
"""

        # Gemini로 콘텐츠 생성
        response = model.generate_content(prompt)
        
        # 마크다운을 HTML로 변환
        markdown_text = response.text
        html_content = markdown2.markdown(markdown_text, extras=['fenced-code-blocks', 'tables', 'break-on-newline'])
        
        # 스타일 적용 - 폭을 넓게 조정
        styled_html = f'''
        <div style="background-color:#ffffff; padding:20px; border-radius:8px; margin-bottom:20px; box-shadow:0 2px 8px rgba(26,115,232,0.1); border:1px solid rgba(26,115,232,0.2); width:100%;">
            <div style="color:#2c3e50; line-height:1.8; font-size:1.1em; width:100%;">
                {html_content}
            </div>
        </div>
        
        <div style="margin-top:30px; padding:15px; background-color:#f8f9fa; border-radius:5px; font-size:0.9em; color:#546e7a;">
            <p>이 글은 YouTube 영상 <a href="https://www.youtube.com/watch?v={video_data['video_id']}" target="_blank">{video_data['title']}</a>를 기반으로 작성되었습니다.</p>
            <p>채널: {video_data['channel_title']}</p>
        </div>
        '''

        # HTML을 파일로 저장
        output_file = f"json/gemini_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(styled_html)
        
        return output_file, styled_html
        
    except Exception as e:
        print(f"콘텐츠 생성 중 오류 발생: {str(e)}")
        return None, None

def create_html_content(json_file):
    try:
        # JSON 파일 로드
        with open(json_file, 'r', encoding='utf-8') as f:
            video_data = json.load(f)
        
        # Gemini로 콘텐츠 생성
        print(f"Gemini로 '{video_data['title']}' 콘텐츠 생성 시작...")
        html_file, html_content = generate_content_with_gemini(video_data)
        
        if html_file:
            print(f"콘텐츠 생성 완료: {html_file}")
            return html_file, html_content, video_data
        else:
            print("콘텐츠 생성 실패")
            return None, None, None
            
    except Exception as e:
        print(f"HTML 콘텐츠 생성 중 오류: {str(e)}")
        return None, None, None

def tistory_write(_driver, json_file):
    try:
        # HTML 콘텐츠 생성
        html_file, html_content, video_data = create_html_content(json_file)
        
        if not html_content or not video_data:
            print("콘텐츠를 생성할 수 없어 티스토리 작성을 중단합니다.")
            return False
            
        # 티스토리 글쓰기 페이지로 이동
        _driver.get(f"{tistory_blog_name}/manage/post")
        _driver.implicitly_wait(LOADING_WAIT_TIME)
        
        # iframe으로 전환
        WebDriverWait(_driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, 'editor-frame'))
        )
        
        # 제목 입력
        title_input = WebDriverWait(_driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".textarea-title"))
        )
        title_input.send_keys(f"{video_data['title']} - {video_data['channel_title']}")
        
        # HTML 모드로 전환
        html_button = WebDriverWait(_driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-html"))
        )
        html_button.click()
        
        # HTML 에디터 영역
        html_editor = WebDriverWait(_driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".CodeMirror-code"))
        )
        html_editor.click()
        
        # 클립보드에 HTML 복사 후 붙여넣기
        pyperclip.copy(html_content)
        
        # Ctrl+V 또는 Command+V로 붙여넣기
        if osName == "Windows":
            ActionChains(_driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        else:  # Mac
            ActionChains(_driver).key_down(Keys.COMMAND).send_keys('v').key_up(Keys.COMMAND).perform()
        
        sleep(2)  # 붙여넣기 완료 대기
        
        # 카테고리 선택
        _driver.switch_to.default_content()  # iframe에서 빠져나옴
        
        # 오른쪽 사이드바 열기
        side_button = WebDriverWait(_driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".wrap_openbtn"))
        )
        side_button.click()
        
        # 카테고리 드롭다운
        category_button = WebDriverWait(_driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".category-btn"))
        )
        category_button.click()
        
        # 카테고리 목록에서 'IT' 선택
        categories = WebDriverWait(_driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".list-item"))
        )
        
        for category in categories:
            if category.text.strip() == tistory_category_name:
                category.click()
                break
        
        # 발행 버튼 클릭
        publish_button = WebDriverWait(_driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-publish"))
        )
        publish_button.click()
        
        # 발행 확인 버튼
        confirm_button = WebDriverWait(_driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-blue"))
        )
        confirm_button.click()
        
        # 발행 완료 확인
        WebDriverWait(_driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".wrap_notice"))
        )
        
        print(f"{C_GREEN}티스토리 포스팅 완료: {video_data['title']}{C_END}")
        return True
        
    except Exception as e:
        print(f"{C_RED}티스토리 글쓰기 중 오류 발생: {str(e)}{C_END}")
        return False
        
def main():
    driver = init_driver()
    if not driver:
        print("브라우저를 초기화할 수 없습니다.")
        return
    
    try:
        # 티스토리 로그인
        tistory_login(driver)
        
        # 유튜브 검색어 입력 받기
        query = input(f"\n{C_YELLOW}YouTube 검색어를 입력하세요: {C_END}")
        
        # 유튜브 영상 검색
        json_file = search_youtube(query)
        
        if json_file:
            print(f"검색 결과 저장됨: {json_file}")
            
            # 티스토리에 글쓰기
            tistory_write(driver, json_file)
            
        else:
            print("검색 결과를 찾을 수 없습니다.")
    
    finally:
        # 브라우저 종료
        input(f"\n{C_YELLOW}종료하려면 아무 키나 누르세요...{C_END}")
        driver.quit()

if __name__ == "__main__":
    main()