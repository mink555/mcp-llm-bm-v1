# 🧪 FunctionChat-Bench OpenRouter 평가 프로젝트

> OpenRouter API를 통해 5개 LLM 모델의 **Tool-Use(Function Calling) 능력**을 평가하고, 
> 전문적인 Excel 리포트를 자동 생성하는 프로젝트입니다.

[![FunctionChat-Bench](https://img.shields.io/badge/Based%20on-FunctionChat--Bench-blue)](https://github.com/kakao/FunctionChat-Bench)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](LICENSE)

---

## 📖 목차

- [프로젝트 소개](#-프로젝트-소개)
- [평가 모델](#-평가-모델)
- [평가 카테고리](#-평가-카테고리)
- [빠른 시작](#-빠른-시작)
- [사용 가이드](#-사용-가이드)
- [결과물](#-결과물)
- [해결한 이슈](#-해결한-이슈)
- [참고 자료](#-참고-자료)

---

## 🎯 프로젝트 소개

### 무엇을 평가하나요?

**FunctionChat-Bench**는 LLM이 대화 중에 **도구(함수)를 올바르게 사용**할 수 있는지 평가하는 벤치마크입니다.

이 프로젝트는 FunctionChat-Bench의 철학과 평가 방식을 그대로 유지하면서:
- ✅ OpenRouter API를 통해 5개 모델을 자동 평가
- ✅ GPT-4를 Judge로 사용한 LLM-as-Judge 평가
- ✅ 전문적인 Excel 리포트 자동 생성

### 평가 철학

FunctionChat-Bench는 단순히 "함수를 호출할 수 있는가?"가 아니라, **대화 맥락에서 적절한 행동**을 평가합니다:

| 상황 | 올바른 행동 |
|------|------------|
| 🎯 **도구로 처리 가능한 요청** | 올바른 함수 선택 + 정확한 인자 추출 |
| 💬 **도구 결과 전달** | 도구 결과를 자연스러운 언어로 응답 |
| ❓ **정보가 부족한 요청** | 필요한 정보를 사용자에게 질문 |
| 🚫 **도구로 불가능한 요청** | 억지로 호출하지 않고 적절히 거절/설명 |

---

## 🤖 평가 모델

OpenRouter를 통해 다음 5개 모델을 평가합니다:

| 모델 | 설명 |
|------|------|
| **meta-llama/llama-3.3-70b-instruct** | Meta의 최신 Llama 3.3 70B |
| **mistralai/mistral-small-3.2-24b-instruct** | Mistral AI의 Small 모델 |
| **qwen/qwen3-32b** | Alibaba의 Qwen 32B |
| **qwen/qwen3-14b** | Alibaba의 Qwen 14B |
| **qwen/qwen3-next-80b-a3b-instruct** | Alibaba의 최신 Qwen Next 80B |

---

## 📊 평가 카테고리

### 1️⃣ Dialog (다중 턴 대화)

실제 대화처럼 여러 턴에 걸쳐 도구를 올바르게 사용하는지 평가합니다.

| 카테고리 | 평가 내용 | 예시 |
|---------|----------|------|
| **Call** | 함수 선택 & 인자 추출 정확도 | "오늘 서울 날씨 알려줘" → `getWeather("서울")` |
| **Completion** | 도구 결과를 자연어로 전달 | 날씨 데이터 → "서울은 현재 맑고 20도입니다" |
| **Slot** | 부족한 정보 질문 | "일정 추가해줘" → "일정 제목과 날짜를 알려주세요" |
| **Relevance** | 불가능한 요청 적절히 거절 | "문자 보내줘" → "문자 기능은 제공하지 않습니다" |

### 2️⃣ SingleCall (단일 턴 함수 선택)

다양한 난이도에서 올바른 함수를 선택하는지 평가합니다.

| 타입 | 난이도 | 설명 |
|------|--------|------|
| **exact** | ⭐ | 타겟 함수만 제공 (가장 쉬움) |
| **4_random** | ⭐⭐ | 타겟 + 무작위 3개 |
| **4_close** | ⭐⭐⭐ | 타겟 + 유사 기능 3개 |
| **8_random** | ⭐⭐⭐⭐ | 타겟 + 무작위 7개 |
| **8_close** | ⭐⭐⭐⭐⭐ | 타겟 + 유사 기능 7개 (가장 어려움) |

### 3️⃣ CallDecision (호출 판단)

"도구를 호출해야 하는가? 말아야 하는가?"를 판단하는 능력을 평가합니다.

---

## 🚀 빠른 시작

### 1️⃣ 저장소 클론

```bash
git clone https://github.com/mink555/mcp-llm-bm-v1.git
cd mcp-llm-bm-v1
```

### 2️⃣ 의존성 설치

```bash
cd FunctionChat-Bench
pip install -r requirements.txt
cd ..
```

> 💡 **Tip**: Python 3.11+ 권장

### 3️⃣ API 키 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음을 입력하세요:

```bash
# OpenRouter API 키 (평가 대상 모델 실행용)
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# OpenAI API 키 (LLM-as-Judge 평가용)
OPENAI_API_KEY=sk-proj-your-key-here

# OpenRouter Base URL (기본값)
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

> ⚠️ **주의**: `.env` 파일은 절대 커밋하지 마세요! (이미 `.gitignore`에 등록됨)

### 4️⃣ 첫 실행 - 퀵 테스트

각 카테고리별로 2개씩만 샘플링해서 빠르게 테스트해보세요:

```bash
python quick_test.py --sample-size 2
```

실행이 완료되면:
- 📊 **Excel 리포트**: `reports/summary/` 폴더에 생성됩니다
- 📁 **평가 결과**: `score/` 폴더에 저장됩니다

---

## 📚 사용 가이드

### 🎯 퀵 테스트 (빠른 검증)

각 평가 카테고리에서 N개씩만 샘플링하여 빠르게 테스트합니다.

```bash
# 기본: 카테고리별 2개씩 샘플링
python quick_test.py

# 샘플 크기 조절
python quick_test.py --sample-size 5

# 특정 모델만 테스트
python quick_test.py --models "qwen/qwen3-14b"

# 여러 모델 테스트 (쉼표로 구분)
python quick_test.py --models "qwen/qwen3-14b,qwen/qwen3-32b"
```

### 🔄 전체 평가 (전체 데이터셋)

5개 모델에 대해 전체 데이터셋으로 평가를 실행합니다.

```bash
# 기본: 5개 모델 전체 평가
python run_evaluation.py

# 특정 모델만 평가
python run_evaluation.py --models "mistralai/mistral-small-3.2-24b-instruct"

# Excel 리포트 생성 스킵
python run_evaluation.py --skip-excel
```

> ⏱️ **참고**: 전체 평가는 모델당 수 시간이 소요될 수 있습니다.

### 📊 Excel 리포트만 재생성

이미 평가가 완료된 결과로 Excel 리포트만 다시 생성합니다:

```bash
python generate_excel_report.py
```

---

## 📁 결과물

평가를 실행하면 다음 폴더에 결과가 저장됩니다:

```
mcp-llm-bm-v1/
├── reports/           # 📊 Excel 리포트
│   ├── {model}/       # 모델별 개별 리포트
│   └── summary/       # 전체 모델 통합 리포트
├── result/            # 🤖 모델 응답 결과 (JSONL)
└── score/             # ✅ Judge 평가 결과 (TSV)
```

> 💡 **Tip**: 이 폴더들은 모두 `.gitignore`에 등록되어 있습니다.

### Excel 리포트 구성

#### 개별 모델 리포트
- **Summary**: 전체 성능 요약 및 카테고리별 점수
- **Details**: 각 테스트 케이스별 상세 결과 (PASS/FAIL, 오류 유형)

#### 통합 리포트 (All_Models_Summary.xlsx)
- **Ranking**: 모델 간 성능 순위
- **Category Matrix**: 카테고리별 모델 비교 매트릭스
- **Error Summary**: 오류 유형별 통계 (카테고리 x 모델)
- **All Details**: 전체 모델의 상세 결과 통합

---

## 🔧 해결한 이슈

### 1️⃣ Mistral 모델의 `tool_call_id` 오류

**문제**:
```
BadRequestError: Tool call id was 'random_id' but must be a-z, A-Z, 0-9
```

**해결**:
- Mistral 모델로 보낼 때만 `tool_call_id`를 9자리 영숫자로 normalize
- 위치: `FunctionChat-Bench/src/api_executor.py`
- 목적: 모델 실력 vs 스키마 검증 오류를 구분

### 2️⃣ CallDecision 실행 옵션 혼동

**문제**:
- FunctionChat-Bench는 CallDecision을 `common` 옵션으로 실행
- 스크립트에서 `calldecision`으로 실행해서 오류 발생

**해결**:
- `run_evaluation.py`, `quick_test.py`에서 `common` 옵션으로 수정

### 3️⃣ openai.cfg 파일 변경으로 Git이 더러워지는 문제

**문제**:
- 실행할 때마다 `FunctionChat-Bench/config/openai.cfg`가 변경됨
- Git diff에 API 키가 노출될 위험

**해결**:
- 스크립트에서 openai.cfg를 실행 전 백업 → 실행 → 복원
- 템플릿 파일은 플레이스홀더만 유지

### 4️⃣ 불필요한 산출물 관리

**문제**:
- 샘플 JSONL, output 폴더, eval_log 등이 커밋됨

**해결**:
- `.gitignore` 보강
- `reports/`, `result/`, `score/` 전체를 ignore 처리

---

## 📖 참고 자료

### 공식 문서
- [FunctionChat-Bench 원본 저장소](https://github.com/kakao/FunctionChat-Bench)
- [FunctionChat-Bench 논문](https://arxiv.org/abs/2411.14054)
- [OpenRouter API 문서](https://openrouter.ai/docs)

### 추가 자료
- FunctionChat-Bench 원본 README: `FunctionChat-Bench/README.md`
- 평가 방법론 정리: [GitBook - FunctionChat-Bench](https://housekdk.gitbook.io/ml/genai/llm-evaluation/funcchat-bench)
- 평가 Rubric 파일: `FunctionChat-Bench/data/rubric_*.txt`

---

## 🤝 기여 & 라이선스

이 프로젝트는 [FunctionChat-Bench](https://github.com/kakao/FunctionChat-Bench)를 기반으로 하며, **Apache 2.0 라이선스**를 따릅니다.

이슈 제보 및 개선 제안은 언제나 환영합니다!

---

## 💡 FAQ

<details>
<summary><b>Q: API 키가 없으면 실행할 수 없나요?</b></summary>

A: 네, OpenRouter API 키(평가 대상 모델용)와 OpenAI API 키(Judge용) 둘 다 필요합니다. 키가 없으면 스크립트 실행 시 오류가 발생합니다.
</details>

<details>
<summary><b>Q: 평가 시간이 얼마나 걸리나요?</b></summary>

A: 
- 퀵 테스트 (샘플 2개): 모델당 약 5-10분
- 전체 평가: 모델당 1-3시간 (데이터셋 크기에 따라 다름)
</details>

<details>
<summary><b>Q: 특정 모델만 평가할 수 있나요?</b></summary>

A: 네, `--models` 옵션을 사용하세요:
```bash
python run_evaluation.py --models "qwen/qwen3-14b"
```
</details>

<details>
<summary><b>Q: 결과 파일이 너무 커서 Git에 올라가면 어떡하나요?</b></summary>

A: `reports/`, `result/`, `score/` 폴더는 이미 `.gitignore`에 등록되어 있어 자동으로 무시됩니다.
</details>

<details>
<summary><b>Q: Excel 리포트만 다시 만들 수 있나요?</b></summary>

A: 네, 평가가 완료된 후 언제든지 다음 명령으로 리포트를 재생성할 수 있습니다:
```bash
python generate_excel_report.py
```
</details>

---

<div align="center">

**Made with ❤️ using [FunctionChat-Bench](https://github.com/kakao/FunctionChat-Bench)**

</div>
