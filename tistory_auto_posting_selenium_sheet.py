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

# 대기 시간 최적화 (기존 값 감소)
LOADING_WAIT_TIME = 3  # 5초에서 3초로 감소
PAUSE_TIME = 1  # 3초에서 1초로 감소

tistory_blog_name = 'https://cathodicpro.tistory.com'

tistory_category_name = 'IT'

def init_driver():
    try:
        # Chrome 설정
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # 성능 개선을 위한 추가 옵션
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        
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
        # 이미 로그인되어 있는지 확인 (프로필 아이콘 찾기)
        try:
            profile = _driver.find_element(By.CLASS_NAME, 'link_profile')
            print('이미 로그인 되어있습니다.')
            return
        except:
            # 로그인이 필요한 경우에만 아래 코드 실행
            pass
            
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
    
        print(f'\n{C_BOLD}{C_RED}{C_BGBLACK}주의: 로그인 진행 중... 60초 동안 대기합니다.{C_END}')
        # 대기 시간 3분에서 1분으로 단축
        WebDriverWait(_driver, 60).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'link_profile')
            )
        )
        print("로그인 완료!")
    except Exception as e:
        print(f'로그인 과정에서 오류 발생: {str(e)}')
    

def search_youtube(query):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    try:
        # YouTube 검색 API 요청을 한 번에 보내기 위해 검색 및 동영상 상세 정보를 병합
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
        # 더 간결한 프롬프트로 최적화하여 API 응답 속도 개선
        prompt = f"""
        다음 YouTube 영상에 대한 블로그 포스트를 작성해주세요 (1200자 내외로 간결하게):

        제목: {video_data['title']}
        채널: {video_data['channel_title']}
        설명: {video_data['description']}

# 블로그 글 작성 요구사항
- 객관적이고 교육적인 내용으로 작성
- 특정 상품이나 브랜드 홍보 없이 중립적으로 서술
- 주제와 관련된 기술적/과학적 설명 포함
- 짧은 문단으로 가독성 높게 작성
- 핵심 내용 요약 및 객관적 관점의 시사점 제시
"""

        # Gemini로 콘텐츠 생성 - 최적화된 설정 사용
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "max_output_tokens": 2048,
        }
        
        response = model.generate_content(prompt, generation_config=generation_config)
        
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
        '''
        
        return styled_html
        
    except Exception as e:
        print(f"Gemini API 호출 중 오류 발생: {str(e)}")
        return None

def create_html_content(json_file):
    try:
        # JSON 파일 읽기
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Gemini로 콘텐츠 생성 (이미 HTML로 변환됨)
        print(f"Gemini로 콘텐츠 생성 중...")
        ai_generated_content = generate_content_with_gemini(data)
        if not ai_generated_content:
            return None
            
        # 간소화된 HTML 템플릿 사용
        html_content = f"""
        <div style="font-family:'Pretendard',sans-serif; line-height:1.8; color:#2d3748; width:100%;">
            <h1 style="color:#2563eb; font-size:2.2em; font-weight:700; margin-bottom:25px; border-bottom:2px solid #e2e8f0; padding-bottom:15px;">{data['title']}</h1>
            <div>
                {ai_generated_content}
            </div>
            <div style="margin-top:20px; font-size:0.9em; color:#64748b;">
                <p>출처: <a href="https://www.youtube.com/watch?v={data['video_id']}" target="_blank">{data['channel_title']}</a></p>
            </div>
        </div>
        """
        
        return html_content
    
    except Exception as e:
        print(f"HTML 생성 중 오류 발생: {str(e)}")
        return None

def tistory_write(_driver, json_file):
    try:
        # HTML 콘텐츠 생성
        html_content = create_html_content(json_file)
        if not html_content:
            raise Exception("HTML 컨텐츠 생성 실패")
            
        # 티스토리 글쓰기 페이지로 직접 이동
        _driver.get(f"{tistory_blog_name}/manage/newpost/?type=post")
        
        # JSON 파일에서 제목 가져오기
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 새로운 에디터 방식 우선 시도 (더 빠름)
        try:
            # HTML 모드로 전환
            html_button = WebDriverWait(_driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#editor-mode-layer-btn-open"))
            )
            html_button.click()
            html_mode = WebDriverWait(_driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#editor-mode-html"))
            )
            html_mode.click()
            
            # 경고창 처리
            try:
                alert = _driver.switch_to.alert
                alert.accept()
            except:
                pass
                
            # 에디터 영역 찾기 및 내용 입력
            editor = WebDriverWait(_driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".CodeMirror-lines"))
            )
            editor.click()
            
            # 기존 내용 선택하여 삭제 후 새 내용 붙여넣기
            actions = ActionChains(_driver)
            actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
            actions.key_down(Keys.DELETE).key_up(Keys.DELETE).perform()
            
            # 내용 붙여넣기
            pyperclip.copy(html_content)
            actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            
            # 제목 입력
            title_input = WebDriverWait(_driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#post-title-inp"))
            )
            title_input.click()
            title_input.clear()
            title_input.send_keys(data['title'])
            
            # 카테고리 선택
            category_button = WebDriverWait(_driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#category-btn"))
            )
            category_button.click()
            
            # 카테고리 목록에서 선택
            category_list = WebDriverWait(_driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".list-item"))
            )
            
            for category in category_list:
                if category.text.strip() == tistory_category_name:
                    category.click()
                    break
            
            # 발행 버튼 클릭
            publish_button = WebDriverWait(_driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-publish"))
            )
            publish_button.click()
            
            # 발행 확인 버튼 찾아서 클릭
            confirm_button = WebDriverWait(_driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-blue"))
            )
            confirm_button.click()
            
            # 발행 완료 확인 (시간 단축)
            WebDriverWait(_driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".wrap_notice"))
            )
            
        except Exception as e:
            print(f"새 에디터 방식 실패, 기존 방식 시도: {str(e)}")
            
            # 페이지 새로고침 후 기존 방식 시도
            _driver.refresh()
            
            # HTML 모드로 전환 - 기존 방식
            html_button = WebDriverWait(_driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn_html"))
            )
            html_button.click()
            
            # 기존 방식 에디터
            html_area = WebDriverWait(_driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.html"))
            )
            html_area.clear()
            pyperclip.copy(html_content)
            html_area.send_keys(Keys.CONTROL, 'v')
            
            # 제목 입력
            title_input = WebDriverWait(_driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#title"))
            )
            title_input.send_keys(data['title'])
            
            # 카테고리 선택
            category_select = WebDriverWait(_driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#category"))
            )
            for option in category_select.find_elements(By.TAG_NAME, "option"):
                if option.text == tistory_category_name:
                    option.click()
                    break
                    
            # 발행 버튼 클릭
            publish_button = WebDriverWait(_driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn_publish"))
            )
            publish_button.click()
        
        print(f"{C_GREEN}티스토리 포스팅 완료: {data['title']}{C_END}")
        return True
        
    except Exception as e:
        print(f"{C_RED}티스토리 글쓰기 중 오류 발생: {str(e)}{C_END}")
        return False

def main():
    try:
        print("\nSTART...")
        
        # YouTube 검색어
        search_query = input("YouTube 검색어를 입력하세요: ")
        
        # chrome driver init (먼저 초기화하여 병렬로 진행되도록)
        print("Chrome 드라이버 초기화 중...")
        driver = init_driver()
        if not driver:
            print("Chrome 드라이버 초기화 실패")
            return
            
        # YouTube 검색 및 JSON 저장 (병렬로 진행)
        print(f"YouTube 검색 중: {search_query}")
        json_file = search_youtube(search_query)
        if not json_file:
            print("YouTube 검색 결과를 가져오는데 실패했습니다.")
            driver.quit()
            return
        
        # tistory login
        print("티스토리 로그인 중...")
        tistory_login(driver)
        
        # tistory write
        print("티스토리 포스팅 시작...")
        tistory_write(driver, json_file)
        
    except Exception as e:
        print(f"예상치 못한 오류 발생: {str(e)}")
    finally:
        try:
            # 드라이버 종료
            driver.quit()
        except:
            pass
        print("\n작업이 완료되었습니다.")


if __name__ == '__main__':
    main()