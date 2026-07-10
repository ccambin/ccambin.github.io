import os
import sys
import threading
import webbrowser

from flask import Flask, render_template, request

import excel_store
import translator

# PyInstaller 번들 실행 시 템플릿 경로를 명시적으로 지정
BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))

PORT = 5860


@app.route('/')
def index():
    total = len(excel_store.load_words(excel_store.DEFAULT_PATH))
    return render_template('index.html', total=total)


@app.route('/process', methods=['POST'])
def process():
    text = request.form.get('mail_text', '').strip()
    if not text:
        total = len(excel_store.load_words(excel_store.DEFAULT_PATH))
        return render_template('index.html', total=total, error='중국어 메일 내용을 입력해주세요.')

    try:
        translation, entries = translator.process_mail(text)
    except Exception as e:
        total = len(excel_store.load_words(excel_store.DEFAULT_PATH))
        return render_template(
            'index.html', total=total,
            error='번역 처리 중 오류가 발생했습니다: {}'.format(e)
        )

    try:
        merged = excel_store.add_words_and_save(entries)
    except PermissionError as e:
        return render_template(
            'index.html', total=0, error=str(e),
            translation=translation
        )

    # 이번 메일 단어들의 누적 카운트를 표시용으로 조회
    rows = []
    for hanzi, pinyin_str, meaning in entries:
        count = merged.get(hanzi, {}).get('count', 1)
        saved_meaning = merged.get(hanzi, {}).get('meaning', meaning)
        rows.append({'hanzi': hanzi, 'pinyin': pinyin_str, 'meaning': saved_meaning, 'count': count})

    return render_template(
        'index.html',
        total=len(merged),
        translation=translation,
        rows=rows,
        original=text,
        excel_path=excel_store.DEFAULT_PATH,
    )


@app.route('/open_excel', methods=['POST'])
def open_excel():
    path = excel_store.DEFAULT_PATH
    if os.path.exists(path):
        os.startfile(path)
    total = len(excel_store.load_words(path))
    return render_template('index.html', total=total)


def open_browser():
    webbrowser.open('http://localhost:{}'.format(PORT))


if __name__ == '__main__':
    # 모델을 시작 시점에 미리 로드 (첫 요청 지연 방지)
    threading.Thread(target=translator.get_llm, daemon=True).start()
    if not os.environ.get('NO_BROWSER') and '--no-browser' not in sys.argv:
        threading.Timer(1.5, open_browser).start()
    app.run(port=PORT, debug=False)
