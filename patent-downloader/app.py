import io
import re

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, send_file, redirect, url_for

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/123.0 Safari/537.36'
}


PDF_BASE_URL = 'https://patentimages.storage.googleapis.com/'
MAX_KEYWORD_RESULTS = 20


def normalize_patent_number(raw):
    return re.sub(r'[\s\-]', '', raw).upper()


def clean_text(text):
    if not text:
        return ''
    return BeautifulSoup(text, 'html.parser').get_text().strip()


def search_patents_by_keyword(keyword):
    resp = requests.get(
        'https://patents.google.com/xhr/query',
        params={'url': 'q=' + keyword, 'exp': ''},
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    results_block = data.get('results') or {}
    total = results_block.get('total_num_results', 0)

    patents = []
    for cluster in results_block.get('cluster', []):
        for item in cluster.get('result', []):
            patent = item.get('patent', {})
            pdf_rel = patent.get('pdf')
            patents.append({
                'publication_number': patent.get('publication_number', ''),
                'title': clean_text(patent.get('title')),
                'snippet': clean_text(patent.get('snippet')),
                'assignee': patent.get('assignee', ''),
                'inventor': patent.get('inventor', ''),
                'pub_date': patent.get('publication_date', ''),
                'pdf_url': (PDF_BASE_URL + pdf_rel) if pdf_rel else None,
            })
            if len(patents) >= MAX_KEYWORD_RESULTS:
                break
        if len(patents) >= MAX_KEYWORD_RESULTS:
            break

    return patents, total


def fetch_patent_info(patent_number):
    url = 'https://patents.google.com/patent/{}/en'.format(patent_number)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    title_tag = soup.find('meta', attrs={'name': 'DC.title'})
    title = title_tag['content'].strip() if title_tag and title_tag.get('content') else patent_number

    abstract_tag = soup.find('meta', attrs={'name': 'DC.description'})
    abstract = abstract_tag['content'].strip() if abstract_tag and abstract_tag.get('content') else ''

    date_tag = soup.find('meta', attrs={'name': 'DC.date'})
    pub_date = date_tag['content'].strip() if date_tag and date_tag.get('content') else ''

    pdf_tag = soup.find('meta', attrs={'name': 'citation_pdf_url'})
    pdf_url = pdf_tag['content'] if pdf_tag and pdf_tag.get('content') else None

    return {
        'patent_number': patent_number,
        'title': title,
        'abstract': abstract,
        'pub_date': pub_date,
        'pdf_url': pdf_url,
        'page_url': url,
    }


@app.route('/')
def index():
    return render_template('index.html')


def render_patent_result(patent_number):
    try:
        info = fetch_patent_info(patent_number)
    except requests.exceptions.RequestException:
        return render_template(
            'index.html',
            error='조회에 실패했습니다. 특허번호가 정확한지 확인해주세요. (예: US10426424B2)'
        )

    if not info['pdf_url']:
        return render_template(
            'index.html',
            error='해당 특허의 PDF 링크를 찾을 수 없습니다. 특허번호를 다시 확인해주세요.'
        )

    return render_template('result.html', info=info)


@app.route('/search', methods=['POST'])
def search():
    raw_number = request.form.get('patent_number', '').strip()
    if not raw_number:
        return render_template('index.html', error='특허번호를 입력해주세요.')

    return render_patent_result(normalize_patent_number(raw_number))


@app.route('/patent/<patent_number>')
def patent_detail(patent_number):
    return render_patent_result(normalize_patent_number(patent_number))


@app.route('/search_keyword', methods=['POST'])
def search_keyword():
    keyword = request.form.get('keyword', '').strip()
    if not keyword:
        return render_template('index.html', error_kw='검색어를 입력해주세요.')

    try:
        results, total = search_patents_by_keyword(keyword)
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        if status in (429, 503):
            msg = 'Google 서버가 요청을 일시적으로 제한하고 있어요. 1분 정도 후 다시 시도해주세요.'
        else:
            msg = '검색 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
        return render_template('index.html', error_kw=msg)
    except (requests.exceptions.RequestException, ValueError):
        return render_template(
            'index.html',
            error_kw='검색 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
        )

    return render_template('results_list.html', keyword=keyword, results=results, total=total)


@app.route('/download')
def download():
    pdf_url = request.args.get('pdf_url')
    patent_number = request.args.get('patent_number', 'patent')
    if not pdf_url:
        return redirect(url_for('index'))

    resp = requests.get(pdf_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    return send_file(
        io.BytesIO(resp.content),
        mimetype='application/pdf',
        as_attachment=True,
        download_name='{}.pdf'.format(patent_number)
    )


if __name__ == '__main__':
    app.run(debug=True, port=5050)
