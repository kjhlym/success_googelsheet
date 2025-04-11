import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
import time

# 환경 변수 로드
load_dotenv()

# Google API 설정
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')  # Custom Search Engine ID
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')  # 스프레드시트 ID

def get_google_sheets_service():
    """Google Sheets API 서비스 생성"""
    try:
        return build('sheets', 'v4', developerKey=GOOGLE_API_KEY)
    except Exception as e:
        print(f"\nGoogle Sheets API 서비스 생성 중 오류: {str(e)}")
        return None

def search_youtube_url(query):
    """Google Custom Search API를 사용하여 YouTube URL 검색"""
    try:
        service = build('customsearch', 'v1', developerKey=GOOGLE_API_KEY)
        result = service.cse().list(
            q=query + ' site:youtube.com',
            cx=GOOGLE_CSE_ID,
            num=1
        ).execute()

        if 'items' in result and len(result['items']) > 0:
            url = result['items'][0]['link']
            if 'youtube.com/watch?v=' in url:
                return url
    except Exception as e:
        print(f"YouTube URL 검색 중 오류 발생: {str(e)}")
    return None

def process_sheet(spreadsheet_id, sheet_name):
    """시트의 체크되지 않은 레코드 처리"""
    try:
        service = get_google_sheets_service()
        if not service:
            print("Google Sheets 서비스를 생성할 수 없습니다.")
            return

        sheet = service.spreadsheets()

        # 시트 데이터 읽기 (모든 열 가져오기)
        try:
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!A:G',  # A부터 G까지 (상태 열까지)
                key=GOOGLE_API_KEY
            ).execute()
            values = result.get('values', [])
        except Exception as e:
            print(f"시트 데이터 읽기 중 오류: {str(e)}")
            return

        if not values:
            print(f'시트 {sheet_name}에 데이터가 없습니다.')
            return

        # 헤더 확인 및 열 인덱스 찾기
        headers = values[0]
        select_col = headers.index('select') if 'select' in headers else None
        title_col = headers.index('Title') if 'Title' in headers else None
        url_col = headers.index('URL') if 'URL' in headers else None
        channel_col = headers.index('Channel') if 'Channel' in headers else None
        published_col = headers.index('Published Date') if 'Published Date' in headers else None
        status_col = headers.index('상태') if '상태' in headers else None

        if None in [select_col, title_col, url_col]:
            print('필요한 열을 찾을 수 없습니다.')
            return

        # 체크되지 않은 레코드 처리
        for i, row in enumerate(values[1:], start=2):
            try:
                # select 열이 비어있거나 FALSE인 경우에만 처리
                is_not_selected = len(row) <= select_col or not row[select_col] or row[select_col].lower() == 'false'
                
                if is_not_selected:
                    # URL이 비어있는 경우에만 검색
                    if len(row) <= url_col or not row[url_col]:
                        title = row[title_col]
                        # 채널명이 있다면 검색어에 포함
                        if len(row) > channel_col and row[channel_col]:
                            search_query = f"{title} {row[channel_col]}"
                        else:
                            search_query = title
                            
                        youtube_url = search_youtube_url(search_query)
                        
                        if youtube_url:
                            try:
                                # URL 업데이트
                                sheet.values().update(
                                    spreadsheetId=spreadsheet_id,
                                    range=f'{sheet_name}!{chr(65+url_col)}{i}',
                                    valueInputOption='RAW',
                                    body={'values': [[youtube_url]]},
                                    key=GOOGLE_API_KEY
                                ).execute()
                                
                                # select 열 체크 표시
                                sheet.values().update(
                                    spreadsheetId=spreadsheet_id,
                                    range=f'{sheet_name}!{chr(65+select_col)}{i}',
                                    valueInputOption='RAW',
                                    body={'values': [['TRUE']]},
                                    key=GOOGLE_API_KEY
                                ).execute()
                                
                                print(f'행 {i}: YouTube URL 업데이트 완료 - {youtube_url}')
                            except Exception as e:
                                print(f"행 {i} 업데이트 중 오류: {str(e)}")
                            
                            # API 호출 제한 고려
                            time.sleep(2)
                        else:
                            print(f'행 {i}: YouTube URL을 찾을 수 없습니다 - {title}')

            except Exception as e:
                print(f"행 {i} 처리 중 오류 발생: {str(e)}")
                continue

    except Exception as e:
        print(f"시트 처리 중 오류 발생: {str(e)}")

def main():
    # .env 파일의 값 확인
    if not all([GOOGLE_CSE_ID, GOOGLE_API_KEY, GOOGLE_SHEET_ID]):
        print("오류: .env 파일에 필요한 설정이 없습니다.")
        print(f"GOOGLE_CSE_ID: {GOOGLE_CSE_ID}")
        print(f"GOOGLE_API_KEY: {GOOGLE_API_KEY}")
        print(f"GOOGLE_SHEET_ID: {GOOGLE_SHEET_ID}")
        return
    
    print("설정된 값:")
    print(f"GOOGLE_CSE_ID: {GOOGLE_CSE_ID}")
    print(f"GOOGLE_API_KEY: {GOOGLE_API_KEY}")
    print(f"GOOGLE_SHEET_ID: {GOOGLE_SHEET_ID}")
    
    try:
        service = get_google_sheets_service()
        if not service:
            print("프로그램을 종료합니다.")
            return
            
        # 모든 시트 목록 가져오기
        try:
            spreadsheet = service.spreadsheets().get(
                spreadsheetId=GOOGLE_SHEET_ID,
                key=GOOGLE_API_KEY
            ).execute()
            sheets = spreadsheet.get('sheets', [])
        except Exception as e:
            print(f"스프레드시트 정보 가져오기 실패: {str(e)}")
            return
        
        for sheet in sheets:
            sheet_name = sheet['properties']['title']
            print(f'\n시트 처리 중: {sheet_name}')
            process_sheet(GOOGLE_SHEET_ID, sheet_name)
            
    except Exception as e:
        print(f"처리 중 오류 발생: {str(e)}")

if __name__ == '__main__':
    main() 