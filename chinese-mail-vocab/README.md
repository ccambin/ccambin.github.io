# 중국어 메일 번역 & 단어장

중국어 메일을 붙여넣으면 ① 한국어 번역 ② 단어별 병음/한국어 뜻을 정리하고, ③ 엑셀 단어장에 누적 저장하는 로컬 웹 프로그램입니다.

**인터넷이 전혀 없는 PC에서도 동작합니다** — 번역 엔진(Qwen2.5-1.5B 로컬 AI 모델)이 프로그램 안에 포함되어 있습니다.

## 주요 기능

- 중국어 메일 전문 → 자연스러운 한국어 번역
- 메일 속 단어 자동 추출(jieba) + 병음 표기(pypinyin, 성조 포함) + 한국어 뜻(로컬 AI)
- 엑셀 단어장 자동 누적 저장
  - 파일 위치: `내 문서\ChineseWordBook\chinese_words.xlsx`
  - 병음 알파벳 오름차순 자동 정렬
  - 반복 단어는 "누적 횟수" 자동 카운트
  - 이미 있는 단어의 뜻이 비어있으면 다음 입력 때 자동 보완

## 설치해서 사용 (인터넷 없는 PC)

1. `ChineseMailVocabSetup.exe` 실행 → 설치
2. 바탕화면의 "중국어 메일 번역 & 단어장" 아이콘 실행
3. 잠시 후 브라우저가 자동으로 열립니다 (`http://localhost:5860`)
4. 중국어 메일을 붙여넣고 "번역 및 저장" 클릭

### 최소 사양

- Windows 10/11 64비트
- RAM 8GB 이상 권장 (AI 모델 구동)
- 디스크 여유 공간 3GB 이상
- 인터넷 불필요

## 개발자용: 소스로 실행

```bash
cd chinese-mail-vocab
pip install -r requirements.txt
# 모델 다운로드 (최초 1회, 인터넷 필요)
python build/download_model.py
python app.py
```

## 빌드 방법 (개발 PC)

```bash
# 1. exe 빌드 (dist/ChineseMailVocab/ 폴더 생성)
pyinstaller build/app.spec --distpath dist --workpath build/pyinstaller-work --noconfirm

# 2. 설치파일 빌드 (Inno Setup 필요)
iscc build/installer.iss
# → Output/ChineseMailVocabSetup.exe
```

## 참고

- 처리 속도: 메일 1건당 약 10~40초 (PC 성능에 따라 다름)
- 번역/뜻 품질: 1.5B 경량 AI 모델이라 간혹 부정확한 뜻이 나올 수 있습니다. 반복 입력 시 잘못된 뜻은 자동으로 교체를 시도합니다.
- 모델 파일(`models/*.gguf`, 약 1GB)은 git에 포함되지 않습니다. `build/download_model.py`로 받으세요.
