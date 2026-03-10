import streamlit as st
import anthropic
import re
import base64
import io
import streamlit.components.v1 as components
from exam_data import EXAM_DATA

# ─── 페이지 설정 ───
st.set_page_config(
    page_title="환경직 모범답안 생성기",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

.stApp { background: #f5f2eb; }
[data-testid="stSidebar"] { background: #fffefb; border-right: 1px solid #d4cfc2; }

.main-header {
    background: linear-gradient(135deg, #2d5a27 0%, #3d7a33 100%);
    color: white; padding: 20px 28px; border-radius: 14px;
    margin-bottom: 22px; display: flex; align-items: center; gap: 16px;
    box-shadow: 0 4px 20px rgba(45,90,39,0.25);
}
.main-header h1 { font-family:'Noto Serif KR',serif; font-size:22px; font-weight:700; margin:0; }
.main-header p { font-size:12px; opacity:0.8; margin:4px 0 0; }

.answer-meta {
    background:#f5edd8; border:1px solid #e0cc99; border-radius:9px;
    padding:12px 18px; margin-bottom:14px;
}
.answer-meta strong { color:#1a1a14; font-size:14px; display:block; margin-bottom:3px; }
.answer-meta span { font-size:11px; color:#8b6914; }
.answer-box {
    background:#fff; border:1px solid #d4cfc2; border-radius:10px;
    padding:28px 32px; font-family:'Noto Serif KR',serif;
    font-size:14.5px; line-height:2.05; color:#1a1a14;
    white-space:pre-wrap; word-break:keep-all;
    box-shadow:0 2px 12px rgba(0,0,0,0.06);
}
.stream-box {
    background:#fff; border:2px solid #4a7c3f; border-radius:10px;
    padding:24px 28px; font-family:'Noto Serif KR',serif;
    font-size:14px; line-height:2.0; color:#1a1a14;
    white-space:pre-wrap; word-break:keep-all; min-height:200px;
}
.empty-state { text-align:center; padding:70px 30px; color:#6b6657; }
.empty-state .icon { font-size:48px; opacity:0.3; margin-bottom:14px; }
.empty-state h3 { font-size:15px; font-weight:600; color:#1a1a14; opacity:0.5; margin-bottom:8px; }
.empty-state p { font-size:12.5px; line-height:1.7; }

.stButton > button { font-family:'Noto Sans KR',sans-serif !important; font-weight:600 !important; border-radius:8px !important; }
div[data-testid="stRadio"] label { font-size:13px; }
</style>
""", unsafe_allow_html=True)


# ─── 상수 ───
EIAS_DATA_AVAILABLE = list(range(1, 17))
GOSI_YEARS = list(range(2025, 2001, -1))
GOSI_SUBJECTS_REQUIRED = ["환경화학", "환경계획", "상하수도공학"]
GOSI_SUBJECTS_ELECTIVE = ["소음진동학", "폐기물처리", "환경미생물학", "환경영향평가론", "대기오염관리", "수질오염관리"]
GOSI_ALL_SUBJECTS = GOSI_SUBJECTS_REQUIRED + GOSI_SUBJECTS_ELECTIVE
PDF_BASE = "data"

EIAS_PDF_MAP = {
    1: "제1회_환경영향평가사_필기시험_기출문제_1.pdf",
    2: "제2회_환경영향평가사_필기시험_기출문제.pdf",
    3: "제3회_환경영향평가사_필기시험_기출문제.pdf",
    4: "제4회_환경영향평가사_필기시험_기출문제.pdf",
    5: "제5회_환경영향평가사_필기시험_기출문제.pdf",
    6: "제6회_환경영향평가사_필기시험_기출문제.pdf",
    7: "제7회_환경영향평가사_필기시험_기출문제.pdf",
    8: "제8회_환경영향평가사_필기시험_기출문제.pdf",
    9: "제9회_필기시험_문제지.pdf",
    10: "제10회_필기시험_문제지.pdf",
    11: "제11회_필기시험_문제지.pdf",
    12: "제12회_필기시험_문제지.pdf",
    13: "제13회_필기시험_문제지.pdf",
    14: "제14회_필기시험_문제지.pdf",
    15: "제15회_필기시험_문제지_최종.pdf",
    16: "제16회_필기시험_문제지_최종완료_hwp.pdf",
    17: "제17회_필기시험_문제지.pdf",
    18: "제18회_필기시험_문제지.pdf",
    19: "제19회_필기시험_문제지_1_1.pdf",
    20: "제20회_필기시험_문제.pdf",
    21: "제21회_환경영향평가사_필기시험_기출문제.pdf",
    22: "제22회_환경영향평가사_필기시험_기출문제_1.pdf",
    27: "제27회_필기시험_실전문제_해설_수정__2026_02_22_21_30_39.pdf",
}
EIAS_PDF_AVAILABLE = set(EIAS_PDF_MAP.keys())

GOSI_PDF_MAP = {
    "환경화학": {
        2002: "01__2002년_환경화학.pdf", 2004: "01__2004년_환경화학.pdf",
        2005: "01__2005년_환경화학.pdf", 2006: "01__2006년_환경화학.pdf",
        2007: "070825_행정고등고시기술직_2차_시험_환경화학.pdf",
        2022: "환경화학.pdf", 2023: "230705_5급_기술_2차_환경화학.pdf",
        2024: "240709_5급_과기_2차_환경화학.pdf", 2025: "250704_5급_2차_과기_환경화학.pdf",
    },
    "환경계획": {
        2002: "02__2002년_환경계획.pdf", 2003: "02__2003_환경계획.pdf",
        2004: "02__2004년_환경계획.pdf", 2005: "02__2005년_환경계획.pdf",
        2006: "02__2006년_환경계획.pdf", 2007: "070825_행정고등고시기술직_2차_시험_환경계획.pdf",
        2022: "환경계획.pdf", 2023: "230705_5급_기술_2차_환경계획.pdf",
        2024: "240709_5급_과기_2차_환경계획.pdf", 2025: "250704_5급_2차_과기_환경계획.pdf",
    },
    "상하수도공학": {
        2002: "03__2002년_상하수도공학.pdf", 2004: "03__2004년_상하수도공학.pdf",
        2005: "03__2005년_상하수도공학.pdf", 2006: "03__2006년_상하수도공학.pdf",
        2007: "070825_행정고등고시기술직_2차_시험_상하수도공학.pdf",
        2022: "상하수도공학.pdf", 2023: "230705_5급_기술_2차_상하수도공학.pdf",
        2024: "240709_5급_과기_2차_상하수도공학.pdf", 2025: "250704_5급_2차_과기_상하수도공학.pdf",
    },
    "소음진동학": {
        2002: "2002년_소음진동학.pdf", 2004: "2004년_소음진동학.pdf",
        2005: "2005년_소음진동학.pdf", 2006: "2006년_소음진동학.pdf", 2022: "소음진동학.pdf",
    },
    "폐기물처리": {
        2002: "2002년_폐기물처리.pdf", 2004: "2004년_폐기물처리.pdf",
        2005: "2005년_폐기물처리.pdf", 2006: "2006년_폐기물처리.pdf",
        2022: "폐기물처리.pdf", 2023: "230705_5급_기술_2차_폐기물처리.pdf",
        2024: "240709_5급_과기_2차_폐기물처리.pdf",
    },
    "환경미생물학": {
        2002: "2002년_환경미생물학.pdf", 2004: "2004년_환경미생물학.pdf",
        2005: "2005년_환경미생물학.pdf", 2006: "2006년_환경미생물학.pdf",
        2022: "환경미생물학.pdf", 2023: "230705_5급_기술_2차_환경미생물학.pdf",
        2024: "240709_5급_과기_2차_환경미생물학.pdf",
    },
    "환경영향평가론": {
        2002: "2002년_환경영향평가론.pdf", 2004: "2004년_환경영향평가론.pdf",
        2005: "2005년_환경영향평가론.pdf", 2006: "2006년_환경영향평가론.pdf",
        2022: "환경영향평가론.pdf", 2023: "230705_5급_기술_2차_환경영향평가론.pdf",
        2024: "240709_5급_과기_2차_환경영향평가론.pdf",
    },
    "대기오염관리": {
        2002: "2002년_대기오염관리.pdf", 2004: "2004년_대기오염관리.pdf",
        2005: "2005년_대기오염관리.pdf", 2006: "2006년_대기오염관리.pdf",
        2022: "대기오염관리.pdf", 2023: "230705_5급_기술_2차_대기오염관리.pdf",
        2024: "240709_5급_과기_2차_대기오염관리.pdf",
    },
    "수질오염관리": {
        2002: "2002년_수질오염관리.pdf", 2004: "2004년_수질오염관리.pdf",
        2005: "2005년_수질오염관리.pdf", 2006: "2006년_수질오염관리.pdf",
        2022: "수질오염관리.pdf", 2023: "230705_5급_기술_2차_수질오염관리.pdf",
        2024: "240709_5급_과기_2차_수질오염관리.pdf",
    },
}


# ─── 파싱 헬퍼 ───
_SUBJ_MAP = {'환경정책': '환경정책', '국토환경계획': '국토계획', '환경영향평가실무': '실무', '환경영향평가제도': '제도'}

def _is_subj_header(line):
    line_ns = line.replace(' ', '')
    if '수험번호' in line or line_ns.startswith('과목'):
        return True
    for k in _SUBJ_MAP:
        if line_ns == k.replace(' ','') or line_ns == f'과목{k.replace(" ","")}':
            return True
    return False

def _extract_score(text):
    m = re.search(r'\[(\d+)점\]', text)
    if m: return m.group(1)
    m = re.search(r'\[(\d+)\s+\]', text)
    if m: return m.group(1)
    return ''

def parse_eias_questions(text):
    questions = []
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    cur_subj = ''
    expanded = []
    for line in lines:
        line = line.strip()
        if not line:
            expanded.append(''); continue
        if _is_subj_header(line):
            expanded.append(line); continue
        parts = re.split(r'(?<!\d)(?=\b\d{1,2}\.[^\d])', line)
        if len(parts) > 1:
            for p in parts:
                p = p.strip()
                if p: expanded.append(p)
        else:
            expanded.append(line)
    i = 0
    while i < len(expanded):
        line = expanded[i].strip()
        if _is_subj_header(line):
            line_ns = line.replace(' ', '')
            for k, v in _SUBJ_MAP.items():
                if k.replace(' ','') in line_ns:
                    cur_subj = v
            i += 1; continue
        if ('필수문제' in line) and not re.match(r'^\d', line) and not re.match(r'^[□(다\s]', line):
            clean = line.strip()
            score = _extract_score(clean)
            if not score:
                for j2 in range(i+1, min(i+4, len(expanded))):
                    score = _extract_score(expanded[j2])
                    if score: break
            extra = ''
            j = i + 1
            while j < len(expanded):
                nl = expanded[j].strip()
                if not nl or re.match(r'^\d{1,2}\.[^\d]', nl) or _is_subj_header(nl): break
                if '□' in nl or '다음 중' in nl: break
                if nl.startswith(('-','·','•','∙','―')): extra += '\n' + nl
                j += 1
            full = (clean + extra).strip()
            if len(full) >= 5:
                questions.append({'text': full, 'subj': cur_subj, 'score': score, 'required': True})
            i += 1; continue
        m = re.match(r'^(\d{1,2})[\.]\s*(.+)', line)
        if m:
            num = int(m.group(1))
            clean = m.group(2).strip()
            if num < 1 or num > 20 or len(clean) < 2:
                i += 1; continue
            is_req = '필수문제' in clean
            score = _extract_score(clean)
            if not score:
                for j2 in range(i+1, min(i+6, len(expanded))):
                    score = _extract_score(expanded[j2])
                    if score: break
            extra = ''
            j = i + 1
            while j < len(expanded):
                nl = expanded[j].strip()
                if not nl or re.match(r'^\d{1,2}\.[^\d]', nl) or _is_subj_header(nl): break
                if '□' in nl or '다음 중' in nl: break
                if nl.startswith(('-','·','•','∙','―')): extra += '\n' + nl
                j += 1
            full = (clean + extra).strip()
            if len(full) >= 5:
                questions.append({'text': full, 'subj': cur_subj, 'score': score, 'required': is_req})
        i += 1
    return questions

def parse_gosi_questions(text):
    questions = []
    lines = text.replace('\r\n', '\n').split('\n')
    expanded = []
    for line in lines:
        line = line.strip()
        if not line:
            expanded.append(''); continue
        parts = re.split(r'(?<!\d)(?=\b\d{1,2}\.[^\d])', line)
        if len(parts) > 1:
            for p in parts:
                p = p.strip()
                if p: expanded.append(p)
        else:
            expanded.append(line)
    i = 0
    while i < len(expanded):
        line = expanded[i].strip()
        m = re.match(r'^(\d{1,2})[\.]\s*(.+)', line)
        if m:
            num = int(m.group(1))
            clean = m.group(2).strip()
            if 1 <= num <= 20 and len(clean) >= 3:
                score = _extract_score(clean)
                if not score:
                    for j2 in range(i+1, min(i+6, len(expanded))):
                        score = _extract_score(expanded[j2])
                        if score: break
                extra = ''
                j = i + 1
                while j < len(expanded):
                    nl = expanded[j].strip()
                    if not nl or re.match(r'^\d{1,2}\.[^\d]', nl): break
                    if nl.startswith(('-','·','•','∙')): extra += '\n' + nl
                    j += 1
                full = (clean + extra).strip()
                if len(full) >= 3:
                    questions.append({'text': full, 'score': score})
        i += 1
    return questions


# ─── PDF 뷰어 팝업 ───
# PDF.js를 사용해 Canvas에 직접 렌더링 → 브라우저 PDF 플러그인/iframe 샌드박스 차단 완전 우회
@st.dialog("📄 PDF 뷰어", width="large")
def show_pdf_dialog(pdf_b64: str, pdf_title: str):
    st.caption(f"**{pdf_title}**  ·  페이지 이동 및 확대/축소 지원")
    components.html(
        f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#525659; font-family:'Noto Sans KR',sans-serif; }}
  #toolbar {{
    position:sticky; top:0; z-index:10;
    background:#2d5a27; color:white;
    padding:8px 14px;
    display:flex; align-items:center; justify-content:space-between;
    font-size:13px; font-weight:600;
    box-shadow:0 2px 6px rgba(0,0,0,0.35);
  }}
  .ctrl {{ display:flex; align-items:center; gap:8px; }}
  .ctrl button {{
    background:rgba(255,255,255,0.18); color:white;
    border:1px solid rgba(255,255,255,0.4);
    border-radius:4px; padding:3px 11px; cursor:pointer; font-size:13px;
  }}
  .ctrl button:hover {{ background:rgba(255,255,255,0.32); }}
  .ctrl button:disabled {{ opacity:0.35; cursor:default; }}
  select {{
    background:rgba(255,255,255,0.15); color:white;
    border:1px solid rgba(255,255,255,0.4);
    border-radius:4px; padding:3px 7px; font-size:12px; cursor:pointer;
  }}
  #page-info {{ font-size:12px; opacity:0.85; }}
  #pdf-wrap {{
    display:flex; flex-direction:column; align-items:center;
    padding:14px 8px 20px; gap:10px;
  }}
  canvas {{
    display:block; max-width:100%;
    box-shadow:0 2px 10px rgba(0,0,0,0.45);
  }}
  #loading {{ color:#ccc; padding:60px 20px; text-align:center; font-size:15px; }}
</style>
</head>
<body>
<div id="toolbar">
  <span id="title-txt" style="max-width:55%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
    📄 {pdf_title}
  </span>
  <div class="ctrl">
    <button id="btn-prev" disabled>◀</button>
    <span id="page-info">로딩중...</span>
    <button id="btn-next" disabled>▶</button>
    <select id="zoom-sel">
      <option value="1.0">100%</option>
      <option value="1.3">130%</option>
      <option value="1.5" selected>150%</option>
      <option value="1.8">180%</option>
      <option value="2.0">200%</option>
    </select>
  </div>
</div>
<div id="pdf-wrap">
  <div id="loading">⏳ PDF 로딩 중...</div>
</div>
<script>
pdfjsLib.GlobalWorkerOptions.workerSrc =
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

var pdfDoc = null, curPage = 1, scale = 1.5;
var wrap = document.getElementById('pdf-wrap');
var info = document.getElementById('page-info');
var btnP = document.getElementById('btn-prev');
var btnN = document.getElementById('btn-next');
var zsel = document.getElementById('zoom-sel');
var canvas = document.createElement('canvas');

// base64 → Uint8Array
var b64 = `{pdf_b64}`;
var bin = atob(b64);
var arr = new Uint8Array(bin.length);
for (var i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);

function renderPage(n) {{
  pdfDoc.getPage(n).then(function(page) {{
    var vp = page.getViewport({{ scale: scale }});
    canvas.width = vp.width;
    canvas.height = vp.height;
    page.render({{ canvasContext: canvas.getContext('2d'), viewport: vp }}).promise.then(function() {{
      info.textContent = n + ' / ' + pdfDoc.numPages + '페이지';
      btnP.disabled = n <= 1;
      btnN.disabled = n >= pdfDoc.numPages;
    }});
  }});
}}

pdfjsLib.getDocument({{ data: arr }}).promise.then(function(pdf) {{
  pdfDoc = pdf;
  wrap.innerHTML = '';
  wrap.appendChild(canvas);
  renderPage(1);
}}).catch(function(e) {{
  wrap.innerHTML = '<div style="color:#ff9a9a;padding:30px;text-align:center;font-size:14px;line-height:2">' +
    '⚠️ PDF 렌더링 오류<br><small>' + e.message + '</small></div>';
}});

btnP.onclick = function() {{ if (curPage > 1) renderPage(--curPage); }};
btnN.onclick = function() {{ if (pdfDoc && curPage < pdfDoc.numPages) renderPage(++curPage); }};
zsel.onchange = function() {{ scale = parseFloat(zsel.value); if (pdfDoc) renderPage(curPage); }};
</script>
</body>
</html>""",
        height=720,
        scrolling=True,
    )
    if st.button("✕ 닫기", use_container_width=True, type="secondary"):
        st.session_state.view_file_key = None
        st.rerun()


# ─── API 스트리밍 생성 ───
def generate_stream(question, score, detail, exam_type, subject=""):
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    is_short = score.isdigit() and int(score) <= 15
    detail_inst = {
        'detailed': '매우 상세하게 작성. 세부 조항, 숫자, 공식, 사례 등 최대한 포함.',
        'brief': '핵심만 간략하게 작성. 불필요한 서술 최소화.',
        'standard': '표준 분량으로 작성. 핵심 내용 균형있게 서술.'
    }.get(detail, '표준 분량으로 작성.')

    if exam_type == "환경영향평가사":
        sys = f"""당신은 환경영향평가사 1차 필기시험 모범답안 작성 전문가입니다.
[답안 형식]
{"단답형(8~9점): 600~900자, Ⅰ.개요→Ⅱ.주요내용→Ⅲ.결론" if is_short else "논술형(25점): 1,500~2,500자, Ⅰ.개요→Ⅱ.본론1→Ⅲ.본론2→Ⅳ.결론"}
계층 구조: 대제목(Ⅰ Ⅱ Ⅲ Ⅳ) → 소제목(1. 2. 3.) → 세부항목(가. 나. 다.) → 불릿(◦) → 세부불릿(-)
- 법령 명칭 정확히 명시: 「환경영향평가법」제○○조 / 최신 법령·정책 반영 (2024년 기준)
- {detail_inst}
답안만 출력하세요."""
    else:
        sys = f"""당신은 5급 공채(기술고시) 환경직 {subject} 모범답안 작성 전문가입니다.
[답안 형식]
{"단답형: 400~600자, Ⅰ.정의→Ⅱ.주요내용→Ⅲ.결론" if is_short else "논술형: 1,500~2,500자, Ⅰ.서론→Ⅱ.본론(2~3개)→Ⅲ.결론"}
계층 구조: 대제목(Ⅰ Ⅱ Ⅲ Ⅳ) → 소제목(1. 2. 3.) → 세부항목(가. 나. 다.) → 불릿(◦) → 세부불릿(-)
- 공학적 원리·이론·공식 정확히 서술 / 관련 법령·기준 명시 / 수치·단위 정확히 기재
- 과목 특성({subject})에 맞는 전문 용어 사용 / {detail_inst}
답안만 출력하세요."""

    user_msg = f"""다음 {'환경영향평가사' if exam_type=='환경영향평가사' else f'5급 기술고시 환경직 {subject}'} 시험 문제에 대한 모범답안을 작성해 주세요.
배점: {score}점
문제: {question}
모범답안:"""

    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=2000 if is_short else 4000,
        system=sys,
        messages=[{"role": "user", "content": user_msg}]
    ) as stream:
        for text in stream.text_stream:
            yield text


# ─── 세션 초기화 ───
defaults = {
    'exam_type': '환경영향평가사',
    'eias_round': None,
    'gosi_subject': '환경화학',
    'gosi_year': None,
    'selected_q': '',
    'selected_score': '25',
    'selected_subj': '',
    'generated_answer': '',
    'is_generating': False,
    'saved_answers': [],
    'uploaded_files': {},
    'uploaded_texts': {},
    'view_file_key': None,
    'auto_saved_answers': {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─── 헤더 ───
st.markdown("""
<div class="main-header">
  <div style="font-size:36px">🌿</div>
  <div>
    <h1>환경직 시험 모범답안 생성기</h1>
    <p>환경영향평가사 (제1~27회) · 5급 공채(기술고시) 환경직 (2002~2025) · Claude AI 답안 생성</p>
  </div>
</div>
""", unsafe_allow_html=True)


# ─── PDF 팝업 트리거 (페이지 최상단에서 처리) ───
vk = st.session_state.view_file_key
if vk:
    pdf_b64 = None
    pdf_title = ""
    is_image = False
    img_bytes = None

    if vk in st.session_state.uploaded_files:
        fd = st.session_state.uploaded_files[vk]
        pdf_title = fd['name']
        ft = fd['type']
        fb = fd['bytes']
        if ft == "application/pdf":
            pdf_b64 = base64.b64encode(fb).decode()
        elif ft in ["image/png", "image/jpeg", "image/jpg"]:
            is_image = True
            img_bytes = fb

    elif vk.startswith("proj_"):
        parts = vk.split("_", 2)
        kind = parts[1] if len(parts) > 1 else ""
        if kind == "eias":
            rn = int(parts[2])
            fname = EIAS_PDF_MAP.get(rn, "")
            pdf_title = f"제{rn}회 환경영향평가사 기출문제"
        else:
            subj_yr = parts[2]
            lu = subj_yr.rfind("_")
            g_subj = subj_yr[:lu]
            g_yr = int(subj_yr[lu+1:])
            fname = GOSI_PDF_MAP.get(g_subj, {}).get(g_yr, "")
            pdf_title = f"{g_yr}년 5급 공채 {g_subj}"
        if fname:
            try:
                with open(f"{PDF_BASE}/{fname}", 'rb') as f:
                    pdf_b64 = base64.b64encode(f.read()).decode()
            except Exception as e:
                st.error(f"PDF 파일 로드 실패: {e}")
                st.session_state.view_file_key = None

    if pdf_b64:
        show_pdf_dialog(pdf_b64, pdf_title)
    elif is_image and img_bytes:
        @st.dialog("🖼️ 이미지 뷰어", width="large")
        def _show_img():
            st.image(img_bytes, caption=pdf_title, use_container_width=True)
            if st.button("✕ 닫기", use_container_width=True):
                st.session_state.view_file_key = None
                st.rerun()
        _show_img()


# ─── 시험 유형 선택 ───
col_t1, col_t2, col_t3 = st.columns([2, 2, 6])
with col_t1:
    if st.button("🌿 환경영향평가사",
                 type="primary" if st.session_state.exam_type == "환경영향평가사" else "secondary",
                 use_container_width=True):
        st.session_state.exam_type = "환경영향평가사"
        st.session_state.generated_answer = ''
        st.session_state.selected_q = ''
        st.session_state.view_file_key = None
        st.rerun()
with col_t2:
    if st.button("📋 5급 공채(기술고시)",
                 type="primary" if st.session_state.exam_type == "5급공채" else "secondary",
                 use_container_width=True):
        st.session_state.exam_type = "5급공채"
        st.session_state.generated_answer = ''
        st.session_state.selected_q = ''
        st.session_state.view_file_key = None
        st.rerun()

st.markdown("---")


# ════════════════════════════════════════════
# 환경영향평가사
# ════════════════════════════════════════════
if st.session_state.exam_type == "환경영향평가사":
    sidebar_col, main_col = st.columns([1, 2], gap="large")

    with sidebar_col:
        st.markdown("### 📚 회차 선택 (제1~27회)")
        for row_start in range(0, 27, 5):
            cols = st.columns(5)
            for i, r in enumerate(range(row_start+1, min(row_start+6, 28))):
                with cols[i]:
                    has_data = r in EIAS_DATA_AVAILABLE
                    has_upload = f"eias_{r}" in st.session_state.uploaded_files
                    label = f"**{r}회**" if (has_data or has_upload) else f"{r}회"
                    if st.button(label, key=f"eias_r_{r}", use_container_width=True):
                        st.session_state.eias_round = r
                        st.session_state.selected_q = ''
                        st.session_state.q_input_main = ''
                        st.session_state.generated_answer = ''
                        st.session_state.view_file_key = None
                        st.rerun()

        st.markdown("")
        r = st.session_state.eias_round
        if r:
            has_data = r in EIAS_DATA_AVAILABLE
            has_upload = f"eias_{r}" in st.session_state.uploaded_files
            st.markdown(f"#### 제{r}회 기출문제")
            has_proj_pdf = r in EIAS_PDF_AVAILABLE
            file_key = f"eias_{r}"

            if has_proj_pdf or has_upload:
                bc1, bc2 = st.columns(2)
                with bc1:
                    if has_proj_pdf:
                        if st.button("📖 원본 PDF 보기", key=f"view_eias_proj_{r}", use_container_width=True):
                            st.session_state.view_file_key = f"proj_eias_{r}"
                            st.rerun()
                with bc2:
                    if has_upload and st.session_state.uploaded_files[file_key].get('type') != 'text/plain':
                        if st.button("📄 업로드 PDF 보기", key=f"view_eias_up_{r}", use_container_width=True):
                            st.session_state.view_file_key = file_key
                            st.rerun()

            if not has_data and not has_upload:
                if has_proj_pdf:
                    st.info("위 버튼으로 원본 PDF를 보고, 문제를 직접 입력해 주세요.\n또는 텍스트 파일을 업로드하면 문제 목록이 자동 생성됩니다.")
                else:
                    st.warning(f"제{r}회 기출문제 파일이 없습니다.")
                uploaded = st.file_uploader(f"제{r}회 기출문제 텍스트 업로드", type=["txt"], key=f"upload_eias_{r}")
                if uploaded:
                    fb = uploaded.read()
                    st.session_state.uploaded_files[file_key] = {'bytes': fb, 'name': uploaded.name, 'type': uploaded.type}
                    st.session_state.uploaded_texts[file_key] = fb.decode('utf-8')
                    st.success("업로드 완료!")
                    st.session_state.view_file_key = None
                    st.rerun()
            else:
                subj_filter = st.radio("과목", ['전체', '환경정책', '국토계획', '실무', '제도'],
                                       horizontal=True, key=f"eias_sf_{r}", label_visibility='collapsed')
                text = EXAM_DATA.get(str(r), '') if has_data else st.session_state.uploaded_texts.get(f"eias_{r}", '')
                qs = parse_eias_questions(text)
                filtered = qs if subj_filter == '전체' else [q for q in qs if q['subj'] == subj_filter]
                st.caption(f"총 {len(filtered)}문제")
                for idx, q in enumerate(filtered):
                    req = "★" if q['required'] else ""
                    score_txt = f"[{q['score']}점]" if q['score'] else ""
                    subj_txt = f"[{q['subj']}] " if q['subj'] else ""
                    preview = q['text'][:50] + ('…' if len(q['text']) > 50 else '')
                    auto_key = q['text'][:80]
                    has_auto = auto_key in st.session_state.auto_saved_answers
                    lbl = f"{'✅ ' if has_auto else ''}{req}{subj_txt}{score_txt}\n{preview}"
                    if st.button(lbl, key=f"eias_q_{r}_{idx}", use_container_width=True):
                        st.session_state.selected_q = q['text']
                        st.session_state.q_input_main = q['text']
                        st.session_state.selected_score = q['score'] if q['score'] else '25'
                        st.session_state.selected_subj = q['subj']
                        st.session_state.generated_answer = st.session_state.auto_saved_answers.get(auto_key, '')
                        st.session_state.view_file_key = None
                        st.rerun()
        else:
            st.info("회차를 선택하면 기출문제 목록이 표시됩니다.")

# ════════════════════════════════════════════
# 5급 공채(기술고시)
# ════════════════════════════════════════════
else:
    sidebar_col, main_col = st.columns([1, 2], gap="large")

    with sidebar_col:
        st.markdown("### 📋 5급 공채 기출문제")
        st.caption("과목과 연도를 선택하세요 · **굵은글씨** = PDF 있음")
        subj = st.session_state.gosi_subject
        yr = st.session_state.gosi_year

        st.markdown("**📌 필수과목**")
        rc = st.columns(3)
        for i, s in enumerate(GOSI_SUBJECTS_REQUIRED):
            with rc[i]:
                if st.button(s, key=f"gs_req_{s}", type="primary" if subj == s else "secondary", use_container_width=True):
                    st.session_state.gosi_subject = s
                    st.session_state.selected_q = ''
                    st.session_state.q_input_main = ''
                    st.session_state.generated_answer = ''
                    st.session_state.view_file_key = None
                    st.rerun()

        st.markdown("**📖 선택과목**")
        for i in range(0, len(GOSI_SUBJECTS_ELECTIVE), 2):
            ec = st.columns(2)
            for j, s in enumerate(GOSI_SUBJECTS_ELECTIVE[i:i+2]):
                with ec[j]:
                    if st.button(s, key=f"gs_el_{s}", type="primary" if subj == s else "secondary", use_container_width=True):
                        st.session_state.gosi_subject = s
                        st.session_state.selected_q = ''
                        st.session_state.q_input_main = ''
                        st.session_state.generated_answer = ''
                        st.session_state.view_file_key = None
                        st.rerun()

        st.markdown("---")
        st.markdown("**📅 연도 선택**")
        for row_start in range(0, len(GOSI_YEARS), 4):
            cols = st.columns(4)
            for i, y in enumerate(GOSI_YEARS[row_start:row_start+4]):
                with cols[i]:
                    has_proj = y in GOSI_PDF_MAP.get(subj, {}) if subj else any(y in GOSI_PDF_MAP.get(s, {}) for s in GOSI_ALL_SUBJECTS)
                    lbl = f"**{y}**" if has_proj else str(y)
                    if st.button(lbl, key=f"gs_yr_{y}", type="primary" if yr == y else "secondary", use_container_width=True):
                        st.session_state.gosi_year = y
                        st.session_state.selected_q = ''
                        st.session_state.q_input_main = ''
                        st.session_state.generated_answer = ''
                        st.session_state.view_file_key = None
                        st.rerun()

        subj = st.session_state.gosi_subject
        yr = st.session_state.gosi_year
        if subj and yr:
            file_key = f"gosi_{subj}_{yr}"
            has_proj = yr in GOSI_PDF_MAP.get(subj, {})
            has_upload = file_key in st.session_state.uploaded_files
            st.markdown(f"---\n#### 📄 {yr}년 {subj}")
            bc1, bc2 = st.columns(2)
            with bc1:
                if has_proj:
                    if st.button("📖 PDF 보기", key=f"view_gosi_proj_{subj}_{yr}", use_container_width=True):
                        st.session_state.view_file_key = f"proj_gosi_{subj}_{yr}"
                        st.rerun()
            with bc2:
                if has_upload and st.session_state.uploaded_files[file_key].get('type') != 'text/plain':
                    if st.button("📄 업로드 보기", key=f"view_gosi_up_{subj}_{yr}", use_container_width=True):
                        st.session_state.view_file_key = file_key
                        st.rerun()
            if not has_proj and not has_upload:
                st.warning("해당 기출문제 PDF가 없습니다.")
                uploaded = st.file_uploader(f"{yr}년 {subj} 파일 업로드", type=["pdf","png","jpg","jpeg","txt"], key=f"upload_gosi_{subj}_{yr}")
                if uploaded:
                    fb = uploaded.read()
                    st.session_state.uploaded_files[file_key] = {'bytes': fb, 'name': uploaded.name, 'type': uploaded.type}
                    if uploaded.type == "text/plain":
                        st.session_state.uploaded_texts[file_key] = fb.decode('utf-8')
                    st.success("업로드 완료!")
                    st.session_state.view_file_key = None
                    st.rerun()
            elif file_key in st.session_state.uploaded_texts:
                text = st.session_state.uploaded_texts[file_key]
                qs = parse_gosi_questions(text)
                st.caption(f"총 {len(qs)}문제")
                for idx, q in enumerate(qs):
                    score_txt = f"[{q['score']}점]" if q['score'] else ""
                    preview = q['text'][:50] + ('…' if len(q['text']) > 50 else '')
                    auto_key = q['text'][:80]
                    has_auto = auto_key in st.session_state.auto_saved_answers
                    lbl = f"{'✅ ' if has_auto else ''}{score_txt}\n{preview}"
                    if st.button(lbl, key=f"gosi_q_{subj}_{yr}_{idx}", use_container_width=True):
                        st.session_state.selected_q = q['text']
                        st.session_state.q_input_main = q['text']
                        st.session_state.selected_score = q['score'] if q['score'] else '25'
                        st.session_state.generated_answer = st.session_state.auto_saved_answers.get(auto_key, '')
                        st.session_state.view_file_key = None
                        st.rerun()
            else:
                if has_proj:
                    st.info("📖 위 PDF 보기 버튼으로 문제를 확인하고 직접 입력해 주세요.")
        elif subj and not yr:
            st.markdown("---"); st.info("연도를 선택하세요.")
        elif yr and not subj:
            st.markdown("---"); st.info("과목을 선택하세요.")


# ════════════════════════════════════════════
# 메인 영역
# ════════════════════════════════════════════
with main_col:
    st.markdown("### ✏️ 문제 입력")
    q_input = st.text_area(
        "문제 입력", height=180,
        placeholder="왼쪽에서 문제를 클릭하거나 직접 입력하세요.\n예) 수질오염총량관리제도의 개념과 할당부하량 산정방법을 설명하시오. [30점]",
        key="q_input_main", label_visibility='collapsed'
    )
    q_input = st.session_state.get('q_input_main', '')

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        score_opt = st.selectbox("배점", ["자동감지","10점","15점","20점","25점","30점","40점"], key="score_sel")
    with c2:
        detail_opt = st.selectbox("상세도", ["표준","상세","간략"], key="detail_sel")
    with c3:
        auto_score = re.search(r'\[(\d+)점\]', q_input)
        final_score = (auto_score.group(1) if auto_score else "25") if score_opt == "자동감지" else score_opt.replace("점","")
        score_type = "단답형" if int(final_score) <= 15 else "논술형"
        st.markdown(f"<br><small style='color:#6b6657'>⚖ <b>{final_score}점</b> · {score_type}</small>", unsafe_allow_html=True)

    detail_val = {"표준":"standard","상세":"detailed","간략":"brief"}[detail_opt]

    gc, sc, dc = st.columns([3, 1.5, 1.5])
    with gc:
        gen_btn = st.button("✨ 모범답안 생성", type="primary", use_container_width=True, disabled=st.session_state.is_generating)
    with sc:
        save_btn = st.button("💾 저장", use_container_width=True, disabled=not st.session_state.generated_answer)
    with dc:
        if st.session_state.generated_answer:
            exam_lbl = f"환경영향평가사_{st.session_state.eias_round}회" if st.session_state.exam_type == "환경영향평가사" else f"5급공채_{st.session_state.gosi_subject}_{st.session_state.gosi_year}"
            st.download_button("📥 다운로드", data=st.session_state.generated_answer,
                               file_name=f"모범답안_{exam_lbl}.txt", mime="text/plain", use_container_width=True)

    if save_btn and st.session_state.generated_answer:
        q_short = (st.session_state.selected_q[:40] + '…') if len(st.session_state.selected_q) > 40 else st.session_state.selected_q
        already = any(s['answer'] == st.session_state.generated_answer for s in st.session_state.saved_answers)
        if not already:
            st.session_state.saved_answers.append({'question': q_short or '직접입력', 'answer': st.session_state.generated_answer, 'exam_type': st.session_state.exam_type})
            st.session_state.save_success = True
        else:
            st.session_state.save_duplicate = True
        st.session_state.view_file_key = None
        st.rerun()

    if st.session_state.get('save_success'):
        st.success("💾 저장되었습니다! 사이드바 하단에서 확인하세요.")
        st.session_state.save_success = False
    if st.session_state.get('save_duplicate'):
        st.warning("이미 저장된 답안입니다.")
        st.session_state.save_duplicate = False

    if gen_btn:
        if not q_input.strip():
            st.error("문제를 입력하거나 선택해 주세요.")
        else:
            st.session_state.selected_q = q_input
            st.session_state.is_generating = True
            st.session_state.generated_answer = ''
            st.session_state.view_file_key = None
            st.rerun()

    st.markdown("---")
    st.markdown("### 📝 모범답안")

    if st.session_state.is_generating:
        q_to_gen = st.session_state.selected_q
        if st.session_state.exam_type == "환경영향평가사":
            exam_lbl = f"환경영향평가사 제{st.session_state.eias_round}회" if st.session_state.eias_round else "환경영향평가사"
            subj_lbl = st.session_state.selected_subj
        else:
            exam_lbl = f"5급 기술고시 {st.session_state.gosi_subject} {st.session_state.gosi_year}년"
            subj_lbl = st.session_state.gosi_subject

        st.markdown(f"""<div class="answer-meta"><strong>{q_to_gen[:80]}{'…' if len(q_to_gen)>80 else ''}</strong>
          <span>{exam_lbl} · {subj_lbl} · [{final_score}점]</span></div>""", unsafe_allow_html=True)

        answer_display = st.empty()
        full_answer = ""
        try:
            for chunk in generate_stream(q_to_gen, final_score, detail_val, st.session_state.exam_type,
                                         st.session_state.gosi_subject if st.session_state.exam_type == "5급공채" else ""):
                full_answer += chunk
                answer_display.markdown(f'<div class="stream-box">{full_answer}▍</div>', unsafe_allow_html=True)
            st.session_state.generated_answer = full_answer
            st.session_state.auto_saved_answers[q_to_gen[:80]] = full_answer
            st.session_state.is_generating = False
            st.rerun()
        except Exception as e:
            st.session_state.is_generating = False
            err = str(e)
            if '401' in err or 'authentication' in err: st.error("❌ API 키 오류.")
            elif '429' in err: st.error("❌ 요청 초과. 잠시 후 다시 시도하세요.")
            elif 'credit' in err.lower(): st.error("❌ 크레딧 부족.")
            else: st.error(f"❌ 오류: {err}")

    elif st.session_state.generated_answer:
        if st.session_state.exam_type == "환경영향평가사":
            exam_lbl = f"환경영향평가사 제{st.session_state.eias_round}회" if st.session_state.eias_round else "환경영향평가사"
            subj_lbl = st.session_state.selected_subj
        else:
            exam_lbl = f"5급 기술고시 {st.session_state.gosi_subject} {st.session_state.gosi_year}년"
            subj_lbl = st.session_state.gosi_subject

        q_display = st.session_state.selected_q
        st.markdown(f"""<div class="answer-meta"><strong>{q_display[:80]}{'…' if len(q_display)>80 else ''}</strong>
          <span>{exam_lbl} · {subj_lbl} · [{final_score}점]</span></div>""", unsafe_allow_html=True)

        tab_view, tab_edit = st.tabs(["👁 미리보기", "✏️ 편집"])
        with tab_view:
            st.markdown(f'<div class="answer-box">{st.session_state.generated_answer}</div>', unsafe_allow_html=True)
            chars = len(st.session_state.generated_answer)
            st.caption(f"📊 총 {chars:,}자 · 예상 {chars//500+1}페이지 · 🔄 자동저장됨")
        with tab_edit:
            edited = st.text_area("편집", value=st.session_state.generated_answer, height=600,
                                  label_visibility='collapsed', key="edit_answer")
            if edited != st.session_state.generated_answer:
                st.session_state.generated_answer = edited
                st.session_state.auto_saved_answers[st.session_state.selected_q[:80]] = edited
            if st.button("🔄 재생성", use_container_width=True):
                st.session_state.generated_answer = ''
                st.session_state.is_generating = True
                st.session_state.view_file_key = None
                st.rerun()
    else:
        st.markdown("""<div class="empty-state">
          <div class="icon">📝</div>
          <h3>모범답안이 여기에 표시됩니다</h3>
          <p>왼쪽에서 회차(연도)를 선택하고 문제를 클릭하거나,<br>문제를 직접 입력한 후 「모범답안 생성」을 클릭하세요.</p>
        </div>""", unsafe_allow_html=True)


# ─── 사이드바 ───
with st.sidebar:
    auto_count = len(st.session_state.auto_saved_answers)
    if auto_count > 0:
        st.markdown("---")
        st.markdown(f"### 🔄 자동저장 답안 ({auto_count}개)")
        st.caption("문제를 클릭하면 자동으로 불러옵니다 (✅ 표시)")
        if st.button("🗑 자동저장 전체 초기화", use_container_width=True):
            st.session_state.auto_saved_answers = {}
            st.session_state.generated_answer = ''
            st.session_state.view_file_key = None
            st.rerun()

    if st.session_state.saved_answers:
        st.markdown("---")
        st.markdown(f"### 💾 저장된 답안 ({len(st.session_state.saved_answers)}개)")
        if st.button("🗑 전체 삭제", key="del_all_saved", use_container_width=True):
            st.session_state.saved_answers = []
            st.session_state.view_file_key = None
            st.rerun()
        for i, saved in enumerate(reversed(st.session_state.saved_answers)):
            ri = len(st.session_state.saved_answers) - 1 - i
            badge = "🌿" if saved.get('exam_type') == '환경영향평가사' else "📋"
            c1, c2 = st.columns([5, 1])
            with c1:
                if st.button(f"{badge} {saved['question']}", key=f"load_{ri}", use_container_width=True, help=saved['question']):
                    st.session_state.generated_answer = saved['answer']
                    st.session_state.q_input_main = saved['question']
                    st.session_state.selected_q = saved['question']
                    st.session_state.view_file_key = None
                    st.rerun()
            with c2:
                if st.button("✕", key=f"del_{ri}"):
                    st.session_state.saved_answers.pop(ri)
                    st.session_state.view_file_key = None
                    st.rerun()


# ─── 푸터 ───
st.markdown(
    "<div style='text-align:center;font-size:11px;color:#6b6657;padding:20px 0 10px'>"
    "🌿 환경직 시험 모범답안 생성기 v5.2 · Powered by Claude AI"
    "</div>",
    unsafe_allow_html=True
)
