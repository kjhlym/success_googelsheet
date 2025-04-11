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
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
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
CATEGORY = 'IT'

def get_google_sheets_service():
    """Google Sheets API 서비스 생성"""
    try:
        return build('sheets', 'v4', developerKey=GOOGLE_API_KEY)
    except Exception as e:
        print(f"\nGoogle Sheets API 서비스 생성 중 오류: {str(e)}")
        return None

def init_driver():
    """Chrome WebDriver 초기화"""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        
        user_data_dir = os.path.join(os.getcwd(), "ChromeProfile")
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument("--new-window")
        
        service = ChromeService()
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(LOADING_WAIT_TIME)
        print("Chrome WebDriver 초기화 성공")
        return driver
        
    except Exception as e:
        print(f"브라우저 초기화 실패: {str(e)}")
        return None

def tistory_login(driver):
    """티스토리 로그인"""
    try:
        # 이미 로그인되어 있는지 확인
        try:
            profile = driver.find_element(By.CLASS_NAME, 'link_profile')
            print('이미 로그인 되어있습니다.')
            return True
        except:
            pass
            
        driver.get('https://www.tistory.com/auth/login')
        driver.implicitly_wait(LOADING_WAIT_TIME)
        driver.find_element(By.CLASS_NAME, 'link_kakao_id').click()
        driver.implicitly_wait(LOADING_WAIT_TIME)
        
        if not KAKAO_ID or not KAKAO_PW:
            raise Exception("카카오 로그인 정보가 .env 파일에 설정되지 않았습니다.")
        
        # 카카오 아이디 입력
        id_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='loginId']"))
        )
        id_field.click()
        id_field.send_keys(KAKAO_ID)
        
        # 카카오 비밀번호 입력
        pw_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='password']"))
        )
        pw_field.click()
        pw_field.send_keys(KAKAO_PW)
        
        # 로그인 버튼 클릭
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        login_button.click()
        
        print(f'\n{C_BOLD}{C_RED}주의: 로그인 진행 중... 60초 동안 대기합니다.{C_END}')
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'link_profile'))
        )
        print("로그인 완료!")
        return True
        
    except Exception as e:
        print(f'로그인 과정에서 오류 발생: {str(e)}')
        return False

def get_youtube_video_info(video_id):
    """YouTube API를 사용하여 비디오 정보 가져오기"""
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        video_response = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        ).execute()
        
        if not video_response['items']:
            return None
            
        video_info = video_response['items'][0]
        return {
            'video_id': video_id,
            'title': video_info['snippet']['title'],
            'description': video_info['snippet']['description'],
            'channel_title': video_info['snippet']['channelTitle'],
            'upload_date': video_info['snippet']['publishedAt'],
            'view_count': video_info['statistics']['viewCount'],
            'tags': video_info['snippet'].get('tags', []),
            'search_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"YouTube API 호출 중 오류: {str(e)}")
        return None

def generate_content_with_gemini(video_data):
    """Gemini API를 사용하여 블로그 콘텐츠 생성"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            prompt = f"""
다음 YouTube 영상의 내용을 요약하여 블로그 포스트를 작성해주세요:

제목: {video_data['title']}
채널: {video_data['channel_title']}

# 블로그 글 작성 요구사항
- 객관적이고 교육적인 내용으로 작성
- 특정 상품이나 브랜드 홍보 없이 중립적으로 서술
- 주제와 관련된 기술적/과학적 설명 포함
- 짧은 문단으로 가독성 높게 작성
- 핵심 내용 요약 및 객관적 관점의 시사점 제시
"""

            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "max_output_tokens": 2048,
            }
            
            response = model.generate_content(prompt, generation_config=generation_config)
            
            # 응답 검증 및 처리
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                print(f"프롬프트가 차단됨: {response.prompt_feedback.block_reason}")
                raise Exception("프롬프트가 정책에 위배되어 차단되었습니다.")

            # 새로운 응답 구조 처리
            try:
                # GenerateContentResponse 객체에서 텍스트 추출 시도
                if hasattr(response, 'text'):
                    content = response.text
                elif hasattr(response, 'parts') and response.parts:
                    content = response.parts[0].text
                elif hasattr(response, 'candidates') and response.candidates:
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content'):
                            if hasattr(candidate.content, 'text'):
                                content = candidate.content.text
                                break
                            elif hasattr(candidate.content, 'parts') and candidate.content.parts:
                                content = candidate.content.parts[0].text
                                break
                else:
                    # 응답 객체의 구조 출력
                    print("응답 객체 구조 분석:")
                    for attr in dir(response):
                        if not attr.startswith('_'):  # 내부 속성 제외
                            try:
                                value = getattr(response, attr)
                                print(f"{attr}: {value}")
                            except:
                                continue

                    raise Exception("응답에서 텍스트를 추출할 수 없습니다")

            except Exception as e:
                print(f"응답 파싱 오류: {str(e)}")
                if retry_count < max_retries - 1:
                    print(f"응답 구조 처리 중 오류. 재시도 중... ({retry_count + 1}/{max_retries})")
                    retry_count += 1
                    sleep(2)
                    continue
                raise Exception("응답 구조를 처리할 수 없습니다")

            # 콘텐츠 검증
            if not content or len(content.strip()) < 100:
                if retry_count < max_retries - 1:
                    print(f"생성된 콘텐츠가 너무 짧습니다. 재시도 중... ({retry_count + 1}/{max_retries})")
                    retry_count += 1
                    sleep(2)
                    continue
                raise Exception("생성된 콘텐츠가 너무 짧습니다")

            # HTML 변환 및 스타일링
            try:
                html_content = markdown2.markdown(content)
            except Exception as e:
                print(f"Markdown 변환 오류: {str(e)}")
                html_content = f"<p>{content}</p>"  # 기본 HTML 포맷으로 폴백

            styled_html = f'''
            <div style="font-family:'Pretendard',sans-serif; line-height:1.8; color:#2d3748; width:100%;">
                <h1 style="color:#2563eb; font-size:2.2em; font-weight:700; margin-bottom:25px; border-bottom:2px solid #e2e8f0; padding-bottom:15px;">{video_data['title']}</h1>
                <div style="background-color:#ffffff; padding:20px; border-radius:8px; margin-bottom:20px; box-shadow:0 2px 8px rgba(26,115,232,0.1); border:1px solid rgba(26,115,232,0.2);">
                    <div style="color:#2c3e50; line-height:1.8; font-size:1.1em;">
                        {html_content}
                    </div>
                </div>
                <div style="margin-top:20px; font-size:0.9em; color:#64748b;">
                    <p>출처: <a href="https://www.youtube.com/watch?v={video_data['video_id']}" target="_blank">{video_data['channel_title']}</a></p>
                </div>
            </div>
            '''
            
            return styled_html
            
        except Exception as e:
            if retry_count < max_retries - 1:
                print(f"콘텐츠 생성 중 오류 (재시도 중 {retry_count + 1}/{max_retries}): {str(e)}")
                retry_count += 1
                sleep(2)
            else:
                print(f"콘텐츠 생성 중 오류: {str(e)}")
                return None

def tistory_write(driver, video_data):
    """티스토리에 글 작성"""
    try:
        # HTML 콘텐츠 생성
        html_content = generate_content_with_gemini(video_data)
        if not html_content:
            raise Exception("HTML 콘텐츠 생성 실패")
            
        # 티스토리 글쓰기 페이지로 이동
        driver.get(f"{tistory_blog_name}/manage/newpost/?type=post")
        sleep(LOADING_WAIT_TIME * 2)  # 페이지 로딩을 위해 대기 시간 증가
        
        # 이전 작성 중이던 글 알림 처리
        try:
            alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
            alert_text = alert.text
            print(f"알림창 발견: {alert_text}")
            if "저장된 글이 있습니다" in alert_text:
                alert.dismiss()  # 취소 버튼 클릭
            else:
                alert.accept()  # 확인 버튼 클릭
            sleep(2)
        except:
            pass
            
        # 새로운 에디터 방식 시도
        try:
            # HTML 모드로 전환
            html_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#editor-mode-layer-btn-open"))
            )
            html_button.click()
            sleep(2)
            
            html_mode = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#editor-mode-html"))
            )
            html_mode.click()
            sleep(2)
            
            # 경고창 처리
            try:
                alert = WebDriverWait(driver, 3).until(EC.alert_is_present())
                alert.accept()
                sleep(1)
            except:
                pass
                
            # 에디터 영역 찾기 및 내용 입력
            editor = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".CodeMirror-lines"))
            )
            editor.click()
            sleep(1)
            
            # 기존 내용 선택하여 삭제
            actions = ActionChains(driver)
            actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
            sleep(1)
            actions.send_keys(Keys.DELETE).perform()
            sleep(1)
            
            # 새 내용 붙여넣기
            pyperclip.copy(html_content)
            actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            sleep(2)
            
            # 제목 입력
            title_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#post-title-inp"))
            )
            title_input.click()
            title_input.clear()
            title_input.send_keys(video_data['title'])
            sleep(1)
            
            # 카테고리 선택
            try:
                category_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#category-btn"))
                )
                category_button.click()
                sleep(2)
                
                # 카테고리 목록에서 선택
                category_list = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".list-item"))
                )
                
                category_found = False
                for category in category_list:
                    if category.text.strip() == CATEGORY:
                        category.click()
                        category_found = True
                        print(f"카테고리 '{CATEGORY}' 선택됨")
                        sleep(2)
                        break
                
                if not category_found:
                    print(f"카테고리 '{CATEGORY}'를 찾지 못했습니다. 기본 카테고리로 진행합니다.")
                
            except Exception as cat_err:
                print(f"카테고리 선택 중 오류 발생 (무시하고 계속): {str(cat_err)}")
            
            # 발행 버튼 클릭 - 여러 선택자 시도
            publish_selectors = [
                ".btn-publish",
                ".publish-btn",
                "#publish-layer-btn",
                "button.btn-publish",
                "[data-test='publish-button']",
                "//button[contains(text(),'발행')]",  # XPath
                "//button[contains(@class,'publish')]"  # XPath
            ]
            
            publish_button = None
            for selector in publish_selectors:
                try:
                    if selector.startswith("//"):  # XPath
                        publish_button = WebDriverWait(driver, 8).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:  # CSS
                        publish_button = WebDriverWait(driver, 8).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    print(f"발행 버튼 찾음: {selector}")
                    break
                except:
                    continue
            
            if publish_button:
                # 버튼이 보이도록 스크롤
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", publish_button)
                sleep(2)
                
                # 클릭 시도
                try:
                    publish_button.click()
                except:
                    try:
                        driver.execute_script("arguments[0].click();", publish_button)
                    except:
                        ActionChains(driver).move_to_element(publish_button).click().perform()
                
                sleep(2)
                
                # 공개 설정 버튼 찾기
                confirm_selectors = [
                    ".btn-blue",
                    "#publish-btn",
                    "button.btn-default",
                    "[type='submit']",
                    ".btn_ok",
                    "//button[contains(text(),'확인')]",  # XPath
                    "//button[contains(@class,'blue')]"   # XPath
                ]
                
                confirm_button = None
                for selector in confirm_selectors:
                    try:
                        if selector.startswith("//"):  # XPath
                            confirm_button = WebDriverWait(driver, 8).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:  # CSS
                            confirm_button = WebDriverWait(driver, 8).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        print(f"확인 버튼 찾음: {selector}")
                        break
                    except:
                        continue
                
                if confirm_button:
                    try:
                        confirm_button.click()
                    except:
                        try:
                            driver.execute_script("arguments[0].click();", confirm_button)
                        except:
                            ActionChains(driver).move_to_element(confirm_button).click().perform()
                    
                    sleep(3)
                else:
                    print("확인 버튼을 찾지 못했지만 계속 진행합니다.")
                
                # 발행 완료 확인
                success_indicators = [
                    ".wrap_notice",
                    ".notice_save",
                    ".alert-success",
                    ".success_notice",
                    "//div[contains(@class,'success')]"  # XPath
                ]
                
                success = False
                for indicator in success_indicators:
                    try:
                        if indicator.startswith("//"):  # XPath
                            WebDriverWait(driver, 15).until(
                                EC.presence_of_element_located((By.XPATH, indicator))
                            )
                        else:  # CSS
                            WebDriverWait(driver, 15).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, indicator))
                            )
                        success = True
                        break
                    except:
                        continue
                
                if success:
                    print(f"{C_GREEN}티스토리 포스팅 완료: {video_data['title']}{C_END}")
                    return True
                else:
                    print(f"{C_YELLOW}포스팅 완료 메시지를 찾지 못했지만, 포스팅은 성공했을 수 있습니다.{C_END}")
                    return True
            else:
                raise Exception("발행 버튼을 찾을 수 없습니다")
            
        except Exception as e:
            print(f"새 에디터 방식 실패: {str(e)}")
            print("기존 방식으로 시도합니다...")
            
            # 페이지 새로고침
            driver.refresh()
            sleep(3)
            
            # 이전 작성 중이던 글 알림 처리
            try:
                alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
                alert.dismiss()
                sleep(2)
            except:
                pass
            
            # 기존 방식으로 시도
            try:
                # HTML 모드로 전환
                html_button = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn_html"))
                )
                html_button.click()
                sleep(2)
                
                # 에디터 찾기
                html_area = WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.html"))
                )
                html_area.clear()
                sleep(1)
                
                # 내용 붙여넣기
                pyperclip.copy(html_content)
                html_area.send_keys(Keys.CONTROL, 'v')
                sleep(2)
                
                # 제목 입력
                title_input = WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#title"))
                )
                title_input.clear()
                title_input.send_keys(video_data['title'])
                sleep(1)
                
                # 카테고리 선택
                try:
                    category_select = WebDriverWait(driver, 8).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#category"))
                    )
                    for option in category_select.find_elements(By.TAG_NAME, "option"):
                        if option.text.strip() == CATEGORY:
                            option.click()
                            print(f"카테고리 '{CATEGORY}' 선택됨 (기존 방식)")
                            break
                except Exception as cat_err:
                    print(f"카테고리 선택 중 오류 발생 (무시하고 계속): {str(cat_err)}")
                
                # 발행 버튼 클릭
                publish_button = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn_publish"))
                )
                publish_button.click()
                sleep(3)
                
                print(f"{C_GREEN}티스토리 포스팅 완료 (기존 방식): {video_data['title']}{C_END}")
                return True
                
            except Exception as legacy_err:
                print(f"{C_RED}기존 방식에서도 오류 발생: {str(legacy_err)}{C_END}")
                return False
        
    except Exception as e:
        print(f"{C_RED}티스토리 글쓰기 중 오류 발생: {str(e)}{C_END}")
        return False

def extract_video_id(url):
    """YouTube URL에서 video ID를 추출"""
    try:
        # URL 정규화
        url = url.strip()
        
        # 일반적인 YouTube URL 패턴
        if 'youtube.com/watch?v=' in url:
            video_id = url.split('watch?v=')[1]
        # 짧은 URL 패턴
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1]
        # 임베드 URL 패턴
        elif 'youtube.com/embed/' in url:
            video_id = url.split('youtube.com/embed/')[1]
        else:
            return None
            
        # 추가 파라미터 제거
        video_id = video_id.split('&')[0].split('?')[0]
        
        # video ID 유효성 검사 (기본 포맷: 11자의 영숫자)
        if video_id and len(video_id) == 11:
            return video_id
        return None
        
    except Exception:
        return None

def process_sheet(sheet_name):
    """구글 시트의 체크되지 않은 레코드 처리"""
    try:
        service = get_google_sheets_service()
        if not service:
            print("Google Sheets 서비스를 생성할 수 없습니다.")
            return
            
        sheet = service.spreadsheets()
        
        # 시트 데이터 읽기
        result = sheet.values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f'{sheet_name}!A:F',  # A부터 F열까지 읽기
            key=GOOGLE_API_KEY
        ).execute()
        values = result.get('values', [])
        
        if not values:
            print(f'시트 {sheet_name}에 데이터가 없습니다.')
            return
            
        # 헤더 확인 및 열 인덱스 찾기
        headers = values[0]
        try:
            select_col = headers.index('select')
            url_col = headers.index('URL')
            title_col = headers.index('Title')
            channel_col = headers.index('Channel')
        except ValueError as e:
            print(f'필요한 열을 찾을 수 없습니다: {str(e)}')
            return
            
        # Chrome 드라이버 초기화
        driver = init_driver()
        if not driver:
            return
            
        try:
            # 티스토리 로그인
            if not tistory_login(driver):
                raise Exception("티스토리 로그인 실패")
                
            # 체크되지 않은 레코드만 처리
            unchecked_rows = []
            for i, row in enumerate(values[1:], start=2):
                # 행이 충분한 열을 가지고 있는지 확인
                if len(row) <= max(select_col, url_col, title_col, channel_col):
                    continue
                    
                # select 열이 비어있거나 FALSE인 경우만 처리
                select_value = row[select_col].strip().upper() if len(row) > select_col and row[select_col] else ""
                if select_value not in ["TRUE", "✓", "V", "O"]:
                    unchecked_rows.append((i, row))
            
            if not unchecked_rows:
                print("처리할 체크되지 않은 행이 없습니다.")
                return
                
            print(f"\n처리할 행 수: {len(unchecked_rows)}")
            
            # 체크되지 않은 행 처리
            for i, row in unchecked_rows:
                try:
                    url = row[url_col].strip()
                    title = row[title_col].strip()
                    channel = row[channel_col].strip()
                    
                    print(f"\n처리 중인 영상:")
                    print(f"제목: {title}")
                    print(f"채널: {channel}")
                    print(f"URL: {url}")
                    
                    video_id = extract_video_id(url)
                    if not video_id:
                        print(f"행 {i}: 올바른 YouTube URL이 아니거나 video ID를 추출할 수 없습니다.")
                        continue
                        
                    # 비디오 정보 가져오기
                    video_data = get_youtube_video_info(video_id)
                    if not video_data:
                        print(f"행 {i}: 비디오 정보를 가져올 수 없습니다.")
                        continue
                        
                    # 티스토리 글쓰기
                    if tistory_write(driver, video_data):
                        # 성공 시 체크박스 업데이트
                        try:
                            # 체크박스 업데이트 요청
                            update_request = {
                                'requests': [
                                    {
                                        'updateCells': {
                                            'range': {
                                                'sheetId': 0,  # 첫 번째 시트
                                                'startRowIndex': i - 1,  # 0-based index
                                                'endRowIndex': i,
                                                'startColumnIndex': select_col,
                                                'endColumnIndex': select_col + 1
                                            },
                                            'rows': [
                                                {
                                                    'values': [
                                                        {
                                                            'userEnteredValue': {
                                                                'boolValue': True
                                                            }
                                                        }
                                                    ]
                                                }
                                            ],
                                            'fields': 'userEnteredValue'
                                        }
                                    }
                                ]
                            }
                            
                            # 체크박스 업데이트 실행
                            sheet.batchUpdate(
                                spreadsheetId=GOOGLE_SHEET_ID,
                                body=update_request,
                                key=GOOGLE_API_KEY
                            ).execute()
                            
                            print(f"{C_GREEN}행 {i}: 체크박스 업데이트 완료{C_END}")
                            sleep(2)
                        except Exception as update_err:
                            print(f"{C_RED}행 {i}: 체크박스 업데이트 실패: {str(update_err)}{C_END}")
                        
                except Exception as row_err:
                    print(f"행 {i} 처리 중 오류: {str(row_err)}")
                    continue
                    
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"시트 처리 중 오류: {str(e)}")

def main():
    """메인 함수"""
    try:
        print("\nSTART...")
        
        # 환경 변수 확인
        if not all([GOOGLE_API_KEY, GOOGLE_SHEET_ID, YOUTUBE_API_KEY, GEMINI_API_KEY, KAKAO_ID, KAKAO_PW]):
            print("오류: .env 파일에 필요한 설정이 없습니다.")
            return
            
        # 구글 시트 서비스 초기화
        service = get_google_sheets_service()
        if not service:
            print("프로그램을 종료합니다.")
            return
            
        # Chrome 드라이버 초기화 (한 번만)
        driver = init_driver()
        if not driver:
            print("브라우저 초기화 실패")
            return
            
        try:
            # 티스토리 로그인 (한 번만)
            print("\n티스토리 로그인 시도...")
            if not tistory_login(driver):
                raise Exception("티스토리 로그인 실패")
            print("로그인 성공! 글 작성을 시작합니다.\n")
            
            # 모든 시트 목록 가져오기
            try:
                spreadsheet = service.spreadsheets().get(
                    spreadsheetId=GOOGLE_SHEET_ID,
                    key=GOOGLE_API_KEY
                ).execute()
                sheets = spreadsheet.get('sheets', [])
            except Exception as e:
                raise Exception(f"스프레드시트 정보 가져오기 실패: {str(e)}")
            
            # 각 시트 처리
            for sheet in sheets:
                sheet_name = sheet['properties']['title']
                print(f'\n{C_BOLD}{C_BLUE}시트 처리 중: {sheet_name}{C_END}')
                
                try:
                    # 시트 데이터 읽기
                    result = service.spreadsheets().values().get(
                        spreadsheetId=GOOGLE_SHEET_ID,
                        range=f'{sheet_name}!A:F',
                        key=GOOGLE_API_KEY
                    ).execute()
                    values = result.get('values', [])
                    
                    if not values:
                        print(f'시트 {sheet_name}에 데이터가 없습니다.')
                        continue
                        
                    # 헤더 확인 및 열 인덱스 찾기
                    headers = values[0]
                    try:
                        select_col = headers.index('select')
                        url_col = headers.index('URL')
                        title_col = headers.index('Title')
                        channel_col = headers.index('Channel')
                    except ValueError as e:
                        print(f'필요한 열을 찾을 수 없습니다: {str(e)}')
                        continue
                    
                    # 체크되지 않은 레코드만 처리
                    unchecked_rows = []
                    for i, row in enumerate(values[1:], start=2):
                        if len(row) <= max(select_col, url_col, title_col, channel_col):
                            continue
                        
                        select_value = row[select_col].strip().upper() if len(row) > select_col and row[select_col] else ""
                        if select_value not in ["TRUE", "✓", "V", "O"]:
                            unchecked_rows.append((i, row))
                    
                    if not unchecked_rows:
                        print(f"{C_YELLOW}처리할 체크되지 않은 행이 없습니다.{C_END}")
                        continue
                    
                    print(f"\n{C_GREEN}처리할 행 수: {len(unchecked_rows)}{C_END}")
                    
                    # 체크되지 않은 행 처리
                    for i, row in unchecked_rows:
                        try:
                            url = row[url_col].strip()
                            title = row[title_col].strip()
                            channel = row[channel_col].strip()
                            
                            print(f"\n{C_CYAN}처리 중인 영상:{C_END}")
                            print(f"제목: {title}")
                            print(f"채널: {channel}")
                            print(f"URL: {url}")
                            
                            video_id = extract_video_id(url)
                            if not video_id:
                                print(f"{C_RED}행 {i}: 올바른 YouTube URL이 아니거나 video ID를 추출할 수 없습니다.{C_END}")
                                continue
                            
                            # 비디오 정보 가져오기
                            video_data = get_youtube_video_info(video_id)
                            if not video_data:
                                print(f"{C_RED}행 {i}: 비디오 정보를 가져올 수 없습니다.{C_END}")
                                continue
                            
                            # 티스토리 글쓰기
                            if tistory_write(driver, video_data):
                                # 성공 시 체크박스 업데이트
                                try:
                                    update_request = {
                                        'requests': [{
                                            'updateCells': {
                                                'range': {
                                                    'sheetId': sheet['properties']['sheetId'],
                                                    'startRowIndex': i - 1,
                                                    'endRowIndex': i,
                                                    'startColumnIndex': select_col,
                                                    'endColumnIndex': select_col + 1
                                                },
                                                'rows': [{
                                                    'values': [{
                                                        'userEnteredValue': {
                                                            'boolValue': True
                                                        }
                                                    }]
                                                }],
                                                'fields': 'userEnteredValue'
                                            }
                                        }]
                                    }
                                    
                                    service.spreadsheets().batchUpdate(
                                        spreadsheetId=GOOGLE_SHEET_ID,
                                        body=update_request,
                                        key=GOOGLE_API_KEY
                                    ).execute()
                                    
                                    print(f"{C_GREEN}행 {i}: 체크박스 업데이트 완료{C_END}")
                                    sleep(2)
                                except Exception as update_err:
                                    print(f"{C_RED}행 {i}: 체크박스 업데이트 실패: {str(update_err)}{C_END}")
                            
                        except Exception as row_err:
                            print(f"{C_RED}행 {i} 처리 중 오류: {str(row_err)}{C_END}")
                            continue
                    
                except Exception as sheet_err:
                    print(f"{C_RED}시트 '{sheet_name}' 처리 중 오류: {str(sheet_err)}{C_END}")
                    continue
                
        finally:
            # 모든 처리가 끝난 후 브라우저 종료
            print("\n모든 처리가 완료되었습니다.")
            driver.quit()
            
    except Exception as e:
        print(f"{C_RED}처리 중 오류 발생: {str(e)}{C_END}")
        if 'driver' in locals():
            driver.quit()

if __name__ == '__main__':
    main()