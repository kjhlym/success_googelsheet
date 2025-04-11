# Tistory YouTube Auto Posting

YouTube 영상 콘텐츠를 자동으로 티스토리 블로그에 포스팅하는 자동화 도구입니다.
Google Sheets에서 YouTube 영상 정보를 가져와서 Gemini AI로 콘텐츠를 생성하고, Selenium을 사용하여 티스토리에 자동으로 포스팅합니다.

## 주요 기능

- Google Sheets에서 YouTube 영상 정보 읽기
- YouTube API를 통한 영상 정보 수집
- Gemini AI를 활용한 블로그 콘텐츠 자동 생성
- Selenium을 사용한 티스토리 자동 로그인 및 포스팅
- 카테고리 자동 선택 및 발행

## 설치 방법

1. 저장소 클론

```bash
git clone https://github.com/yourusername/tistory-youtube-auto-posting.git
cd tistory-youtube-auto-posting
```

2. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

4. `.env` 파일 설정

```env
KAKAO_ID=your_kakao_id
KAKAO_PW=your_kakao_password
YOUTUBE_API_KEY=your_youtube_api_key
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SHEET_ID=your_sheet_id
```

## 사용 방법

1. Google Sheets 설정

   - 시트에 다음 열을 추가: select, URL, Title, Channel
   - YouTube 영상 정보 입력

2. 스크립트 실행

```bash
python tistory_auto_posting_selenium_sheet.py
```

## 주의사항

- `.env` 파일에 민감한 정보를 저장하므로 절대 공개하지 마세요
- ChromeProfile 폴더는 로그인 정보를 포함하므로 공유하지 마세요
- API 키는 안전하게 보관하고 주기적으로 갱신하세요

## 라이선스

MIT License
