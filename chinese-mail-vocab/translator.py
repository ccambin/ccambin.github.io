import os
import re
import sys
import threading

import jieba
from pypinyin import pinyin, Style

# PyInstaller onefile 실행 시 리소스가 임시폴더(_MEIPASS)에 풀림
BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'qwen2.5-1.5b-instruct-q4_k_m.gguf')

HANZI_RE = re.compile(r'^[一-鿿]+$')

_llm = None
_llm_lock = threading.Lock()


def get_llm():
    """모델을 최초 1회만 로드해 재사용한다 (로드에 수 초 소요)."""
    global _llm
    with _llm_lock:
        if _llm is None:
            from llama_cpp import Llama
            _llm = Llama(
                model_path=MODEL_PATH,
                n_ctx=4096,
                n_threads=max(2, (os.cpu_count() or 4) - 1),
                verbose=False,
            )
    return _llm


def segment_words(text):
    """jieba로 분절 후 한자로만 이루어진 고유 단어 리스트를 등장 순서대로 반환."""
    seen = []
    for token in jieba.cut(text):
        token = token.strip()
        if token and HANZI_RE.match(token) and token not in seen:
            seen.append(token)
    return seen


def get_pinyin(word):
    """성조 부호 포함 병음 (예: nǐ hǎo). LLM이 아닌 pypinyin으로 결정적으로 계산."""
    syllables = pinyin(word, style=Style.TONE)
    return ' '.join(s[0] for s in syllables)


def _chat(system, user, max_tokens=2048):
    llm = get_llm()
    with _llm_lock:
        result = llm.create_chat_completion(
            messages=[
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user},
            ],
            max_tokens=max_tokens,
            temperature=0.1,
        )
    return result['choices'][0]['message']['content'].strip()


def _hangul_ratio(s):
    letters = [c for c in s if not c.isspace()]
    if not letters:
        return 1.0
    hangul = [c for c in letters if '가' <= c <= '힣']
    return len(hangul) / len(letters)


TRANSLATE_SYSTEM = (
    'You are a Chinese-to-Korean translator. Translate the Chinese sentence '
    'into natural Korean. Output ONLY Korean.'
)


def translate_mail(text):
    """메일 전문을 한국어로 번역.

    소형 모델이 긴 다중 문단 입력에서 언어가 흔들리는 문제가 있어,
    줄 단위로 나눠 번역하고 한글 비율이 낮으면 1회 재시도한다.
    """
    results = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            results.append('')
            continue
        translated = _chat(TRANSLATE_SYSTEM, line, max_tokens=512)
        if _hangul_ratio(translated) < 0.5:
            translated = _chat(
                TRANSLATE_SYSTEM, 'Translate to KOREAN (한국어로만): ' + line, max_tokens=512
            )
        results.append(translated)
    return '\n'.join(results).strip()


def _contains_hangul(s):
    return any('가' <= c <= '힣' for c in s)


def _parse_meanings_lines(raw, words):
    """'단어 = 뜻' 줄 형식 응답을 파싱. 한글이 포함된 뜻만 유효 처리. {단어: 뜻} dict 반환."""
    meanings = {}
    word_set = set(words)
    for line in raw.splitlines():
        if '=' not in line:
            continue
        left, _, right = line.partition('=')
        word = left.strip().strip('"\'`-* ')
        meaning = right.strip().strip('"\'`')
        if word in word_set and meaning and _contains_hangul(meaning):
            meanings[word] = meaning
    return meanings


MEANING_SYSTEM = (
    'You are a Chinese-Korean dictionary. For each Chinese word, give a concise '
    'Korean meaning (under 10 characters, in Hangul only). Output format: one per line, '
    '"word = meaning". No other text.'
)


def get_meanings(words, batch_size=15):
    """단어 리스트에 대한 한국어 뜻을 LLM으로 조회. {단어: 뜻} dict 반환."""
    meanings = {}
    for i in range(0, len(words), batch_size):
        batch = words[i:i + batch_size]
        raw = _chat(MEANING_SYSTEM, '\n'.join(batch), max_tokens=1024)
        parsed = _parse_meanings_lines(raw, batch)
        missing = [w for w in batch if w not in parsed]
        if missing:
            # 누락/무효 단어는 배치로 1회 재시도
            raw2 = _chat(MEANING_SYSTEM, '\n'.join(missing), max_tokens=1024)
            parsed.update(_parse_meanings_lines(raw2, missing))
        # 그래도 남은 단어는 하나씩 개별 조회 후 응답에서 한글만 추출
        for w in [w for w in batch if w not in parsed]:
            raw3 = _chat(MEANING_SYSTEM, w, max_tokens=128)
            single = _extract_hangul_meaning(raw3)
            if single:
                parsed[w] = single
        meanings.update(parsed)
    return meanings


def _extract_hangul_meaning(raw):
    """개별 단어 조회 응답에서 한글 뜻만 추출 (모델이 형식을 안 지키는 경우 대비)."""
    # '=' 오른쪽 우선, 없으면 전체에서 첫 한글 시퀀스
    target = raw.partition('=')[2] if '=' in raw else raw
    match = re.search(r'[가-힣][가-힣\s]{0,12}', target) or re.search(r'[가-힣][가-힣\s]{0,12}', raw)
    return match.group(0).strip() if match else ''


def process_mail(text):
    """전체 파이프라인: 번역 + 분절 + 병음 + 뜻. 반환: (번역문, [(한자, 병음, 뜻), ...])"""
    translation = translate_mail(text)
    words = segment_words(text)
    meanings = get_meanings(words)
    entries = [(w, get_pinyin(w), meanings.get(w, '')) for w in words]
    return translation, entries
