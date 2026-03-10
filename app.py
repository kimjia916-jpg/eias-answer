import streamlit as st
import anthropic
import re
import base64
import io
from exam_data import EXAM_DATA  # 환경영향평가사 1~16회

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

/* 헤더 */
.main-header {
    background: linear-gradient(135deg, #2d5a27 0%, #3d7a33 100%);
    color: white; padding: 20px 28px; border-radius: 14px;
    margin-bottom: 22px; display: flex; align-items: center; gap: 16px;
    box-shadow: 0 4px 20px rgba(45,90,39,0.25);
}
.main-header h1 { font-family:'Noto Serif KR',serif; font-size:22px; font-weight:700; margin:0; }
.main-header p { font-size:12px; opacity:0.8; margin:4px 0 0; }

/* 시험 유형 탭 */
.exam-type-btn {
    display:inline-block; padding:10px 20px; border-radius:10px;
    font-size:14px; font-weight:700; cursor:pointer;
    border:2px solid #d4cfc2; background:#fff;
    color:#6b6657; transition:all .2s; margin-right:8px;
}
.exam-type-btn.active { background:#2d5a27; color:#fff; border-color:#2d5a27; }

/* 회차/연도 그리드 */
.year-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:5px; margin-bottom:10px; }
.year-btn {
    padding:7px 4px; border-radius:7px; text-align:center;
    font-size:11px; font-weight:600; cursor:pointer;
    border:1.5px solid #d4cfc2; background:#fff; color:#1a1a14;
    transition:all .15s;
}
.year-btn:hover { border-color:#4a7c3f; background:#e8f0e6; }
.year-btn.active { background:#2d5a27; color:#fff; border-color:#2d5a27; }
.year-btn.empty { background:#f5f2eb; color:#bbb; border-style:dashed; cursor:pointer; }
.year-btn.empty:hover { border-color:#e0b060; background:#fdf6e8; color:#8b6914; }
.year-btn.uploaded { background:#fff8e8; color:#8b6914; border-color:#e0cc99; }

/* 과목 탭 */
.subj-grid { display:flex; flex-wrap:wrap; gap:4px; margin-bottom:10px; }
.subj-btn {
    padding:5px 10px; border-radius:20px; font-size:11px;
    font-weight:600; cursor:pointer; border:1.5px solid #d4cfc2;
    background:#fff; color:#6b6657; transition:all .15s;
}
.subj-btn:hover { border-color:#4a7c3f; color:#2d5a27; }
.subj-btn.active { background:#2d5a27; color:#fff; border-color:#2d5a27; }
.subj-btn.required { border-color:#8b6914; color:#8b6914; }
.subj-btn.required.active { background:#8b6914; color:#fff; }

/* 문제 리스트 */
.q-item {
    padding:9px 12px; border-radius:8px; border:1px solid #d4cfc2;
    background:#fff; cursor:pointer; font-size:12.5px; line-height:1.55;
    transition:all .15s; margin-bottom:5px;
}
.q-item:hover { border-color:#4a7c3f; background:#e8f0e6; }
.q-item.sel { border-color:#2d5a27; background:#e8f0e6; border-left:3px solid #2d5a27; }

/* 배지 */
.badge { display:inline-block; padding:2px 7px; border-radius:10px; font-size:10px; font-weight:700; margin-right:4px; }
.badge-green { background:#2d5a27; color:#fff; }
.badge-gold { background:#f5edd8; color:#8b6914; border:1px solid #e0cc99; }
.badge-red { background:#8b2020; color:#fff; }
.badge-blue { background:#1a4a7a; color:#fff; }

/* 답안 영역 */
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

/* 업로드 존 */
.upload-zone {
    border:2px dashed #d4cfc2; border-radius:10px;
    padding:24px; text-align:center; background:#fafaf8;
    color:#6b6657; font-size:13px;
}
.upload-zone:hover { border-color:#8b6914; background:#fdf6e8; }

/* 빈 상태 */
.empty-state { text-align:center; padding:70px 30px; color:#6b6657; }
.empty-state .icon { font-size:48px; opacity:0.3; margin-bottom:14px; }
.empty-state h3 { font-size:15px; font-weight:600; color:#1a1a14; opacity:0.5; margin-bottom:8px; }
.empty-state p { font-size:12.5px; line-height:1.7; }

/* 이미지 뷰어 */
.img-viewer { border:1px solid #d4cfc2; border-radius:10px; overflow:hidden; }

/* Streamlit 기본 버튼 */
.stButton > button { font-family:'Noto Sans KR',sans-serif !important; font-weight:600 !important; border-radius:8px !important; }
div[data-testid="stRadio"] label { font-size:13px; }
</style>
""", unsafe_allow_html=True)


# ─── 상수 정의 ───
EIAS_ROUNDS = list(range(1, 28))   # 1~27회
EIAS_DATA_AVAILABLE = list(range(1, 17))  # 1~16회 텍스트 데이터 내장

GOSI_YEARS = list(range(2025, 2001, -1))  # 2025~2002

GOSI_SUBJECTS_REQUIRED = ["환경화학", "환경계획", "상하수도공학"]
GOSI_SUBJECTS_ELECTIVE = ["소음진동학", "폐기물처리", "환경미생물학", "환경영향평가론", "대기오염관리", "수질오염관리"]
GOSI_ALL_SUBJECTS = GOSI_SUBJECTS_REQUIRED + GOSI_SUBJECTS_ELECTIVE

PDF_BASE = "data"

# ─── 환경영향평가사 PDF 매핑 (1~27회) ───
EIAS_PDF_MAP = {
    1:  "제1회_환경영향평가사_필기시험_기출문제_1.pdf",
    2:  "제2회_환경영향평가사_필기시험_기출문제.pdf",
    3:  "제3회_환경영향평가사_필기시험_기출문제.pdf",
    4:  "제4회_환경영향평가사_필기시험_기출문제.pdf",
    5:  "제5회_환경영향평가사_필기시험_기출문제.pdf",
    6:  "제6회_환경영향평가사_필기시험_기출문제.pdf",
    7:  "제7회_환경영향평가사_필기시험_기출문제.pdf",
    8:  "제8회_환경영향평가사_필기시험_기출문제.pdf",
    9:  "제9회_필기시험_문제지.pdf",
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

# ─── 5급 기술고시 PDF 매핑 (과목별·연도별) ───
GOSI_PDF_MAP = {
    "환경화학": {
        2002: "01__2002년_환경화학.pdf",
        2004: "01__2004년_환경화학.pdf",
        2005: "01__2005년_환경화학.pdf",
        2006: "01__2006년_환경화학.pdf",
        2007: "070825_행정고등고시기술직_2차_시험_환경화학.pdf",
        2022: "환경화학.pdf",
        2023: "230705_5급_기술_2차_환경화학.pdf",
        2024: "240709_5급_과기_2차_환경화학.pdf",
        2025: "250704_5급_2차_과기_환경화학.pdf",
    },
    "환경계획": {
        2002: "02__2002년_환경계획.pdf",
        2003: "02__2003_환경계획.pdf",
        2004: "02__2004년_환경계획.pdf",
        2005: "02__2005년_환경계획.pdf",
        2006: "02__2006년_환경계획.pdf",
        2007: "070825_행정고등고시기술직_2차_시험_환경계획.pdf",
        2022: "환경계획.pdf",
        2023: "230705_5급_기술_2차_환경계획.pdf",
        2024: "240709_5급_과기_2차_환경계획.pdf",
        2025: "250704_5급_2차_과기_환경계획.pdf",
    },
    "상하수도공학": {
        2002: "03__2002년_상하수도공학.pdf",
        2004: "03__2004년_상하수도공학.pdf",
        2005: "03__2005년_상하수도공학.pdf",
        2006: "03__2006년_상하수도공학.pdf",
        2007: "070825_행정고등고시기술직_2차_시험_상하수도공학.pdf",
        2022: "상하수도공학.pdf",
        2023: "230705_5급_기술_2차_상하수도공학.pdf",
        2024: "240709_5급_과기_2차_상하수도공학.pdf",
        2025: "250704_5급_2차_과기_상하수도공학.pdf",
    },
    "소음진동학": {
        2002: "2002년_소음진동학.pdf",
        2004: "2004년_소음진동학.pdf",
        2005: "2005년_소음진동학.pdf",
        2006: "2006년_소음진동학.pdf",
        2022: "소음진동학.pdf",
    },
    "폐기물처리": {
        2002: "2002년_폐기물처리.pdf",
        2004: "2004년_폐기물처리.pdf",
        2005: "2005년_폐기물처리.pdf",
        2006: "2006년_폐기물처리.pdf",
        2022: "폐기물처리.pdf",
        2023: "230705_5급_기술_2차_폐기물처리.pdf",
        2024: "240709_5급_과기_2차_폐기물처리.pdf",
    },
    "환경미생물학": {
        2002: "2002년_환경미생물학.pdf",
        2004: "2004년_환경미생물학.pdf",
        2005: "2005년_환경미생물학.pdf",
        2006: "2006년_환경미생물학.pdf",
        2022: "환경미생물학.pdf",
        2023: "230705_5급_기술_2차_환경미생물학.pdf",
        2024: "240709_5급_과기_2차_환경미생물학.pdf",
    },
    "환경영향평가론": {
        2002: "2002년_환경영향평가론.pdf",
        2004: "2004년_환경영향평가론.pdf",
        2005: "2005년_환경영향평가론.pdf",
        2006: "2006년_환경영향평가론.pdf",
        2022: "환경영향평가론.pdf",
        2023: "230705_5급_기술_2차_환경영향평가론.pdf",
        2024: "240709_5급_과기_2차_환경영향평가론.pdf",
    },
    "대기오염관리": {
        2002: "2002년_대기오염관리.pdf",
        2004: "2004년_대기오염관리.pdf",
        2005: "2005년_대기오염관리.pdf",
        2006: "2006년_대기오염관리.pdf",
        2022: "대기오염관리.pdf",
        2023: "230705_5급_기술_2차_대기오염관리.pdf",
        2024: "240709_5급_과기_2차_대기오염관리.pdf",
    },
    "수질오염관리": {
        2002: "2002년_수질오염관리.pdf",
        2004: "2004년_수질오염관리.pdf",
        2005: "2005년_수질오염관리.pdf",
        2006: "2006년_수질오염관리.pdf",
        2022: "수질오염관리.pdf",
        2023: "230705_5급_기술_2차_수질오염관리.pdf",
        2024: "240709_5급_과기_2차_수질오염관리.pdf",
    },
}


# ─── 기출문제 파싱 헬퍼 ───
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


# ─── 기출문제 파싱 (환경영향평가사) - 최종 버전 ───
def parse_eias_questions(text):
    """
    개선된 파서:
    - 한 줄에 여러 문제 → 분리 (6.', 7.「 등 비공백 구분자 포함)
    - 과목명 공백 포함 (환 경 정 책) 처리
    - 문제 본문 과목명으로 오인식 방지 (헤더 줄만 인식)
    - [9 ] / [25 ] 형식 배점 처리
    - '필수문제'로만 시작하는 Q1 처리
    """
    questions = []
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    cur_subj = ''

    # 1단계: 여러 문제가 한 줄에 있으면 분리
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

    # 2단계: 파싱
    i = 0
    while i < len(expanded):
        line = expanded[i].strip()

        # 과목 헤더에서만 과목 변경
        if _is_subj_header(line):
            line_ns = line.replace(' ', '')
            for k, v in _SUBJ_MAP.items():
                if k.replace(' ','') in line_ns:
                    cur_subj = v
            i += 1; continue

        # '필수문제'로만 시작하는 Q1 (16회 등)
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

        # 일반 문제: 숫자. 로 시작
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


# ─── 기출문제 파싱 (5급 기술고시) ───
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
        sys = f"""당신은 환경영향평가사 1차 필기시험 모범답안 작성 전문가입니다. 환경부 고위 전문가 수준의 전문성을 보유하고 있습니다.

[답안 형식 - 엄격히 준수]
{"단답형(8~9점): 600~900자, Ⅰ.개요→Ⅱ.주요내용→Ⅲ.결론" if is_short else "논술형(25점): 1,500~2,500자, Ⅰ.개요→Ⅱ.본론1→Ⅲ.본론2→Ⅳ.결론"}

계층 구조: 대제목(Ⅰ Ⅱ Ⅲ Ⅳ) → 소제목(1. 2. 3.) → 세부항목(가. 나. 다.) → 불릿(◦) → 세부불릿(-)

[원칙]
- 법령 명칭 정확히 명시: 「환경영향평가법」제○○조
- 숫자·수치 정확히 기재
- 최신 법령·정책 반영 (2024년 기준)
- {detail_inst}

답안만 출력하세요."""
    else:  # 5급 기술고시
        sys = f"""당신은 5급 공채(기술고시) 환경직 {subject} 모범답안 작성 전문가입니다. 행정고시 환경직 출제위원 수준의 전문성을 보유하고 있습니다.

[답안 형식 - 엄격히 준수]
{"단답형: 400~600자, Ⅰ.정의→Ⅱ.주요내용→Ⅲ.결론" if is_short else "논술형: 1,500~2,500자, Ⅰ.서론→Ⅱ.본론(2~3개)→Ⅲ.결론"}

계층 구조: 대제목(Ⅰ Ⅱ Ⅲ Ⅳ) → 소제목(1. 2. 3.) → 세부항목(가. 나. 다.) → 불릿(◦) → 세부불릿(-)

[원칙]
- 공학적 원리·이론·공식 정확히 서술
- 관련 법령·기준 명시
- 수치·단위 정확히 기재
- 최신 정책·기술 반영
- 과목 특성({subject})에 맞는 전문 용어 사용
- {detail_inst}

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
    'auto_saved_answers': {},  # {문제텍스트_키 → 생성된 답안} 자동저장
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


# ─── 시험 유형 선택 ───
col_t1, col_t2, col_t3 = st.columns([2, 2, 6])
with col_t1:
    if st.button("🌿 환경영향평가사",
                 type="primary" if st.session_state.exam_type == "환경영향평가사" else "secondary",
                 use_container_width=True):
        st.session_state.exam_type = "환경영향평가사"
        st.session_state.generated_answer = ''
        st.session_state.selected_q = ''
        st.rerun()
with col_t2:
    if st.button("📋 5급 공채(기술고시)",
                 type="primary" if st.session_state.exam_type == "5급공채" else "secondary",
                 use_container_width=True):
        st.session_state.exam_type = "5급공채"
        st.session_state.generated_answer = ''
        st.session_state.selected_q = ''
        st.rerun()

st.markdown("---")

# ════════════════════════════════════════════
# 환경영향평가사
# ════════════════════════════════════════════
if st.session_state.exam_type == "환경영향평가사":

    sidebar_col, main_col = st.columns([1, 2], gap="large")

    with sidebar_col:
        st.markdown("### 📚 회차 선택 (제1~27회)")

        # 회차 그리드 (5열)
        rounds_per_row = 5
        rounds = list(range(1, 28))
        for row_start in range(0, len(rounds), rounds_per_row):
            cols = st.columns(rounds_per_row)
            for i, r in enumerate(rounds[row_start:row_start+rounds_per_row]):
                with cols[i]:
                    has_data = r in EIAS_DATA_AVAILABLE
                    has_upload = f"eias_{r}" in st.session_state.uploaded_files
                    is_active = st.session_state.eias_round == r

                    if has_data or has_upload:
                        label = f"**{r}회**"
                        btn_type = "primary" if is_active else "secondary"
                    else:
                        label = f"{r}회"
                        btn_type = "secondary"

                    if st.button(label, key=f"eias_r_{r}", use_container_width=True):
                        st.session_state.eias_round = r
                        st.session_state.selected_q = ''
                        st.session_state.q_input_main = ''
                        st.session_state.generated_answer = ''
                        st.rerun()

        st.markdown("")

        # 선택된 회차 처리
        r = st.session_state.eias_round
        if r:
            has_data = r in EIAS_DATA_AVAILABLE
            has_upload = f"eias_{r}" in st.session_state.uploaded_files

            st.markdown(f"#### 제{r}회 기출문제")

            has_proj_pdf = r in EIAS_PDF_AVAILABLE
            file_key = f"eias_{r}"

            # PDF 보기 버튼 (항상 상단에)
            if has_proj_pdf or has_upload:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if has_proj_pdf:
                        if st.button("📖 원본 PDF 보기", key=f"view_eias_proj_{r}", use_container_width=True):
                            st.session_state.view_file_key = f"proj_eias_{r}"
                            st.rerun()
                with btn_col2:
                    if has_upload and st.session_state.uploaded_files[file_key].get('type') != 'text/plain':
                        if st.button("📄 업로드 PDF 보기", key=f"view_eias_up_{r}", use_container_width=True):
                            st.session_state.view_file_key = file_key
                            st.rerun()

            # 텍스트 데이터 없으면 업로드 유도
            if not has_data and not has_upload:
                if has_proj_pdf:
                    st.info("위 버튼으로 원본 PDF를 보고, 문제를 직접 입력해 주세요.\n또는 텍스트 파일을 업로드하면 문제 목록이 자동 생성됩니다.")
                else:
                    st.warning(f"제{r}회 기출문제 파일이 없습니다.")
                uploaded = st.file_uploader(
                    f"제{r}회 기출문제 텍스트 업로드",
                    type=["txt"],
                    key=f"upload_eias_{r}"
                )
                if uploaded:
                    file_bytes = uploaded.read()
                    st.session_state.uploaded_files[file_key] = {
                        'bytes': file_bytes, 'name': uploaded.name, 'type': uploaded.type
                    }
                    st.session_state.uploaded_texts[file_key] = file_bytes.decode('utf-8')
                    st.success("업로드 완료!")
                    st.rerun()
            else:

                # 과목 필터
                subj_opts = ['전체', '환경정책', '국토계획', '실무', '제도']
                subj_filter = st.radio("과목", subj_opts, horizontal=True,
                                       key=f"eias_subj_filter_{r}", label_visibility='collapsed')

                # 문제 파싱
                if has_data:
                    text = EXAM_DATA.get(str(r), '')
                elif f"eias_{r}" in st.session_state.uploaded_texts:
                    text = st.session_state.uploaded_texts[f"eias_{r}"]
                else:
                    text = ''

                qs = parse_eias_questions(text)
                filtered = qs if subj_filter == '전체' else [q for q in qs if q['subj'] == subj_filter]

                st.caption(f"총 {len(filtered)}문제")

                for idx, q in enumerate(filtered):
                    req = "★" if q['required'] else ""
                    score_txt = f"[{q['score']}점]" if q['score'] else ""
                    subj_txt = f"[{q['subj']}] " if q['subj'] else ""
                    preview = q['text'][:50] + ('…' if len(q['text']) > 50 else '')
                    # 자동저장 답안 있으면 ✅ 표시
                    auto_key = q['text'][:80]
                    has_auto = auto_key in st.session_state.auto_saved_answers
                    label = f"{'✅ ' if has_auto else ''}{req}{subj_txt}{score_txt}\n{preview}"
                    if st.button(label, key=f"eias_q_{r}_{idx}", use_container_width=True):
                        st.session_state.selected_q = q['text']
                        st.session_state.q_input_main = q['text']
                        st.session_state.selected_score = q['score'] if q['score'] else '25'
                        st.session_state.selected_subj = q['subj']
                        # 자동저장된 답안 있으면 바로 불러오기
                        st.session_state.generated_answer = st.session_state.auto_saved_answers.get(auto_key, '')
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
        st.caption("과목과 연도를 각각 선택하세요 · **굵은글씨** = PDF 있음")

        subj = st.session_state.gosi_subject
        yr   = st.session_state.gosi_year

        # ── 과목 선택 (항상 표시) ──
        st.markdown("**📌 필수과목**")
        req_cols = st.columns(3)
        for i, s in enumerate(GOSI_SUBJECTS_REQUIRED):
            with req_cols[i]:
                if st.button(s, key=f"gs_req_{s}",
                             type="primary" if subj == s else "secondary",
                             use_container_width=True):
                    st.session_state.gosi_subject = s
                    st.session_state.selected_q = ''
                    st.session_state.q_input_main = ''
                    st.session_state.generated_answer = ''
                    st.rerun()

        st.markdown("**📖 선택과목**")
        for i in range(0, len(GOSI_SUBJECTS_ELECTIVE), 2):
            e_cols = st.columns(2)
            for j, s in enumerate(GOSI_SUBJECTS_ELECTIVE[i:i+2]):
                with e_cols[j]:
                    if st.button(s, key=f"gs_el_{s}",
                                 type="primary" if subj == s else "secondary",
                                 use_container_width=True):
                        st.session_state.gosi_subject = s
                        st.session_state.selected_q = ''
                        st.session_state.q_input_main = ''
                        st.session_state.generated_answer = ''
                        st.rerun()

        st.markdown("---")

        # ── 연도 선택 (항상 표시) ──
        st.markdown("**📅 연도 선택**")
        for row_start in range(0, len(GOSI_YEARS), 4):
            cols = st.columns(4)
            for i, y in enumerate(GOSI_YEARS[row_start:row_start+4]):
                with cols[i]:
                    # 현재 선택된 과목에 PDF 있으면 굵게, 없으면 일반
                    has_proj = y in GOSI_PDF_MAP.get(subj, {}) if subj else any(
                        y in GOSI_PDF_MAP.get(s, {}) for s in GOSI_ALL_SUBJECTS)
                    label = f"**{y}**" if has_proj else str(y)
                    if st.button(label, key=f"gs_yr_{y}",
                                 type="primary" if yr == y else "secondary",
                                 use_container_width=True):
                        st.session_state.gosi_year = y
                        st.session_state.selected_q = ''
                        st.session_state.q_input_main = ''
                        st.session_state.generated_answer = ''
                        st.rerun()

        # ── 과목+연도 선택 시 PDF 보기 + 문제 표시 ──
        subj = st.session_state.gosi_subject
        yr   = st.session_state.gosi_year
        if subj and yr:
            file_key = f"gosi_{subj}_{yr}"
            has_proj = yr in GOSI_PDF_MAP.get(subj, {})
            has_upload = file_key in st.session_state.uploaded_files

            st.markdown(f"---\n#### 📄 {yr}년 {subj}")

            btn_c1, btn_c2 = st.columns(2)
            with btn_c1:
                if has_proj:
                    if st.button("📖 PDF 보기", key=f"view_gosi_proj_{subj}_{yr}", use_container_width=True):
                        st.session_state.view_file_key = f"proj_gosi_{subj}_{yr}"
                        st.rerun()
            with btn_c2:
                if has_upload and st.session_state.uploaded_files[file_key].get('type') != 'text/plain':
                    if st.button("📄 업로드 보기", key=f"view_gosi_up_{subj}_{yr}", use_container_width=True):
                        st.session_state.view_file_key = file_key
                        st.rerun()

            if not has_proj and not has_upload:
                st.warning("해당 기출문제 PDF가 없습니다.")
                uploaded = st.file_uploader(
                    f"{yr}년 {subj} 파일 업로드",
                    type=["pdf", "png", "jpg", "jpeg", "txt"],
                    key=f"upload_gosi_{subj}_{yr}"
                )
                if uploaded:
                    file_bytes = uploaded.read()
                    st.session_state.uploaded_files[file_key] = {
                        'bytes': file_bytes, 'name': uploaded.name, 'type': uploaded.type
                    }
                    if uploaded.type == "text/plain":
                        st.session_state.uploaded_texts[file_key] = file_bytes.decode('utf-8')
                    st.success("업로드 완료!")
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
                        st.rerun()
            else:
                if has_proj:
                    st.info("📖 위 PDF 보기 버튼으로 문제를 확인하고 직접 입력해 주세요.")
        elif subj and not yr:
            st.markdown("---")
            st.info("연도를 선택하세요.")
        elif yr and not subj:
            st.markdown("---")
            st.info("과목을 선택하세요.")


# ════════════════════════════════════════════
# 메인 영역 (공통)
# ════════════════════════════════════════════
with main_col:

    # ── 이미지/PDF 뷰어 ──
    vk = st.session_state.view_file_key

    # ── PDF/이미지 팝업 뷰어 ──
    pdf_b64 = None
    pdf_title = ""
    pdf_is_image = False
    pdf_img_bytes = None

    if vk and vk in st.session_state.uploaded_files:
        fdata = st.session_state.uploaded_files[vk]
        pdf_title = fdata['name']
        ftype = fdata['type']
        fbytes = fdata['bytes']
        if ftype == "application/pdf":
            pdf_b64 = base64.b64encode(fbytes).decode()
        elif ftype in ["image/png", "image/jpeg", "image/jpg"]:
            pdf_is_image = True
            pdf_img_bytes = fbytes

    elif vk and vk.startswith("proj_"):
        parts = vk.split("_", 2)
        exam_kind = parts[1] if len(parts) > 1 else ""
        if exam_kind == "eias":
            r_num = int(parts[2])
            fname = EIAS_PDF_MAP.get(r_num, "")
            pdf_title = f"제{r_num}회 환경영향평가사 기출문제"
        else:
            subj_yr = parts[2]
            last_under = subj_yr.rfind("_")
            g_subj = subj_yr[:last_under]
            g_yr = int(subj_yr[last_under+1:])
            fname = GOSI_PDF_MAP.get(g_subj, {}).get(g_yr, "")
            pdf_title = f"{g_yr}년 5급 공채 {g_subj}"
        if fname:
            try:
                with open(f"{PDF_BASE}/{fname}", 'rb') as f:
                    pdf_b64 = base64.b64encode(f.read()).decode()
            except Exception as e:
                st.error(f"PDF 로드 실패: {e}")

    # 팝업 오버레이 렌더링
    if vk and (pdf_b64 or pdf_is_image):
        if pdf_is_image:
            st.image(pdf_img_bytes, caption=pdf_title, use_container_width=True)
            if st.button("✕ 닫기", key="close_viewer"):
                st.session_state.view_file_key = None
                st.rerun()
        else:
            # 모달 팝업 - 작은 크기 + 바깥 클릭 시 닫기
            close_col, _ = st.columns([1, 5])
            with close_col:
                if st.button("✕ PDF 닫기", key="close_viewer", type="secondary"):
                    st.session_state.view_file_key = None
                    st.rerun()
            st.markdown(
                f"""
                <div id="pdf-overlay" onclick="if(event.target===this){{document.getElementById('pdf-close-btn').click()}}"
                  style="
                    position:fixed; top:0; left:0; width:100vw; height:100vh;
                    background:rgba(0,0,0,0.55); z-index:9999;
                    display:flex; align-items:center; justify-content:center;
                  ">
                  <div style="
                    background:#fff; border-radius:12px;
                    width:70vw; height:80vh; max-width:960px;
                    display:flex; flex-direction:column;
                    box-shadow:0 8px 40px rgba(0,0,0,0.4);
                    overflow:hidden;
                  ">
                    <div style="
                      padding:10px 16px; background:#2d5a27; color:#fff;
                      font-weight:600; font-size:14px;
                      display:flex; justify-content:space-between; align-items:center;
                      flex-shrink:0;
                    ">
                      <span>📄 {pdf_title}</span>
                      <span id="pdf-close-btn" onclick="
                        var btns = window.parent.document.querySelectorAll('button');
                        for(var b of btns){{if(b.innerText.includes('PDF 닫기')){{b.click();break;}}}}
                      " style="cursor:pointer; font-size:18px; line-height:1; opacity:0.8;">✕</span>
                    </div>
                    <iframe
                      src="data:application/pdf;base64,{pdf_b64}"
                      style="flex:1; border:none; width:100%;"
                    ></iframe>
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    elif vk:
        st.warning("PDF 파일을 찾을 수 없습니다.")
        if st.button("✕ 닫기", key="close_viewer"):
            st.session_state.view_file_key = None
            st.rerun()

    # ── 문제 입력 + 생성 ──
    st.markdown("### ✏️ 문제 입력")

    q_input = st.text_area(
        "문제 입력",
        height=180,
        placeholder="왼쪽에서 문제를 클릭하거나 직접 입력하세요.\n예) 수질오염총량관리제도의 개념과 할당부하량 산정방법을 설명하시오. [30점]",
        key="q_input_main",
        label_visibility='collapsed'
    )
    q_input = st.session_state.get('q_input_main', '')

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        score_opt = st.selectbox("배점", ["자동감지", "10점", "15점", "20점", "25점", "30점", "40점"], key="score_sel")
    with c2:
        detail_opt = st.selectbox("상세도", ["표준", "상세", "간략"], key="detail_sel")
    with c3:
        auto_score = re.search(r'\[(\d+)점\]', q_input)
        if score_opt == "자동감지":
            final_score = auto_score.group(1) if auto_score else "25"
        else:
            final_score = score_opt.replace("점", "")
        score_type = "단답형" if int(final_score) <= 15 else "논술형"
        st.markdown(f"<br><small style='color:#6b6657'>⚖ <b>{final_score}점</b> · {score_type}</small>", unsafe_allow_html=True)

    detail_map = {"표준": "standard", "상세": "detailed", "간략": "brief"}
    detail_val = detail_map[detail_opt]

    gen_col, save_col, dl_col = st.columns([3, 1.5, 1.5])
    with gen_col:
        gen_btn = st.button("✨ 모범답안 생성", type="primary", use_container_width=True,
                            disabled=st.session_state.is_generating)
    with save_col:
        save_btn = st.button("💾 저장", use_container_width=True,
                             disabled=not st.session_state.generated_answer)
    with dl_col:
        if st.session_state.generated_answer:
            exam_label = f"환경영향평가사_{st.session_state.eias_round}회" if st.session_state.exam_type == "환경영향평가사" else f"5급공채_{st.session_state.gosi_subject}_{st.session_state.gosi_year}"
            st.download_button("📥 저장", data=st.session_state.generated_answer,
                               file_name=f"모범답안_{exam_label}.txt",
                               mime="text/plain", use_container_width=True)

    if save_btn and st.session_state.generated_answer:
        q_short = st.session_state.selected_q[:40] + '…' if len(st.session_state.selected_q) > 40 else st.session_state.selected_q
        # 중복 저장 방지
        already = any(s['answer'] == st.session_state.generated_answer for s in st.session_state.saved_answers)
        if not already:
            st.session_state.saved_answers.append({
                'question': q_short or '직접입력',
                'answer': st.session_state.generated_answer,
                'exam_type': st.session_state.exam_type
            })
            st.session_state.save_success = True
        else:
            st.session_state.save_success = False
            st.session_state.save_duplicate = True
        st.rerun()

    # 저장 성공/중복 메시지
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
            st.rerun()

    st.markdown("---")
    st.markdown("### 📝 모범답안")

    # ── 생성 중 ──
    if st.session_state.is_generating:
        q_to_gen = st.session_state.selected_q

        if st.session_state.exam_type == "환경영향평가사":
            exam_label = f"환경영향평가사 제{st.session_state.eias_round}회" if st.session_state.eias_round else "환경영향평가사"
            subj_label = st.session_state.selected_subj
        else:
            exam_label = f"5급 기술고시 {st.session_state.gosi_subject} {st.session_state.gosi_year}년"
            subj_label = st.session_state.gosi_subject

        st.markdown(f"""
        <div class="answer-meta">
            <strong>{q_to_gen[:80]}{'…' if len(q_to_gen)>80 else ''}</strong>
            <span>{exam_label} · {subj_label} · [{final_score}점]</span>
        </div>
        """, unsafe_allow_html=True)

        answer_display = st.empty()
        full_answer = ""

        try:
            for chunk in generate_stream(
                q_to_gen, final_score, detail_val,
                st.session_state.exam_type,
                st.session_state.gosi_subject if st.session_state.exam_type == "5급공채" else ""
            ):
                full_answer += chunk
                answer_display.markdown(
                    f'<div class="stream-box">{full_answer}▍</div>',
                    unsafe_allow_html=True
                )

            st.session_state.generated_answer = full_answer
            # ── 자동저장 ──
            auto_key = q_to_gen[:80]
            st.session_state.auto_saved_answers[auto_key] = full_answer
            st.session_state.is_generating = False
            st.rerun()

        except Exception as e:
            st.session_state.is_generating = False
            err = str(e)
            if '401' in err or 'authentication' in err:
                st.error("❌ API 키 오류. Streamlit Secrets를 확인해주세요.")
            elif '429' in err:
                st.error("❌ 요청 초과. 잠시 후 다시 시도해주세요.")
            elif 'credit' in err.lower():
                st.error("❌ 크레딧 부족. console.anthropic.com에서 충전해주세요.")
            else:
                st.error(f"❌ 오류: {err}")

    # ── 생성 완료 ──
    elif st.session_state.generated_answer:
        if st.session_state.exam_type == "환경영향평가사":
            exam_label = f"환경영향평가사 제{st.session_state.eias_round}회" if st.session_state.eias_round else "환경영향평가사"
            subj_label = st.session_state.selected_subj
        else:
            exam_label = f"5급 기술고시 {st.session_state.gosi_subject} {st.session_state.gosi_year}년"
            subj_label = st.session_state.gosi_subject

        q_display = st.session_state.selected_q
        st.markdown(f"""
        <div class="answer-meta">
            <strong>{q_display[:80]}{'…' if len(q_display)>80 else ''}</strong>
            <span>{exam_label} · {subj_label} · [{final_score}점]</span>
        </div>
        """, unsafe_allow_html=True)

        tab_view, tab_edit = st.tabs(["👁 미리보기", "✏️ 편집"])
        with tab_view:
            st.markdown(f'<div class="answer-box">{st.session_state.generated_answer}</div>',
                        unsafe_allow_html=True)
            chars = len(st.session_state.generated_answer)
            auto_key = st.session_state.selected_q[:80]
            st.caption(f"📊 총 {chars:,}자 · 예상 {chars//500+1}페이지 · 🔄 자동저장됨")
        with tab_edit:
            edited = st.text_area("편집", value=st.session_state.generated_answer,
                                  height=600, label_visibility='collapsed', key="edit_answer")
            if edited != st.session_state.generated_answer:
                st.session_state.generated_answer = edited
                # 편집 내용도 자동저장
                auto_key = st.session_state.selected_q[:80]
                st.session_state.auto_saved_answers[auto_key] = edited
            if st.button("🔄 재생성", use_container_width=True):
                st.session_state.generated_answer = ''
                st.session_state.is_generating = True
                st.rerun()

    # ── 빈 상태 ──
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">📝</div>
            <h3>모범답안이 여기에 표시됩니다</h3>
            <p>왼쪽에서 회차(연도)를 선택하고 문제를 클릭하거나,<br>
            문제를 직접 입력한 후 「모범답안 생성」을 클릭하세요.</p>
        </div>
        """, unsafe_allow_html=True)


# ─── 저장된 답안 (사이드바 하단) ───
with st.sidebar:
    # 자동저장 현황
    auto_count = len(st.session_state.auto_saved_answers)
    if auto_count > 0:
        st.markdown("---")
        st.markdown(f"### 🔄 자동저장 답안 ({auto_count}개)")
        st.caption("문제를 클릭하면 자동으로 불러옵니다 (✅ 표시)")
        if st.button("🗑 자동저장 전체 초기화", use_container_width=True):
            st.session_state.auto_saved_answers = {}
            st.session_state.generated_answer = ''
            st.rerun()

    if st.session_state.saved_answers:
        st.markdown("---")
        saved_count = len(st.session_state.saved_answers)
        st.markdown(f"### 💾 저장된 답안 ({saved_count}개)")
        
        # 전체 삭제
        if st.button("🗑 전체 삭제", key="del_all_saved", use_container_width=True):
            st.session_state.saved_answers = []
            st.rerun()

        for i, saved in enumerate(reversed(st.session_state.saved_answers)):
            ri = len(st.session_state.saved_answers) - 1 - i
            exam_badge = "🌿" if saved.get('exam_type') == '환경영향평가사' else "📋"
            c1, c2 = st.columns([5, 1])
            with c1:
                if st.button(
                    f"{exam_badge} {saved['question']}",
                    key=f"load_saved_{ri}",
                    use_container_width=True,
                    help=saved['question']
                ):
                    st.session_state.generated_answer = saved['answer']
                    st.session_state.q_input_main = saved['question']
                    st.session_state.selected_q = saved['question']
                    st.rerun()
            with c2:
                if st.button("✕", key=f"del_saved_{ri}"):
                    st.session_state.saved_answers.pop(ri)
                    st.rerun()


# ─── 푸터 ───
st.markdown(
    "<div style='text-align:center;font-size:11px;color:#6b6657;padding:20px 0 10px'>"
    "🌿 환경직 시험 모범답안 생성기 v5.0 · Powered by Claude AI"
    "</div>",
    unsafe_allow_html=True
)
