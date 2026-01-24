# mcp-llm-bm-v1 (FunctionChat-Bench + OpenRouter)

FunctionChat-Bench를 **그대로 존중**하면서, OpenRouter(OpenAI-compatible API)를 통해 **5개 모델의 Tool-Use(=function calling) 능력**을 평가하고, `reports/`에 **업무용 Excel 리포트**를 생성하는 프로젝트입니다.

---

## 핵심 목표 (FunctionChat-Bench의 평가 의도)

FunctionChat-Bench는 “도구 호출을 할 줄 아는가?”를 **대화 맥락 안에서** 정량적으로 평가합니다.

- **정답이 “툴 호출”인 상황**에는: 올바른 함수 선택 + 올바른 인자 추출 + 올바른 형식으로 tool call 생성
- **정답이 “자연어 응답”인 상황**에는: 도구 결과를 바탕으로 적절한 완료 응답 생성
- **정보가 부족한 상황**에는: 도구 호출 대신 필요한 정보를 질문(slot)
- **도구로 처리할 수 없는 요청**에는: 도구를 억지로 호출하지 않고 적절히 거절/설명(relevance)

평가는 LLM-as-Judge(원본 프로젝트의 rubric 기반)로 PASS/FAIL을 매기며, 이 프로젝트는 그 결과를 엑셀로 보기 좋게 정리합니다.

---

## 평가 카테고리/지표 (원본 README 기준)

### 1) Dialog (멀티턴)

- **call**: 함수 선택/인자 추출이 맞는가?
- **completion**: tool 결과를 근거로 자연어 응답을 잘 생성하는가?
- **slot**: 함수 호출에 필요한 정보가 부족할 때 사용자에게 필요한 정보를 묻는가?
- **relevance**: 사용자의 요청이 제공된 도구로 불가능할 때, 도구를 억지 호출하지 않고 적절히 응답하는가?

### 2) SingleCall (싱글턴)

같은 기능을 다양한 난이도의 후보군에서 고르게 하는 테스트입니다.

- `exact`: 타겟 함수만 제공
- `4_random`: 타겟 + 랜덤 3개
- `4_close`: 타겟 + 유사 도메인 3개
- `8_random`: 타겟 + 랜덤 7개
- `8_close`: 타겟 + 유사 도메인 7개

### 3) CallDecision

해당 요청에서 “도구를 호출해야 하는가/아닌가”를 판단합니다.  
FunctionChat-Bench CLI에서는 이 세트를 `evaluate.py common ...` 옵션으로 실행합니다.

### 기본 지표

- **PASS/FAIL**
- **Accuracy** = PASS / Total

---

## 평가 모델 (OpenRouter)

- `meta-llama/llama-3.3-70b-instruct`
- `mistralai/mistral-small-3.2-24b-instruct`
- `qwen/qwen3-32b`
- `qwen/qwen3-14b`
- `qwen/qwen3-next-80b-a3b-instruct`

---

## 프로젝트 산출물 구조

평가 실행 시 프로젝트 루트에 아래 구조로 생성됩니다. (전부 `.gitignore` 처리)

```
reports/    # 엑셀 보고서
result/     # 모델 응답 결과
score/      # Judge 평가 결과/TSV
```

---

## 설치

### 1) Python 의존성

```bash
cd /Users/mink/00_Workspace/mcp-llm-bm-v1/FunctionChat-Bench
pip install -r requirements.txt
cd ..
```

### 2) 환경변수 (.env 권장)

루트에 `.env` 생성:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
OPENAI_API_KEY=sk-proj-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

주의: **키는 커밋 금지**(이미 `.gitignore` 처리).

---

## CLI 사용법

### 1) 퀵 테스트 (카테고리별 N개 샘플링)

```bash
python quick_test.py --sample-size 2
```

특정 모델만:

```bash
python quick_test.py --models "mistralai/mistral-small-3.2-24b-instruct"
```

### 2) 전체 평가 (5개 모델 기본)

```bash
python run_evaluation.py
```

모델 지정:

```bash
python run_evaluation.py --models "qwen/qwen3-14b,qwen/qwen3-32b"
```

엑셀 생성 스킵:

```bash
python run_evaluation.py --skip-excel
```

### 3) 엑셀만 재생성

```bash
python generate_excel_report.py
```

---

## OpenRouter / 5개 모델에서 겪었던 이슈와 해결

- **Mistral 계열 tool_call_id 제약(400 BadRequest)**  
  Provider가 tool_call_id 형식(영숫자/길이)을 강하게 요구해, `random_id` 같은 값이 있으면 평가가 아예 진행되지 않았습니다.  
  → `FunctionChat-Bench/src/api_executor.py`에서 **Mistral 모델에만 tool_call_id를 9자리 영숫자로 normalize**하여 “모델 실력 문제 vs 스키마 검증 문제”를 구분 가능하게 했습니다.

- **CallDecision 실행 옵션 혼동**  
  FunctionChat-Bench는 CallDecision을 별도 서브커맨드가 아니라 `common` 옵션으로 실행합니다.  
  → `run_evaluation.py` / `quick_test.py`는 CallDecision을 `common`으로 실행하도록 정리했습니다.

- **실행 후 repo가 더러워지는 문제(openai.cfg 변경)**  
  Judge(OpenAI) 설정 파일(`FunctionChat-Bench/config/openai.cfg`)을 실행 시점에 덮어쓰다보니 git diff가 남았습니다.  
  → 스크립트에서 **openai.cfg를 백업 후 실행, 종료 시 복원**하도록 변경했습니다.

- **중복/불필요 산출물**  
  샘플 jsonl, output 폴더, eval_log 등은 실행 산출물이라 커밋 대상이 아닙니다.  
  → `.gitignore` 보강 및 불필요 산출물 정리 흐름을 확립했습니다.

---

## 참고 자료

- FunctionChat-Bench 원본: `FunctionChat-Bench/README.md`
- GitBook 정리(개념/사례): `https://housekdk.gitbook.io/ml/genai/llm-evaluation/funcchat-bench`
