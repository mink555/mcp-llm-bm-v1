# FunctionChat-Bench OpenRouter 평가 프로젝트

> OpenRouter API를 통해 여러 LLM 모델의 **Tool-Use(Function Calling) 능력**을 평가하고,
> 전문적인 Excel 리포트를 자동 생성하는 프로젝트입니다.

[![FunctionChat-Bench](https://img.shields.io/badge/Based%20on-FunctionChat--Bench-blue)](https://github.com/kakao/FunctionChat-Bench)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](LICENSE)

---

## 목차

- [프로젝트 소개](#프로젝트-소개)
- [데이터셋 구성](#데이터셋-구성)
- [평가 지표 상세](#평가-지표-상세)
- [평가 산식](#평가-산식)
- [모델에게 Tool 사용을 지시하는 방법](#모델에게-tool-사용을-지시하는-방법)
- [빠른 시작](#빠른-시작)
- [사용 가이드](#사용-가이드)
- [결과물](#결과물)
- [해결한 이슈](#해결한-이슈)
- [FAQ](#faq)
- [참고 자료](#참고-자료)

---

## 프로젝트 소개

### 무엇을 평가하나요?

**FunctionChat-Bench**는 LLM이 대화 중에 **도구(함수)를 올바르게 사용**할 수 있는지 평가하는 벤치마크입니다.
Kakao에서 공개한 한국어 Tool-use 대화 벤치마크를 기반으로 합니다.

이 프로젝트는 FunctionChat-Bench의 평가 방식을 그대로 유지하면서:
- OpenRouter API를 통해 다양한 모델을 자동 평가
- GPT-4.1을 Judge로 사용한 LLM-as-Judge 평가 (OpenRouter 경유)
- 전문적인 Excel 리포트 자동 생성

### 평가 철학

FunctionChat-Bench는 단순히 "함수를 호출할 수 있는가?"가 아니라, **대화 맥락에서 적절한 행동**을 평가합니다:

| 상황 | 올바른 행동 | 평가 카테고리 |
|------|------------|--------------|
| 도구로 처리 가능한 요청 | 올바른 함수 선택 + 정확한 인자 추출 | **Call** |
| 도구 실행 결과 전달 | 결과를 자연스러운 한국어로 응답 | **Completion** |
| 필수 정보가 부족한 요청 | 필요한 정보를 사용자에게 질문 | **Slot** |
| 도구로 불가능한 요청 | 억지로 호출하지 않고 적절히 거절 | **Relevance** |

---

## 데이터셋 구성

FunctionChat-Bench는 3가지 데이터셋으로 구성되어 있습니다.

### 1. Dialog (다중 턴 대화) - 200건

실제 대화처럼 여러 턴에 걸쳐 도구를 사용하는 시나리오입니다.

- **파일**: `FunctionChat-Dialog.jsonl` (45개 대화 시나리오, 총 200턴)
- **구성**: 각 시나리오는 여러 턴의 대화로 구성
- **평가 유형 분포**: call, completion, slot, relevance 4가지 유형이 섞여 있음

**데이터 구조 예시**:
```json
{
  "dialog_num": 1,
  "tools": [{"type": "function", "function": {"name": "create_user", ...}}],
  "turns": [
    {
      "serial_num": 1,
      "query": [{"role": "user", "content": "새 계정을 만들고 싶습니다."}],
      "ground_truth": {"role": "assistant", "content": "네, 도와드릴 수 있습니다..."},
      "type_of_output": "slot"
    }
  ]
}
```

### 2. SingleCall (단일 턴 함수 선택) - 500건

다양한 난이도에서 올바른 함수를 선택하는지 평가합니다.

- **파일**: `FunctionChat-Singlecall.jsonl` (25개 함수 x 4개 쿼리 x 5가지 난이도)
- **구성**: 25개의 서로 다른 함수에 대해, 각 함수마다 4개의 사용자 쿼리 제공

**난이도 유형 (tools_type)**:

| 타입 | 후보 함수 구성 | 난이도 |
|------|---------------|-------|
| `1_exact` | 정답 함수 1개만 제공 | 가장 쉬움 |
| `4_random` | 정답 + 무관한 함수 3개 | 쉬움 |
| `4_close` | 정답 + 유사 도메인 함수 3개 | 보통 |
| `8_random` | 정답 + 무관한 함수 7개 | 어려움 |
| `8_close` | 정답 + 유사 도메인 함수 7개 | 가장 어려움 |

유사 도메인 함수(close)가 포함된 경우가 더 어렵습니다. 예를 들어 날씨 조회 함수가 정답일 때, 일정 조회/메모 추가 같은 비슷한 기능의 함수들이 후보로 주어지면 구분이 더 어려워집니다.

### 3. CallDecision (호출 판단) - 606건

"함수를 호출해야 하는가? 말아야 하는가?"를 판단하는 능력을 평가합니다.

- **파일**: `FunctionChat-CallDecision.jsonl`
- **구성**: CALL/COMPLETION/SLOT/RELEVANCE 4가지 카테고리

**카테고리별 의미**:
- **CALL**: 함수 호출이 필요한 상황 (호출해야 pass)
- **COMPLETION**: 함수 결과를 자연어로 전달해야 하는 상황
- **SLOT**: 파라미터가 부족해서 질문해야 하는 상황
- **RELEVANCE**: 주어진 함수로는 처리 불가능한 상황 (호출하면 fail)

---

## 평가 지표 상세

### LLM-as-Judge 평가 방식

FunctionChat-Bench는 **LLM-as-Judge** 방식을 사용합니다. 평가 대상 모델의 응답을 GPT-4 계열 모델(Judge)이 평가하여 pass/fail을 판정합니다.

평가 과정:
1. **Exact Match 검사**: 먼저 정답과 정확히 일치하는지 확인
2. **Rubric 평가**: Exact Match 실패 시, Judge 모델이 rubric에 따라 평가

### 평가 유형별 Rubric

각 평가 유형마다 별도의 rubric 파일이 있습니다 (`FunctionChat-Bench/data/rubric_*.txt`).

#### Call (함수 호출 정확도)

**평가 기준**: 올바른 함수 선택과 정확한 인자 값 생성

**Pass 조건**:
- 적절한 함수를 선택하고 정확히 이름을 생성
- arguments의 모든 키가 Ground Truth와 일치
- 각 argument 값의 타입이 함수 스키마와 일치
- argument 값이 Ground Truth 또는 Acceptable Arguments와 의미적으로 일치

**Fail 조건**:
- 함수 선택 오류 (다른 함수 선택 또는 미선택)
- 함수 이름 오류 (철자 오류)
- argument 키 오류 (존재하지 않는 키 생성)
- argument 타입 오류 (예: 정수여야 하는데 실수 생성)
- argument 값의 논리적 오류 (허용 범위 초과)

#### Completion (결과 전달)

**평가 기준**: 함수 실행 결과를 자연스러운 한국어로 전달

**Pass 조건**:
- 함수 결과를 대화체로 자연스럽게 paraphrase
- 결과의 의미를 왜곡하지 않음
- Ground Truth보다 간결해도 허용
- 사실에 기반한 추가 설명/제안 포함 가능

**Fail 조건**:
- JSON 데이터를 그대로 출력
- 결과의 의미를 왜곡
- 한국어 대화인데 전체 응답이 영어/중국어

#### Slot (정보 요청)

**평가 기준**: 함수 호출에 필요한 누락된 정보를 사용자에게 질문

**Pass 조건**:
- 적절한 slot filling 질문 수행
- 누락된 필수 파라미터를 모두 빠짐없이 요청 (tool_calls가 null이어도 무관)

**Fail 조건**:
- 필수 정보가 누락된 채로 함수 호출
- 환각(hallucination): 쿼리에 없는 정보를 임의로 생성
- 잘못된 함수 선택
- 자체 지식으로 임의 답변
- 일부 필수 정보만 요청하고 나머지 누락
- 이미 제공된 정보를 중복 질문

#### Relevance (관련성 판단)

**평가 기준**: 함수 호출이 불필요한 상황을 올바르게 인식

**Pass 조건**:
- 함수 호출 없이 자체 지식으로 자연스럽게 대응
- 제공된 함수로 불가능한 요청임을 설명하고 거절

**Fail 조건**:
- 불필요하게 함수 호출
- 불가능한 작업을 수행했다고 거짓 주장
- 한국어 대화인데 영어로만 응답

---

## 평가 산식

### 점수 계산 방식

모든 평가는 **Pass/Fail 이진 판정**으로 이루어집니다.

#### 기본 산식

```
Pass Rate = Pass Count / Total Count
```

#### Dialog 평가

유형별(call, completion, slot, relevance) Pass Rate를 각각 계산하고, 전체 micro average를 산출합니다:

```
유형별 Pass Rate = 해당 유형의 Pass 수 / 해당 유형의 Total 수
Micro Average = 전체 Pass 수 / 전체 평가 건수 (200)
```

#### SingleCall 평가

난이도별(1_exact, 4_random, 4_close, 8_random, 8_close) Pass Rate를 각각 계산합니다:

```
난이도별 Pass Rate = 해당 난이도의 Pass 수 / 해당 난이도의 Total 수
전체 Pass Rate = 전체 Pass 수 / 전체 평가 건수 (500)
```

#### CallDecision 평가

카테고리별(CALL, COMPLETION, SLOT, RELEVANCE) Pass Rate를 계산합니다:

```
카테고리별 Pass Rate = 해당 카테고리 Pass 수 / 해당 카테고리 Total 수
전체 Pass Rate = 전체 Pass 수 / 전체 평가 건수 (606)
```

#### Excel 리포트의 Accuracy

최종 Excel 리포트의 Accuracy는:

```
Accuracy = Total Pass / Total Evaluated * 100%
```

전체 평가 건수: Dialog(200) + SingleCall(500) + CallDecision(606) = **1,306건**

---

## 모델에게 Tool 사용을 지시하는 방법

FunctionChat-Bench가 모델에게 "어떤 함수를 어떤 인자로 호출하라"고 지시하는 방식을 설명합니다.

### 1. System Prompt

모든 평가에서 아래 시스템 프롬프트가 사용됩니다:

```
AI assistant로서, user와 한국어로 대화를 나누세요. 적합한 function이 있으면, 
자체 지식으로 답하지 말고 function 호출을 통해 user의 요청을 해결하세요. 
function 호출에 필요한 파라미터 값을 임의로 생성하지 마세요. 
필수 정보가 부족할 경우 user에게 질문해 정보를 얻으세요. 
누락된 필수 정보가 여러가지이면, 각각을 모두 빠짐없이 구체적으로 요청하세요. 
특별한 이유가 없다면, 파라미터 값을 생성할 때 user의 한국어 표현을 영어로 변경하지 마세요.
```

### 2. Tools Schema (함수 정의)

OpenAI Function Calling 표준 형식으로 사용 가능한 함수들을 정의합니다:

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "informWeather",
        "description": "특정 지역의 현재 날씨 정보 제공",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "날씨 정보를 가져올 지역 이름"
            }
          },
          "required": ["location"]
        }
      }
    }
  ]
}
```

### 3. API 요청 구성

실제 API 호출 시 다음과 같이 구성됩니다:

```python
# payload_creator.py에서 생성하는 요청 형식
request = {
    "model": "qwen/qwen3-32b",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "오늘 서울 날씨 어때?"}
    ],
    "tools": tools_schema,
    "tool_choice": "auto",  # 모델이 자동으로 함수 호출 여부 결정
    "temperature": 0.1
}
```

### 4. 모델의 응답 형식

모델이 함수를 호출하기로 결정하면 아래 형식으로 응답합니다:

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": null,
      "tool_calls": [{
        "id": "call_abc123",
        "type": "function",
        "function": {
          "name": "informWeather",
          "arguments": "{\"location\": \"서울\"}"
        }
      }]
    }
  }]
}
```

### 5. 평가 흐름 정리

```
1. 데이터셋 로드 (Dialog/SingleCall/CallDecision)
   |
2. 각 테스트 케이스마다:
   - System Prompt + User Query + Tools Schema로 API 요청 생성
   - tool_choice="auto"로 모델이 판단하게 함
   |
3. 모델 응답 수집
   - tool_calls 필드 확인 (함수 호출 여부)
   - content 필드 확인 (자연어 응답)
   |
4. 평가 (Judge 호출)
   - Ground Truth와 비교
   - Rubric에 따라 pass/fail 판정
   |
5. 결과 집계 및 리포트 생성
```

---

## 빠른 시작

### 1. 저장소 클론

```bash
git clone https://github.com/mink555/mcp-llm-bm-v1.git
cd mcp-llm-bm-v1
```

### 2. 의존성 설치

```bash
cd FunctionChat-Bench
pip install -r requirements.txt
cd ..
```

Python 3.11+ 권장

### 3. API 키 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음을 입력하세요:

```bash
# OpenRouter API 키 (평가 대상 모델 + Judge 모델 모두 사용)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

**주의**: `.env` 파일은 절대 커밋하지 마세요! (이미 `.gitignore`에 등록됨)

### 4. 퀵 테스트

각 카테고리별로 2개씩만 샘플링해서 빠르게 테스트:

```bash
python quick_test.py --sample-size 2
```

실행이 완료되면:
- **Excel 리포트**: `reports/summary/` 폴더에 생성
- **평가 결과**: `score/` 폴더에 저장

---

## 사용 가이드

### 퀵 테스트 (빠른 검증)

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

### 전체 평가 (전체 데이터셋)

```bash
# 기본: 설정된 모델 전체 평가
python run_evaluation.py

# 특정 모델만 평가
python run_evaluation.py --models "mistralai/mistral-small-3.2-24b-instruct"

# Excel 리포트 생성 스킵
python run_evaluation.py --skip-excel
```

전체 평가는 모델당 수 시간이 소요될 수 있습니다.

### Excel 리포트만 재생성

이미 평가가 완료된 결과로 Excel 리포트만 다시 생성:

```bash
python generate_excel_report.py
```

---

## 결과물

평가를 실행하면 다음 폴더에 결과가 저장됩니다:

```
mcp-llm-bm-v1/
├── reports/           # Excel 리포트
│   ├── {model}/       # 모델별 개별 리포트
│   └── summary/       # 전체 모델 통합 리포트
├── result/            # 모델 응답 결과 (JSONL)
└── score/             # Judge 평가 결과 (TSV)
```

이 폴더들은 모두 `.gitignore`에 등록되어 있습니다.

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

## 해결한 이슈

### 1. Rate Limit (429) 및 크레딧 부족 (402) 오류

**문제**: Judge API 호출 시 rate limit 또는 크레딧 부족으로 평가 중단

**해결**:
- `--num-threads 1`로 동시 호출 수 제한
- 지수 백오프 적용 (4초, 8초, 16초... 최대 60초)
- 재시도 횟수 8회로 증가
- 401/402/403 오류는 즉시 실패 처리 (재시도 무의미)
- Judge 호출 실패 시에도 평가 계속 진행 (해당 케이스만 skip 처리)

### 2. JSON 파싱 오류 (arguments가 비어있거나 잘못된 형식)

**문제**: 일부 모델이 `tool_calls[].function.arguments`를 빈 문자열이나 잘못된 JSON으로 출력

**원인**: 모델의 Function Calling 능력 부족 (버그가 아닌 모델 실력 문제)

**처리**: 해당 케이스는 exact match에서 fail로 처리 후 Judge 평가로 진행

### 3. Mistral 모델의 tool_call_id 오류

**문제**:
```
BadRequestError: Tool call id was 'random_id' but must be a-z, A-Z, 0-9
```

**해결**: Mistral 모델로 보낼 때만 `tool_call_id`를 9자리 영숫자로 normalize

### 4. ZeroDivisionError (평가 건수가 0인 경우)

**문제**: Judge 호출이 모두 실패하면 pass rate 계산 시 0으로 나누기 오류

**해결**: `evaluation_registor.py`에서 분모가 0인 경우 pass rate를 0.0으로 처리

### 5. openai.cfg 파일에 API 키 노출

**문제**: 설정 파일에 API 키가 직접 저장되어 Git에 노출 위험

**해결**:
- 환경변수 placeholder 지원 (`"${OPENROUTER_API_KEY}"`)
- `evaluation_handler.py`에서 placeholder를 실제 환경변수로 치환

---

## FAQ

<details>
<summary><b>Q: API 키가 없으면 실행할 수 없나요?</b></summary>

A: 네, OpenRouter API 키가 필요합니다. 평가 대상 모델과 Judge 모델 모두 OpenRouter를 통해 호출합니다.
</details>

<details>
<summary><b>Q: 평가 시간이 얼마나 걸리나요?</b></summary>

A:
- 퀵 테스트 (샘플 2개): 모델당 약 5-10분
- 전체 평가: 모델당 1-3시간 (rate limit, 모델 응답 속도에 따라 다름)
</details>

<details>
<summary><b>Q: 특정 모델만 평가할 수 있나요?</b></summary>

A: 네, `--models` 옵션을 사용하세요:
```bash
python run_evaluation.py --models "qwen/qwen3-14b"
```
</details>

<details>
<summary><b>Q: 평가 중간에 중단되면 어떻게 되나요?</b></summary>

A: 평가 결과는 실시간으로 파일에 저장됩니다(streaming). 재실행하면 이미 완료된 부분은 건너뛰고 이어서 진행합니다.
</details>

<details>
<summary><b>Q: Excel 리포트만 다시 만들 수 있나요?</b></summary>

A: 네, 평가가 완료된 후 언제든지 다음 명령으로 리포트를 재생성할 수 있습니다:
```bash
python generate_excel_report.py
```
</details>

<details>
<summary><b>Q: Judge 모델을 변경할 수 있나요?</b></summary>

A: 네, `FunctionChat-Bench/config/openai.cfg` 파일에서 `api_version` 값을 변경하면 됩니다. 현재는 `openai/gpt-4.1`을 사용합니다.
</details>

<details>
<summary><b>Q: "Failed to parse JSON" 오류가 많이 보이는데 문제인가요?</b></summary>

A: 아닙니다. 이는 평가 대상 모델이 `arguments` 필드를 올바른 JSON으로 생성하지 못한 경우입니다. 모델의 Function Calling 능력을 측정하는 벤치마크 특성상 자연스러운 현상이며, 해당 케이스는 fail로 처리됩니다.
</details>

<details>
<summary><b>Q: tool_choice="auto"는 무슨 의미인가요?</b></summary>

A: 모델이 스스로 함수 호출 여부를 결정하게 합니다. 함수가 필요하면 호출하고, 필요 없으면 자연어로 응답합니다. 이것이 FunctionChat-Bench가 테스트하려는 핵심 능력입니다.
</details>

---

## 참고 자료

### 공식 문서
- [FunctionChat-Bench 원본 저장소](https://github.com/kakao/FunctionChat-Bench)
- [FunctionChat-Bench 논문 (arXiv)](https://arxiv.org/abs/2411.14054)
- [OpenRouter API 문서](https://openrouter.ai/docs)

### 추가 자료
- FunctionChat-Bench 원본 README: `FunctionChat-Bench/README.md`
- 평가 Rubric 파일: `FunctionChat-Bench/data/rubric_*.txt`

---

## 기여 및 라이선스

이 프로젝트는 [FunctionChat-Bench](https://github.com/kakao/FunctionChat-Bench)를 기반으로 하며, **Apache 2.0 라이선스**를 따릅니다.

이슈 제보 및 개선 제안은 언제나 환영합니다!

---

<div align="center">

**Based on [FunctionChat-Bench](https://github.com/kakao/FunctionChat-Bench) by Kakao**

</div>
