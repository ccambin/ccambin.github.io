# 특허 PDF 다운로더

Google Patents에서 특허번호로 검색하고 PDF를 다운로드하는 로컬 웹앱입니다.

## 실행 방법

```bash
cd patent-downloader
pip install -r requirements.txt
python app.py
```

브라우저에서 http://localhost:5050 접속 후 특허번호를 입력하세요. (예: `US10426424B2`, `EP1234567A1`, `KR1020190012345A`)

## 참고

- 개인 조회용 도구입니다. Google Patents에 짧은 시간에 대량 요청을 보내지 마세요.
- GitHub Pages는 정적 파일만 서빙하므로 이 앱은 온라인 사이트가 아닌 로컬(내 컴퓨터)에서 실행해야 합니다.
