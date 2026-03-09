import streamlit as st
import anthropic
import re
from exam_data import EXAM_DATA

# ─── 페이지 설정 ───
st.set_page_config(
    page_title="환경영향평가사 모범답안 생성기",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

/* 전체 배경 */
.stApp { background: #f5f2eb; }
[data-testid="stSidebar"] { background: #fffefb; border-right: 1px solid #d4cfc2; }

/* 헤더 */
.main-header {
    background: #2d5a27;
    color: white;
    padding: 18px 24px;
    border-radius: 12px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 14px;
}
.main-header h1 { font-family: 'Noto Serif KR', serif; font-size: 22px; font-weight: 700; margin: 0; }
.main-header p { font-size: 12px; opacity: 0.75; margin: 3px 0 0; }

/* 섹션 헤더 */
.section-label {
    font-size: 11px; font-weight: 700; letter-spacing: 0.8px;
    text-transform: uppercase; color: #6b6657;
    background: #f0ede4; padding: 8px 12px;
    border-radius: 6px 6px 0 0; border: 1px solid #d4cfc2;
    margin-bottom: 0;
}

/* 문제 카드 */
.q-card {
    background: #fffefb; border: 1px solid #d4cfc2;
    border-radius: 8px; padding: 10px 12px;
    margin-bottom: 6px; cursor: pointer;
    transition: all 0.15s; font-size: 13px;
    line-height: 1.5;
}
.q-card:hover { border-color: #4a7c3f; background: #e8f0e6; }
.q-card.selected { border-color: #2d5a27; background: #e8f0e6; border-left: 3px solid #2d5a27; }

/* 배지 */
.badge {
    display: inline-block; padding: 2px 8px;
    border-radius: 12px; font-size: 10px; font-weight: 700;
    margin-right: 5px;
}
.badge-subj { background: #2d5a27; color: white; }
.badge-score { background: #f5edd8; color: #8b6914; border: 1px solid #e0cc99; }
.badge-req { background: #8b2020; color: white; }

/* 답안 출력 */
.answer-box {
    background: #fffefb;
    border: 1px solid #d4cfc2;
    border-radius: 10px;
    padding: 28px 32px;
    font-family: 'Noto Serif KR', serif;
    font-size: 14.5px;
    line-height: 2.0;
    color: #1a1a14;
    white-space: pre-wrap;
    word-break: keep-all;
    min-height: 400px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.answer-meta {
    background: #f5edd8;
    border: 1px solid #e0cc99;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 12px;
    font-size: 12px;
    color: #8b6914;
}
.answer-meta strong { color: #1a1a14; font-size: 14px; display: block; margin-bottom: 3px; }

/* 스트림 박스 */
.stream-container {
    background: #fff;
    border: 1.5px solid #4a7c3f;
    border-radius: 10px;
    padding: 24px 28px;
    font-family: 'Noto Serif KR', serif;
    font-size: 14px;
    line-height: 2.0;
    color: #1a1a14;
    white-space: pre-wrap;
    word-break: keep-all;
    min-height: 300px;
}

/* 버튼 커스텀 */
.stButton > button {
    font-family: 'Noto Sans KR', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}

/* 탭 */
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] { font-family: 'Noto Sans KR', sans-serif; font-size: 13px; }

/* 토스트 대체 info box */
.info-box {
    padding: 10px 14px; border-radius: 7px;
    font-size: 12.5px; font-weight: 500; margin: 8px 0;
}
.info-ok { background: #e8f0e6; color: #2d5a27; border: 1px solid #b8d4b0; }
.info-er { background: #fde8e8; color: #8b2020; border: 1px solid #f0b8b8; }

/* 사이드바 라디오 */
div[data-testid="stRadio"] label { font-size: 13px; }

/* 빈 상태 */
.empty-state {
    text-align: center; padding: 80px 40px;
    color: #6b6657;
}
.empty-state .icon { font-size: 52px; opacity: 0.35; margin-bottom: 16px; }
.empty-state h3 { font-size: 16px; font-weight: 600; color: #1a1a14; opacity: 0.5; margin-bottom: 8px; }
.empty-state p { font-size: 13px; line-height: 1.7; }
</style>
""", unsafe_allow_html=True)


# ─── 기출문제 파싱 ───
def parse_questions(text):
    questions = []
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    subj_map = {
        '환경정책': '환경정책',
        '국토환경계획': '국토계획',
        '환경영향평가실무': '실무',
        '환경영향평가제도': '제도'
    }
    cur_subj = ''
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        for k, v in subj_map.items():
            if k in line:
                cur_subj = v
        
        if re.match(r'^\d+[\.\s]', line) and not re.match(r'^\d+\)', line) and len(line) > 8:
            clean = re.sub(r'^\d+[\.\s]+', '', line).strip()
            if len(clean) < 5:
                continue
            
            is_required = '[필수문제]' in clean or '필수지정문제' in clean
            score = ''
            m = re.search(r'\[(\d+)점\]', clean)
            if m:
                score = m.group(1)
            
            # 이어지는 줄 합치기 (용어 목록 등)
            extra = ''
            j = i + 1
            while j < len(lines):
                nl = lines[j].strip()
                if nl.startswith('-') or nl.startswith('·') or nl.startswith('•'):
                    extra += '\n' + nl
                    j += 1
                else:
                    break
            
            if not score:
                for k2 in range(i+1, min(i+4, len(lines))):
                    nm = re.search(r'\[(\d+)점\]', lines[k2])
                    if nm:
                        score = nm.group(1)
                        break
            
            full_text = clean + extra
            if len(full_text) > 5:
                questions.append({
                    'text': full_text,
                    'subj': cur_subj,
                    'score': score,
                    'required': is_required
                })
    
    return questions


# ─── API 호출 (스트리밍) ───
def generate_answer_stream(question, score, detail):
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    
    is_short = int(score) <= 9 if score.isdigit() else False
    
    detail_inst = {
        'detailed': '매우 상세하게 작성. 세부 조항, 숫자, 사례, 판례 등 최대한 포함. 각 항목을 충분히 서술.',
        'brief': '핵심만 간략하게 작성. 불필요한 서술 최소화.',
        'standard': '표준 분량으로 작성. 핵심 내용 균형있게 서술.'
    }.get(detail, '표준 분량으로 작성.')

    system_prompt = f"""당신은 환경영향평가사 1차 필기시험 모범답안 작성 전문가입니다. 환경부 고위 전문가, 환경영향평가사 시험 출제위원 수준의 전문성을 보유하고 있습니다.

[답안 작성 형식 - 엄격히 준수]

{"▶ 단답형 (8~9점):" if is_short else "▶ 논술형 (25점):"}
{"구성: 정의 → 주요 내용(2~4개 항목) → 관련 법령 → 결론/의의" if is_short else "구성: 개요 → 본론 2~3개 → 결론"}
{"분량: 600~900자 (A4 2~3페이지 분량)" if is_short else "분량: 1,500~2,500자 (A4 4~6페이지 분량)"}

형식 (대제목: Ⅰ Ⅱ Ⅲ Ⅳ / 소제목: 1. 2. 3. / 세부항목: 가. 나. 다. / 불릿: ◦ / 세부불릿: -):

Ⅰ. {"개요" if is_short else "개요 (정의 및 배경)"}
Ⅱ. 주요 내용
  1. ○○○
    가. ~~~
      ◦ ~~~
        - ~~~
    나. ~~~
  2. ○○○
{"Ⅲ. 결론" if is_short else "Ⅲ. 문제점 및 개선방안\n  1. 문제점\n  2. 개선방안\nⅣ. 결론"}

[필수 작성 원칙]
1. 관련 법령 반드시 명시: 「환경영향평가법」제○○조, 「환경정책기본법」등
2. 숫자·수치 정확히 기재 (면적 기준, 기간, 비율 등)
3. 전문용어 정확히 사용
4. 최신 법령·정책 반영 (2024년 기준)
5. {detail_inst}

답안 텍스트만 출력하세요. 다른 설명 없이 바로 시작."""

    user_msg = f"""다음 환경영향평가사 필기시험 문제에 대한 모범답안을 작성해 주세요.

배점: {score}점 ({"단답형" if is_short else "논술형"})

문제:
{question}

모범답안:"""

    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=2000 if is_short else 4000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}]
    ) as stream:
        for text in stream.text_stream:
            yield text


# ─── 세션 초기화 ───
if 'selected_q' not in st.session_state:
    st.session_state.selected_q = ''
if 'selected_score' not in st.session_state:
    st.session_state.selected_score = '25'
if 'selected_subj' not in st.session_state:
    st.session_state.selected_subj = ''
if 'selected_exam' not in st.session_state:
    st.session_state.selected_exam = None
if 'generated_answer' not in st.session_state:
    st.session_state.generated_answer = ''
if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False
if 'saved_answers' not in st.session_state:
    st.session_state.saved_answers = []


# ─── 헤더 ───
st.markdown("""
<div class="main-header">
  <div style="font-size:32px">🌿</div>
  <div>
    <h1>환경영향평가사 모범답안 생성기</h1>
    <p>제1~16회 기출문제 내장 · Claude AI 답안 생성 · 편집 · 저장 · PDF 추출</p>
  </div>
</div>
""", unsafe_allow_html=True)


# ─── 사이드바 ───
with st.sidebar:
    st.markdown("### 📚 기출문제 선택")
    
    exam_num = st.selectbox(
        "회차 선택",
        options=list(range(1, 17)),
        format_func=lambda x: f"제{x}회",
        index=0,
        key="exam_select"
    )
    
    if exam_num:
        st.session_state.selected_exam = exam_num
        questions = parse_questions(EXAM_DATA.get(str(exam_num), ''))
        
        subj_options = ['전체', '환경정책', '국토계획', '실무', '제도']
        subj_filter = st.radio("과목 필터", subj_options, horizontal=True, label_visibility='collapsed')
        
        filtered_qs = questions if subj_filter == '전체' else [q for q in questions if q['subj'] == subj_filter]
        
        st.markdown(f"<small style='color:#6b6657'>총 {len(filtered_qs)}문제</small>", unsafe_allow_html=True)
        
        for idx, q in enumerate(filtered_qs):
            score_badge = f"[{q['score']}점]" if q['score'] else ""
            req_badge = "★필수 " if q['required'] else ""
            subj_badge = f"[{q['subj']}] " if q['subj'] else ""
            preview = q['text'][:55] + ('...' if len(q['text']) > 55 else '')
            
            label = f"{req_badge}{subj_badge}{score_badge}\n{preview}"
            
            if st.button(label, key=f"q_{exam_num}_{idx}", use_container_width=True):
                st.session_state.selected_q = q['text']
                st.session_state.selected_score = q['score'] if q['score'] else '25'
                st.session_state.selected_subj = q['subj']
                st.session_state.generated_answer = ''
                st.rerun()
    
    st.divider()
    st.markdown("### 💾 저장된 답안")
    if st.session_state.saved_answers:
        for i, saved in enumerate(st.session_state.saved_answers):
            col1, col2 = st.columns([5, 1])
            with col1:
                if st.button(f"📄 {saved['question'][:30]}...", key=f"saved_{i}", use_container_width=True):
                    st.session_state.selected_q = saved['question']
                    st.session_state.generated_answer = saved['answer']
                    st.rerun()
            with col2:
                if st.button("✕", key=f"del_{i}"):
                    st.session_state.saved_answers.pop(i)
                    st.rerun()
    else:
        st.caption("저장된 답안이 없습니다.")


# ─── 메인 영역 ───
col_input, col_output = st.columns([1, 1.6], gap="large")

with col_input:
    st.markdown("### ✏️ 문제 입력")
    
    question_input = st.text_area(
        "문제를 입력하거나 왼쪽에서 선택하세요",
        value=st.session_state.selected_q,
        height=200,
        placeholder="예) 환경영향평가의 주민의견수렴 시 설명회·공청회 생략조건 및 생략 시 조치사항에 대하여 기술하시오. [25점]",
        key="q_input_main",
        label_visibility='collapsed'
    )
    
    c1, c2 = st.columns(2)
    with c1:
        score_opt = st.selectbox("배점", ["자동감지", "8점", "9점", "25점"], label_visibility='visible')
    with c2:
        detail_opt = st.selectbox("상세도", ["표준", "상세", "간략"], label_visibility='visible')
    
    detail_map = {"표준": "standard", "상세": "detailed", "간략": "brief"}
    detail_val = detail_map[detail_opt]
    
    # 배점 감지
    auto_score = re.search(r'\[(\d+)점\]', question_input)
    if score_opt == "자동감지":
        final_score = auto_score.group(1) if auto_score else "25"
    else:
        final_score = score_opt.replace("점", "")
    
    st.markdown(f"<small style='color:#6b6657'>감지된 배점: <b>{final_score}점</b> · {'단답형' if int(final_score)<=9 else '논술형'}</small>", unsafe_allow_html=True)
    
    gen_btn = st.button("✨ 모범답안 생성", type="primary", use_container_width=True, disabled=st.session_state.is_generating)
    
    if gen_btn:
        if not question_input.strip():
            st.error("문제를 입력하거나 선택해 주세요.")
        else:
            st.session_state.selected_q = question_input
            st.session_state.is_generating = True
            st.session_state.generated_answer = ''
            st.rerun()
    
    # 저장 / 복사 버튼
    if st.session_state.generated_answer:
        st.divider()
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("💾 저장", use_container_width=True):
                q_short = question_input[:40] + '...' if len(question_input) > 40 else question_input
                st.session_state.saved_answers.append({
                    'question': q_short,
                    'answer': st.session_state.generated_answer,
                    'exam': st.session_state.selected_exam
                })
                st.success("저장되었습니다!")
        with bc2:
            st.download_button(
                "📥 텍스트 저장",
                data=st.session_state.generated_answer,
                file_name=f"모범답안_{st.session_state.selected_exam or '직접입력'}회.txt",
                mime="text/plain",
                use_container_width=True
            )


with col_output:
    st.markdown("### 📝 모범답안")
    
    if st.session_state.is_generating:
        # 생성 중 - 스트리밍
        q_to_gen = st.session_state.selected_q or question_input
        
        if q_to_gen.strip():
            exam_info = f"제{st.session_state.selected_exam}회" if st.session_state.selected_exam else "직접입력"
            st.markdown(f"""
            <div class="answer-meta">
                <strong>{q_to_gen[:80]}{'...' if len(q_to_gen)>80 else ''}</strong>
                {exam_info} · {st.session_state.selected_subj or ''} · [{final_score}점]
            </div>
            """, unsafe_allow_html=True)
            
            placeholder = st.empty()
            full_answer = ""
            
            try:
                with placeholder.container():
                    answer_display = st.empty()
                    progress_msg = st.caption("⏳ AI가 모범답안을 작성하는 중...")
                    
                    for chunk in generate_answer_stream(q_to_gen, final_score, detail_val):
                        full_answer += chunk
                        answer_display.markdown(f"""
                        <div class="stream-container">{full_answer}▍</div>
                        """, unsafe_allow_html=True)
                
                st.session_state.generated_answer = full_answer
                st.session_state.is_generating = False
                st.rerun()
                
            except Exception as e:
                st.session_state.is_generating = False
                err_msg = str(e)
                if 'api_key' in err_msg.lower() or 'authentication' in err_msg.lower():
                    st.error("❌ API 키 오류: secrets 설정을 확인해주세요.")
                elif '429' in err_msg:
                    st.error("❌ 요청 초과: 잠시 후 다시 시도해주세요.")
                else:
                    st.error(f"❌ 오류 발생: {err_msg}")
        else:
            st.session_state.is_generating = False
            st.rerun()
    
    elif st.session_state.generated_answer:
        # 생성 완료 - 답안 표시
        q_display = st.session_state.selected_q or question_input
        exam_info = f"제{st.session_state.selected_exam}회" if st.session_state.selected_exam else "직접입력"
        
        st.markdown(f"""
        <div class="answer-meta">
            <strong>{q_display[:80]}{'...' if len(q_display)>80 else ''}</strong>
            {exam_info} · {st.session_state.selected_subj or ''} · [{final_score}점]
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["👁 미리보기", "✏️ 편집"])
        
        with tab1:
            st.markdown(f"""
            <div class="answer-box">{st.session_state.generated_answer}</div>
            """, unsafe_allow_html=True)
            
            char_count = len(st.session_state.generated_answer)
            st.caption(f"📊 총 {char_count:,}자 · 예상 {char_count//500 + 1}페이지")
        
        with tab2:
            edited = st.text_area(
                "편집",
                value=st.session_state.generated_answer,
                height=600,
                label_visibility='collapsed',
                key="edit_answer"
            )
            if edited != st.session_state.generated_answer:
                st.session_state.generated_answer = edited
            
            if st.button("🔄 재생성", use_container_width=True):
                st.session_state.generated_answer = ''
                st.session_state.is_generating = True
                st.rerun()
    
    else:
        # 빈 상태
        st.markdown("""
        <div class="empty-state">
            <div class="icon">📝</div>
            <h3>모범답안이 여기에 표시됩니다</h3>
            <p>왼쪽 사이드바에서 회차를 선택하고 문제를 클릭하거나,<br>
            문제를 직접 입력한 후 「모범답안 생성」을 클릭하세요.</p>
        </div>
        """, unsafe_allow_html=True)


# ─── 푸터 ───
st.markdown("---")
st.markdown(
    "<div style='text-align:center;font-size:11px;color:#6b6657'>"
    "🌿 환경영향평가사 모범답안 생성기 v4.0 · Powered by Claude AI · "
    "제1~16회 기출문제 내장"
    "</div>",
    unsafe_allow_html=True
)
