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
EIAS_DATA_AVAILABLE = list(range(1, 17))  # 1~16회 데이터 내장

GOSI_YEARS = list(range(2025, 2001, -1))  # 2025~2002

GOSI_SUBJECTS_REQUIRED = ["환경화학", "환경계획", "상하수도공학"]
GOSI_SUBJECTS_ELECTIVE = ["소음진동학", "폐기물처리", "환경미생물학", "환경영향평가론", "대기오염관리", "수질오염관리"]
GOSI_ALL_SUBJECTS = GOSI_SUBJECTS_REQUIRED + GOSI_SUBJECTS_ELECTIVE


# ─── 기출문제 파싱 (환경영향평가사) ───
def parse_eias_questions(text):
    questions = []
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    subj_map = {'환경정책': '환경정책', '국토환경계획': '국토계획', '환경영향평가실무': '실무', '환경영향평가제도': '제도'}
    cur_subj = ''
    for i, line in enumerate(lines):
        line = line.strip()
        for k, v in subj_map.items():
            if k in line: cur_subj = v
        if re.match(r'^\d+[\.\s]', line) and not re.match(r'^\d+\)', line) and len(line) > 8:
            clean = re.sub(r'^\d+[\.\s]+', '', line).strip()
            if len(clean) < 5: continue
            is_req = '[필수문제]' in clean or '필수지정문제' in clean
            score = ''
            m = re.search(r'\[(\d+)점\]', clean)
            if m: score = m.group(1)
            extra = ''
            j = i + 1
            while j < len(lines):
                nl = lines[j].strip()
                if nl.startswith('-') or nl.startswith('·') or nl.startswith('•'):
                    extra += '\n' + nl; j += 1
                else: break
            if not score:
                for k2 in range(i+1, min(i+4, len(lines))):
                    nm = re.search(r'\[(\d+)점\]', lines[k2])
                    if nm: score = nm.group(1); break
            full = clean + extra
            if len(full) > 5:
                questions.append({'text': full, 'subj': cur_subj, 'score': score, 'required': is_req})
    return questions


# ─── 기출문제 파싱 (5급 기술고시) ───
def parse_gosi_questions(text):
    questions = []
    lines = text.replace('\r\n', '\n').split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if re.match(r'^\d+[\.\s]', line) and not re.match(r'^\d+\)', line) and len(line) > 8:
            clean = re.sub(r'^\d+[\.\s]+', '', line).strip()
            if len(clean) < 5: continue
            score = ''
            m = re.search(r'\[(\d+)점\]', clean)
            if m: score = m.group(1)
            extra = ''
            j = i + 1
            while j < len(lines):
                nl = lines[j].strip()
                if nl.startswith('-') or nl.startswith('·') or nl.startswith('•'):
                    extra += '\n' + nl; j += 1
                else: break
            full = clean + extra
            if len(full) > 5:
                questions.append({'text': full, 'score': score})
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

            # 데이터 없으면 업로드 유도
            if not has_data and not has_upload:
                st.warning(f"제{r}회 기출문제 데이터가 없습니다.")
                uploaded = st.file_uploader(
                    f"제{r}회 기출문제 파일 업로드 (PDF/이미지/텍스트)",
                    type=["pdf", "png", "jpg", "jpeg", "txt"],
                    key=f"upload_eias_{r}"
                )
                if uploaded:
                    file_bytes = uploaded.read()
                    st.session_state.uploaded_files[f"eias_{r}"] = {
                        'bytes': file_bytes,
                        'name': uploaded.name,
                        'type': uploaded.type
                    }
                    # 텍스트 파일이면 문제 파싱용으로 저장
                    if uploaded.type == "text/plain":
                        st.session_state.uploaded_texts[f"eias_{r}"] = file_bytes.decode('utf-8')
                    st.success("업로드 완료!")
                    st.rerun()
            else:
                # 원본 보기 버튼
                file_key = f"eias_{r}"
                if has_upload and st.session_state.uploaded_files[file_key]['type'] != 'text/plain':
                    if st.button("🖼 원본 문제 보기", key=f"view_eias_{r}", use_container_width=True):
                        st.session_state.view_file_key = file_key
                        st.rerun()

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
        st.markdown("### 📚 과목 선택")

        st.markdown("**📌 필수과목**")
        req_cols = st.columns(3)
        for i, subj in enumerate(GOSI_SUBJECTS_REQUIRED):
            with req_cols[i]:
                is_active = st.session_state.gosi_subject == subj
                if st.button(subj, key=f"gosi_subj_req_{subj}",
                             type="primary" if is_active else "secondary",
                             use_container_width=True):
                    st.session_state.gosi_subject = subj
                    st.session_state.gosi_year = None
                    st.session_state.selected_q = ''
                    st.session_state.q_input_main = ''
                    st.session_state.generated_answer = ''
                    st.rerun()

        st.markdown("**📖 선택과목**")
        for i in range(0, len(GOSI_SUBJECTS_ELECTIVE), 2):
            e_cols = st.columns(2)
            for j, subj in enumerate(GOSI_SUBJECTS_ELECTIVE[i:i+2]):
                with e_cols[j]:
                    is_active = st.session_state.gosi_subject == subj
                    if st.button(subj, key=f"gosi_subj_el_{subj}",
                                 type="primary" if is_active else "secondary",
                                 use_container_width=True):
                        st.session_state.gosi_subject = subj
                        st.session_state.gosi_year = None
                        st.session_state.selected_q = ''
                        st.session_state.q_input_main = ''
                        st.session_state.generated_answer = ''
                        st.rerun()

        st.markdown("---")
        subj = st.session_state.gosi_subject
        st.markdown(f"### 📅 연도 선택 — {subj}")
        st.caption("🟩 데이터 있음 · 📂 업로드됨 · ⬜ 업로드 필요")

        # 연도 그리드 (4열)
        years_per_row = 4
        for row_start in range(0, len(GOSI_YEARS), years_per_row):
            cols = st.columns(years_per_row)
            for i, yr in enumerate(GOSI_YEARS[row_start:row_start+years_per_row]):
                with cols[i]:
                    file_key = f"gosi_{subj}_{yr}"
                    has_upload = file_key in st.session_state.uploaded_files
                    is_active = st.session_state.gosi_year == yr

                    if has_upload:
                        label = f"📂{yr}"
                    else:
                        label = f"⬜{yr}"

                    btn_type = "primary" if is_active else "secondary"
                    if st.button(label, key=f"gosi_yr_{subj}_{yr}",
                                 type=btn_type, use_container_width=True):
                        st.session_state.gosi_year = yr
                        st.session_state.selected_q = ''
                        st.session_state.q_input_main = ''
                        st.session_state.generated_answer = ''
                        st.rerun()

        # 선택된 연도 처리
        yr = st.session_state.gosi_year
        if yr:
            file_key = f"gosi_{subj}_{yr}"
            has_upload = file_key in st.session_state.uploaded_files

            st.markdown(f"#### {yr}년 {subj}")

            if not has_upload:
                st.warning(f"{yr}년 {subj} 기출문제가 없습니다.")
                uploaded = st.file_uploader(
                    f"{yr}년 {subj} 파일 업로드 (PDF/이미지/텍스트)",
                    type=["pdf", "png", "jpg", "jpeg", "txt"],
                    key=f"upload_gosi_{subj}_{yr}"
                )
                if uploaded:
                    file_bytes = uploaded.read()
                    st.session_state.uploaded_files[file_key] = {
                        'bytes': file_bytes,
                        'name': uploaded.name,
                        'type': uploaded.type
                    }
                    if uploaded.type == "text/plain":
                        st.session_state.uploaded_texts[file_key] = file_bytes.decode('utf-8')
                    st.success("업로드 완료!")
                    st.rerun()
            else:
                # 원본 보기 버튼
                if st.session_state.uploaded_files[file_key]['type'] != 'text/plain':
                    if st.button("🖼 원본 문제 보기", key=f"view_gosi_{yr}", use_container_width=True):
                        st.session_state.view_file_key = file_key
                        st.rerun()

                # 텍스트로 업로드된 경우 문제 파싱
                if file_key in st.session_state.uploaded_texts:
                    text = st.session_state.uploaded_texts[file_key]
                    qs = parse_gosi_questions(text)
                    st.caption(f"총 {len(qs)}문제")
                    for idx, q in enumerate(qs):
                        score_txt = f"[{q['score']}점]" if q['score'] else ""
                        preview = q['text'][:50] + ('…' if len(q['text']) > 50 else '')
                        auto_key = q['text'][:80]
                        has_auto = auto_key in st.session_state.auto_saved_answers
                        label = f"{'✅ ' if has_auto else ''}{score_txt}\n{preview}"
                        if st.button(label, key=f"gosi_q_{subj}_{yr}_{idx}", use_container_width=True):
                            st.session_state.selected_q = q['text']
                            st.session_state.q_input_main = q['text']
                            st.session_state.selected_score = q['score'] if q['score'] else '25'
                            st.session_state.generated_answer = st.session_state.auto_saved_answers.get(auto_key, '')
                            st.rerun()
                else:
                    st.info("📄 PDF/이미지 파일은 원본 보기로 확인 후 문제를 직접 입력해 주세요.")


# ════════════════════════════════════════════
# 메인 영역 (공통)
# ════════════════════════════════════════════
with main_col:

    # ── 이미지/PDF 뷰어 ──
    vk = st.session_state.view_file_key
    if vk and vk in st.session_state.uploaded_files:
        fdata = st.session_state.uploaded_files[vk]
        col_vh, col_vc = st.columns([6, 1])
        with col_vh:
            st.markdown(f"**📄 원본 문제: {fdata['name']}**")
        with col_vc:
            if st.button("✕ 닫기", key="close_viewer"):
                st.session_state.view_file_key = None
                st.rerun()

        ftype = fdata['type']
        fbytes = fdata['bytes']
        b64 = base64.b64encode(fbytes).decode()

        if ftype == "application/pdf":
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64}" '
                f'width="100%" height="700px" style="border:1px solid #d4cfc2;border-radius:8px"></iframe>',
                unsafe_allow_html=True
            )
        elif ftype in ["image/png", "image/jpeg", "image/jpg"]:
            st.markdown(
                f'<div class="img-viewer"><img src="data:{ftype};base64,{b64}" '
                f'style="width:100%;display:block;" /></div>',
                unsafe_allow_html=True
            )
        st.markdown("---")

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
