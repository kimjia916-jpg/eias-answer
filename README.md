# 🌿 환경영향평가사 모범답안 생성기

Claude AI 기반 환경영향평가사 필기시험 모범답안 자동 생성기입니다.
제1~16회 기출문제가 내장되어 있으며, 회차별 문제를 선택하거나 직접 입력하여 AI 모범답안을 생성할 수 있습니다.

## 📁 파일 구성

```
├── app.py            ← 메인 Streamlit 앱
├── exam_data.py      ← 제1~16회 기출문제 데이터
├── requirements.txt  ← 필요 라이브러리
└── README.md
```

## 🚀 Streamlit Community Cloud 배포 방법

### 1단계 — GitHub에 올리기

1. [github.com](https://github.com) 로그인 후 **New repository** 생성
2. Repository name: `eias-answer` (Public 선택)
3. 이 폴더의 파일 4개를 모두 업로드:
   - `app.py`
   - `exam_data.py`
   - `requirements.txt`
   - `README.md`

### 2단계 — Streamlit Cloud 배포

1. [share.streamlit.io](https://share.streamlit.io) 접속
2. GitHub 계정으로 로그인
3. **"New app"** 클릭
4. 설정:
   - Repository: `내아이디/eias-answer`
   - Branch: `main`
   - Main file path: `app.py`
5. **Advanced settings** → **Secrets** 탭에서 아래 입력:

```toml
ANTHROPIC_API_KEY = "sk-ant-여기에-본인-키-입력"
```

6. **Deploy!** 클릭

### 3단계 — 완료!

몇 분 후 주소 생성:
```
https://내아이디-eias-answer-app-xxxxx.streamlit.app
```

이 주소를 친구에게 공유하면 끝! 🎉

---

## 💰 API 키 발급

[console.anthropic.com](https://console.anthropic.com/settings/keys) 에서 무료 발급
- 신규 가입 시 $5 무료 크레딧 제공
- 답안 1회 생성 ≈ 20~60원 수준
