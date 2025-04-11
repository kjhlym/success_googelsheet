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

# 환경 변수 로드
load_dotenv()

# API 키 및 계정 정보
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro-latest')
TISTORY_ID = os.getenv('TISTORY_ID')
TISTORY_PASSWORD = os.getenv('TISTORY_PASSWORD')
KAKAO_ID = os.getenv('KAKAO_ID')
KAKAO_PW = os.getenv('KAKAO_PW')

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
        _driver.implicitly_wait(LOADING_WAIT_TIME)
     
        
        if not KAKAO_ID or not KAKAO_PW:
            raise Exception("카카오 로그인 정보가 .env 파일에 설정되지 않았습니다.")
            
        
        
        
        
        # 카카오 로그인 버튼 클릭
        
        # 카카오 아이디 입력
        id_field = WebDriverWait(_driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='loginId']"))
        )
        id_field.click()
        id_field.send_keys(KAKAO_ID)
        
        # 카카오 비밀번호 입력
        pw_field = WebDriverWait(_driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='password']"))
        )
        pw_field.click()
        pw_field.send_keys(KAKAO_PW)
        
        
        
        
        
      
        
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
    # URL이 직접 입력된 경우 처리
    if 'youtube.com/watch?v=' in query or 'youtu.be/' in query:
        try:
            # URL에서 video_id 추출
            if 'youtube.com/watch?v=' in query:
                video_id = query.split('watch?v=')[1].split('&')[0]
            elif 'youtu.be/' in query:
                video_id = query.split('youtu.be/')[1].split('?')[0]
            
            print(f"YouTube URL이 감지되었습니다. Video ID: {video_id}")
            
            # API 키 유효성 확인
            if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == '':
                print("YouTube API 키가 설정되지 않았습니다. 기본 정보만으로 진행합니다.")
                # API 키 없이 기본 데이터 생성
                data = {
                    'video_id': video_id,
                    'title': f"YouTube 영상 ({video_id})",
                    'description': "YouTube 영상에 대한 설명입니다.",
                    'channel_title': "YouTube 채널",
                    'upload_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'view_count': "0",
                    'tags': [],
                    'search_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # YouTube 페이지 직접 스크래핑 제안 메시지
                print("참고: API 키가 없어 상세 정보를 가져올 수 없습니다.")
            else:
                # API 키가 있는 경우 정보 가져오기 시도
                try:
                    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
                    video_response = youtube.videos().list(
                        part='snippet,statistics',
                        id=video_id
                    ).execute()
                    
                    if not video_response['items']:
                        raise Exception("비디오 정보를 찾을 수 없습니다.")
                        
                    video_info = video_response['items'][0]
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
                except Exception as api_err:
                    print(f"YouTube API 호출 실패: {str(api_err)}")
                    # API 호출 실패 시 기본 데이터 사용
                    data = {
                        'video_id': video_id,
                        'title': f"YouTube 영상 ({video_id})",
                        'description': "YouTube API 호출 실패로 상세 정보를 가져올 수 없습니다.",
                        'channel_title': "YouTube 채널",
                        'upload_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'view_count': "0",
                        'tags': [],
                        'search_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
            
            # JSON 파일 저장
            os.makedirs('json', exist_ok=True)
            filename = f"json/youtube_video_{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            return filename
            
        except Exception as e:
            print(f"YouTube URL 처리 중 오류 발생: {str(e)}")
            return None
    
    # 일반 검색어인 경우 기존 API 검색 로직 실행
    try:
        # API 키 확인
        if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == '':
            print("YouTube API 키가 설정되지 않았습니다.")
            return None
            
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        
        # YouTube 검색 API 요청
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
        
        # 안전 설정 추가 - 모든 카테고리에 대해 차단 임계값 낮추기
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # 최대 3번 재시도
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(
                    prompt, 
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                
                # 응답 검증
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    print(f"프롬프트 피드백: {response.prompt_feedback}")
                    
                    if response.prompt_feedback.block_reason:
                        print(f"프롬프트가 차단되었습니다. 이유: {response.prompt_feedback.block_reason}")
                        # 차단된 경우 기본 콘텐츠 생성
                        markdown_text = f"""
# {video_data['title']}

이 블로그 포스트는 YouTube 영상 [{video_data['title']}](https://www.youtube.com/watch?v={video_data['video_id']})에 대한 간략한 소개입니다.

## 영상 정보

- **채널명**: {video_data['channel_title']}
- **조회수**: {video_data['view_count']}

## 영상 내용 요약

이 영상은 채널 [{video_data['channel_title']}](https://www.youtube.com/channel)에서 제작한
교육적인 콘텐츠입니다. 영상에서 다루는 내용을 참고하시려면 원본 영상을 시청해 주세요.

[영상 바로가기](https://www.youtube.com/watch?v={video_data['video_id']})
"""
                    else:
                        # 응답이 비어있거나 parts가 없는 경우 처리
                        if not hasattr(response, 'text') or not response.text:
                            if attempt < max_retries - 1:
                                print(f"응답이 비어있습니다. {attempt+1}번째 재시도 중...")
                                continue
                            else:
                                # 모든 재시도가 실패하면 기본 콘텐츠 생성
                                markdown_text = f"""
# {video_data['title']}

이 블로그 포스트는 YouTube 영상 [{video_data['title']}](https://www.youtube.com/watch?v={video_data['video_id']})에 대한 간략한 소개입니다.

## 영상 정보

- **채널명**: {video_data['channel_title']}
- **조회수**: {video_data['view_count']}

## 영상 내용 요약

이 영상은 채널 [{video_data['channel_title']}](https://www.youtube.com/channel)에서 제작한
교육적인 콘텐츠입니다. 영상에서 다루는 내용을 참고하시려면 원본 영상을 시청해 주세요.

[영상 바로가기](https://www.youtube.com/watch?v={video_data['video_id']})
"""
                        else:
                            markdown_text = response.text
                else:
                    # 정상적인 응답인 경우
                    if hasattr(response, 'text') and response.text:
                        markdown_text = response.text
                    else:
                        if attempt < max_retries - 1:
                            print(f"응답이 비어있습니다. {attempt+1}번째 재시도 중...")
                            continue
                        else:
                            # 모든 재시도가 실패하면 기본 콘텐츠 생성
                            markdown_text = f"""
# {video_data['title']}

이 블로그 포스트는 YouTube 영상 [{video_data['title']}](https://www.youtube.com/watch?v={video_data['video_id']})에 대한 간략한 소개입니다.

## 영상 정보

- **채널명**: {video_data['channel_title']}
- **조회수**: {video_data['view_count']}

## 영상 내용 요약

이 영상은 채널 [{video_data['channel_title']}](https://www.youtube.com/channel)에서 제작한
교육적인 콘텐츠입니다. 영상에서 다루는 내용을 참고하시려면 원본 영상을 시청해 주세요.

[영상 바로가기](https://www.youtube.com/watch?v={video_data['video_id']})
"""
                
                # 마크다운을 HTML로 변환
                html_content = markdown2.markdown(markdown_text, extras=['fenced-code-blocks', 'tables', 'break-on-newline'])
                
                # 스타일 적용 - 폭을 넓게 조정
                styled_html = f'''
                <div style="background-color:#ffffff; padding:20px; border-radius:8px; margin-bottom:20px; box-shadow:0 2px 8px rgba(26,115,232,0.1); border:1px solid rgba(26,115,232,0.2); width:100%;">
                    <div style="color:#2c3e50; line-height:1.8; font-size:1.1em; width:100%;">
                        {html_content}
                    </div>
                </div>
                '''
                
                print(f"콘텐츠 생성 완료 ({attempt+1}번째 시도)")
                return styled_html
                
            except Exception as retry_err:
                if attempt < max_retries - 1:
                    print(f"API 호출 실패 ({attempt+1}번째 시도): {str(retry_err)}")
                    sleep(2)  # 잠시 대기 후 재시도
                else:
                    raise retry_err
        
    except Exception as e:
        print(f"Gemini API 호출 중 오류 발생: {str(e)}")
        
        # 오류 발생 시 기본 콘텐츠 생성
        try:
            markdown_text = f"""
# {video_data['title']}

이 블로그 포스트는 YouTube 영상 [{video_data['title']}](https://www.youtube.com/watch?v={video_data['video_id']})에 대한 간략한 소개입니다.

## 영상 정보

- **채널명**: {video_data['channel_title']}
- **조회수**: {video_data['view_count']}

## 영상 내용 요약

이 영상은 채널 [{video_data['channel_title']}](https://www.youtube.com/channel)에서 제작한
교육적인 콘텐츠입니다. 영상에서 다루는 내용을 참고하시려면 원본 영상을 시청해 주세요.

[영상 바로가기](https://www.youtube.com/watch?v={video_data['video_id']})
"""
            html_content = markdown2.markdown(markdown_text, extras=['fenced-code-blocks', 'tables', 'break-on-newline'])
            
            styled_html = f'''
            <div style="background-color:#ffffff; padding:20px; border-radius:8px; margin-bottom:20px; box-shadow:0 2px 8px rgba(26,115,232,0.1); border:1px solid rgba(26,115,232,0.2); width:100%;">
                <div style="color:#2c3e50; line-height:1.8; font-size:1.1em; width:100%;">
                    {html_content}
                </div>
            </div>
            '''
            
            print("오류 발생으로 기본 콘텐츠 생성 완료")
            return styled_html
            
        except Exception as fallback_err:
            print(f"기본 콘텐츠 생성 중 오류 발생: {str(fallback_err)}")
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
        sleep(3)  # 페이지 로딩 대기
        
        # 이전 작성 중이던 글 알림 처리
        try:
            # 알림창 확인
            alert = WebDriverWait(_driver, 5).until(EC.alert_is_present())
            # 알림 내용에 따라 처리
            alert_text = alert.text
            print(f"알림창 발견: {alert_text}")
            if "저장된 글이 있습니다" in alert_text:
                # '취소' 버튼 클릭 (새 글 작성)
                alert.dismiss()
            else:
                # 기본적으로 '확인' 클릭
                alert.accept()
            sleep(2)  # 알림창 처리 후 대기
        except:
            # 알림창이 없으면 무시
            pass
        
        # JSON 파일에서 제목 가져오기
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 새로운 에디터 방식 우선 시도
        try:
            # HTML 모드로 전환
            html_button = WebDriverWait(_driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#editor-mode-layer-btn-open"))
            )
            html_button.click()
            sleep(1)
            
            html_mode = WebDriverWait(_driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#editor-mode-html"))
            )
            html_mode.click()
            sleep(1)
            
            # 경고창 처리
            try:
                alert = WebDriverWait(_driver, 3).until(EC.alert_is_present())
                alert.accept()
                sleep(1)
            except:
                pass
                
            # 에디터 영역 찾기 및 내용 입력
            editor = WebDriverWait(_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".CodeMirror-lines"))
            )
            editor.click()
            sleep(1)
            
            # 기존 내용 선택하여 삭제 후 새 내용 붙여넣기
            actions = ActionChains(_driver)
            actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
            sleep(0.5)
            actions.key_down(Keys.DELETE).key_up(Keys.DELETE).perform()
            sleep(0.5)
            
            # 내용 붙여넣기
            pyperclip.copy(html_content)
            actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            sleep(2)
            
            # 제목 입력
            title_input = WebDriverWait(_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#post-title-inp"))
            )
            title_input.click()
            title_input.clear()
            title_input.send_keys(data['title'])
            sleep(1)
            
            # 카테고리 선택
            try:
                category_button = WebDriverWait(_driver, 8).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#category-btn"))
                )
                category_button.click()
                sleep(1)
                
                # 카테고리 목록에서 선택
                category_found = False
                category_list = WebDriverWait(_driver, 8).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".list-item"))
                )
                
                for category in category_list:
                    if category.text.strip() == tistory_category_name:
                        category.click()
                        category_found = True
                        break
                
                if not category_found:
                    print(f"카테고리 '{tistory_category_name}'를 찾지 못했습니다. 기본 카테고리로 진행합니다.")
                
                sleep(1)
            except Exception as cat_err:
                print(f"카테고리 선택 중 오류 발생 (무시하고 계속): {str(cat_err)}")
            
            # 발행 버튼 클릭 - 여러 선택자 시도
            publish_selectors = [
                ".btn-publish", 
                ".publish-btn", 
                "#publish-layer-btn", 
                "button.btn-publish", 
                "[data-test='publish-button']"
            ]
            
            publish_button = None
            for selector in publish_selectors:
                try:
                    publish_button = WebDriverWait(_driver, 8).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"발행 버튼 찾음: {selector}")
                    break
                except:
                    continue
            
            if not publish_button:
                # XPath로 시도
                xpath_options = [
                    "//button[contains(text(),'완료')]",
                    "//button[contains(text(),'발행')]",
                    "//div[contains(@class,'publish')]"
                ]
                
                for xpath in xpath_options:
                    try:
                        publish_button = WebDriverWait(_driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        print(f"XPath로 발행 버튼 찾음: {xpath}")
                        break
                    except:
                        continue
            
            if publish_button:
                publish_button.click()
                sleep(2)
                
                # 공개 발행 버튼 찾기
                confirm_selectors = [
                    ".btn-blue", 
                    "#publish-btn", 
                    "button.btn-default", 
                    "[type='submit']",
                    ".btn_ok"
                ]
                
                confirm_button = None
                for selector in confirm_selectors:
                    try:
                        confirm_button = WebDriverWait(_driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        print(f"확인 버튼 찾음: {selector}")
                        break
                    except:
                        continue
                
                if confirm_button:
                    confirm_button.click()
                    sleep(2)
                else:
                    print("확인 버튼을 찾지 못했지만 계속 진행합니다.")
                
                # 발행 완료 확인 - 여러 선택자 시도
                success_indicators = [".wrap_notice", ".notice_save", ".alert-success"]
                success = False
                
                for indicator in success_indicators:
                    try:
                        WebDriverWait(_driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, indicator))
                        )
                        success = True
                        break
                    except:
                        continue
                
                if success:
                    print(f"{C_GREEN}티스토리 포스팅 완료: {data['title']}{C_END}")
                else:
                    print(f"{C_YELLOW}포스팅 완료 메시지를 찾지 못했지만, 포스팅은 성공했을 수 있습니다.{C_END}")
            else:
                raise Exception("발행 버튼을 찾을 수 없습니다")
            
        except Exception as e:
            print(f"새 에디터 방식 실패, 기존 방식 시도: {str(e)}")
            
            # 페이지 새로고침 후 기존 방식 시도
            _driver.refresh()
            sleep(3)
            
            # 이전 작성 중이던 글 알림 처리 (새로고침 후)
            try:
                alert = WebDriverWait(_driver, 5).until(EC.alert_is_present())
                alert_text = alert.text
                print(f"알림창 발견 (새로고침 후): {alert_text}")
                alert.dismiss()  # 취소 버튼 클릭
                sleep(2)
            except:
                pass
            
            # HTML 모드로 전환 - 기존 방식
            try:
                html_button = WebDriverWait(_driver, 8).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn_html"))
                )
                html_button.click()
                sleep(1)
                
                # 기존 방식 에디터
                html_area = WebDriverWait(_driver, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.html"))
                )
                html_area.clear()
                sleep(0.5)
                pyperclip.copy(html_content)
                html_area.send_keys(Keys.CONTROL, 'v')
                sleep(1)
                
                # 제목 입력
                title_input = WebDriverWait(_driver, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#title"))
                )
                title_input.clear()
                title_input.send_keys(data['title'])
                sleep(1)
                
                # 카테고리 선택
                try:
                    category_select = WebDriverWait(_driver, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#category"))
                    )
                    for option in category_select.find_elements(By.TAG_NAME, "option"):
                        if option.text == tistory_category_name:
                            option.click()
                            break
                except Exception as cat_err:
                    print(f"카테고리 선택 중 오류 발생 (무시하고 계속): {str(cat_err)}")
                
                # 발행 버튼 클릭
                publish_button = WebDriverWait(_driver, 8).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn_publish"))
                )
                publish_button.click()
                sleep(2)
                
                print(f"{C_GREEN}티스토리 포스팅 완료 (기존 방식): {data['title']}{C_END}")
            except Exception as legacy_err:
                print(f"{C_RED}기존 방식에서도 오류 발생: {str(legacy_err)}{C_END}")
                return False
        
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