# Success GoogleSheet

구글 시트와 유튜브 API를 활용하여 티스토리에 자동으로 포스팅하는 프로젝트입니다.

## 기능

- 유튜브 영상 검색 및 정보
- Gemini AI를 활용한 콘텐츠 생성
- 티스토리 자동 로그인 및 포스팅

## 설치 방법

1. 필요한 패키지 설치
```
pip install selenium webdriver-manager pyperclip google-api-python-client python-dotenv google-generativeai markdown2
```

2. `.env` 파일 설정
```
YOUTUBE_API_KEY=your_youtube_api_key
GEMINI_API_KEY=your_gemini_api_key
TISTORY_ID=your_tistory_id
TISTORY_PASSWORD=your_tistory_password
```

3. ChromeDriver 설치

## 사용 방법

```python
python tistory_auto_posting_selenium_sheet.py
```

## 주의사항

- 개인 인증 정보가 포함된 `.env` 파일은 반드시 비공개로 관리해야 합니다.
- Chrome 프로필은 로컬에서만 사용되며 GitHub에 업로드되지 않습니다.