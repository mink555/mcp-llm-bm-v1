# FunctionChat-Bench OpenRouter 평가 프로젝트

> OpenRouter API를 통해 여러 LLM 모델의 **Tool-Use(Function Calling) 능력**을 평가하고,
> 전문적인 Excel 리포트를 자동 생성하는 프로젝트입니다.

[![FunctionChat-Bench](https://img.shields.io/badge/Based%20on-FunctionChat--Bench-blue)](https://github.com/kakao/FunctionChat-Bench)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](LICENSE)

---

## 목차

| 섹션 | 설명 |
|-----|------|
| [프로젝트 소개](#프로젝트-소개) | 이 벤치마크가 무엇을 평가하는지 |
| [데이터셋 구성](#데이터셋-구성) | 3가지 평가 데이터셋 상세 |
| [평가 지표](#평가-지표) | Call, Completion, Slot, Relevance 설명 |
| [평가 산식](#평가-산식) | 점수 계산 방법 |
| [Tool 호출 지시 방법](#tool-호출-지시-방법) | 모델에게 함수 사용을 알려주는 방식 |
| [결과 분석](#결과-분석) | 1,306건 전체 채점 최종 결과 |
| [빠른 시작](#빠른-시작) | 설치 및 실행 가이드 |
| [해결한 이슈](#해결한-이슈) | 트러블슈팅 |
| [FAQ](#faq) | 자주 묻는 질문 |

---

## 프로젝트 소개

### 무엇을 평가하나요?

**FunctionChat-Bench**는 LLM이 대화 중에 **도구(함수)를 올바르게 사용**할 수 있는지 평가하는 한국어 벤치마크입니다.

| 항목 | 내용 |
|-----|------|
| 원본 | Kakao에서 공개한 [FunctionChat-Bench](https://github.com/kakao/FunctionChat-Bench) |
| 언어 | 한국어 |
| 평가 방식 | LLM-as-Judge (GPT-4.1이 채점) |
| 총 평가 건수 | **1,306건** |

### 평가 철학

단순히 "함수를 호출할 수 있는가?"가 아니라, **대화 맥락에서 적절한 행동**을 평가합니다.

| 상황 | 올바른 행동 | 평가 유형 |
|------|-----------|----------|
| 도구로 처리 가능한 요청 | 올바른 함수 선택 + 정확한 인자 추출 | **Call** |
| 도구 실행 결과 전달 | 결과를 자연스러운 한국어로 응답 | **Completion** |
| 필수 정보가 부족한 요청 | 필요한 정보를 사용자에게 질문 | **Slot** |
| 도구로 불가능한 요청 | 억지로 호출하지 않고 적절히 거절 | **Relevance** |

---

## 데이터셋 구성

### 전체 요약

| 데이터셋 | 파일명 | 평가 건수 | 설명 |
|---------|-------|----------|------|
| **Dialog** | `FunctionChat-Dialog.jsonl` | 200건 | 다중 턴 대화에서 도구 사용 |
| **SingleCall** | `FunctionChat-Singlecall.jsonl` | 500건 | 단일 턴에서 올바른 함수 선택 |
| **CallDecision** | `FunctionChat-CallDecision.jsonl` | 606건 | 함수 호출 여부 판단 |
| **합계** | - | **1,306건** | - |

---

### 1. Dialog (다중 턴 대화)

실제 대화처럼 여러 턴에 걸쳐 도구를 사용하는 시나리오입니다.

| 항목 | 내용 |
|-----|------|
| 대화 시나리오 수 | 45개 |
| 총 평가 턴 수 | 200턴 |
| 평가 유형 | call, completion, slot, relevance 혼합 |

**데이터 구조 예시:**

```json
{
  "dialog_num": 1,
  "tools": [{"type": "function", "function": {"name": "create_user", ...}}],
  "turns": [
    {
      "serial_num": 1,
      "query": [{"role": "user", "content": "새 계정을 만들고 싶습니다."}],
      "ground_truth": {"content": "네, 성함과 이메일, 비밀번호를 알려주세요."},
      "type_of_output": "slot"
    }
  ]
}
```

---

### 2. SingleCall (단일 턴 함수 선택)

다양한 난이도에서 올바른 함수를 선택하는지 평가합니다.

| 항목 | 내용 |
|-----|------|
| 함수 종류 | 25개 |
| 함수당 쿼리 | 4개 |
| 난이도 유형 | 5가지 |
| 총 평가 건수 | 25 x 4 x 5 = **500건** |

**난이도 유형 (tools_type):**

| 타입 | 후보 함수 구성 | 난이도 | 설명 |
|------|--------------|-------|------|
| `1_exact` | 정답 1개 | 매우 쉬움 | 선택지가 하나뿐 |
| `4_random` | 정답 + 무관한 3개 | 쉬움 | 무관한 함수는 구분 용이 |
| `4_close` | 정답 + 유사 3개 | 보통 | 비슷한 기능이라 헷갈림 |
| `8_random` | 정답 + 무관한 7개 | 어려움 | 후보가 많음 |
| `8_close` | 정답 + 유사 7개 | 매우 어려움 | 후보 많고 유사 |

> **예시:** 날씨 조회 함수가 정답일 때
> - `4_random`: 날씨 + 환율변환 + 번역 + 이미지생성 (구분 쉬움)
> - `4_close`: 날씨 + 일정조회 + 메모추가 + 알람설정 (구분 어려움)

---

### 3. CallDecision (호출 판단)

"함수를 호출해야 하는가? 말아야 하는가?"를 판단하는 능력을 평가합니다.

| 카테고리 | 평가 건수 | 올바른 행동 |
|---------|----------|-----------|
| **CALL** | 약 150건 | 함수 호출해야 함 |
| **COMPLETION** | 약 150건 | 결과를 자연어로 전달 |
| **SLOT** | 약 150건 | 누락 정보 질문 |
| **RELEVANCE** | 약 156건 | 호출하지 않아야 함 |
| **합계** | **606건** | - |

---

## 평가 지표

### LLM-as-Judge 방식

| 단계 | 설명 |
|-----|------|
| 1. 모델 응답 수집 | 평가 대상 모델이 각 테스트 케이스에 응답 |
| 2. Exact Match 검사 | 정답과 정확히 일치하는지 확인 |
| 3. Rubric 평가 | 불일치 시 Judge(GPT-4.1)가 rubric에 따라 평가 |
| 4. Pass/Fail 판정 | 최종 결과 기록 |

---

### 평가 유형별 Pass/Fail 기준

#### Call (함수 호출 정확도)

| 결과 | 조건 |
|-----|------|
| **Pass** | 올바른 함수 선택 + 정확한 함수명 + 올바른 argument 키/타입/값 |
| **Fail** | 함수 미선택, 잘못된 함수, 오타, 잘못된 키, 타입 오류, 값 오류 |

**Fail 세부 유형:**

| 오류 유형 | 설명 | 예시 |
|----------|------|-----|
| 함수 선택 오류 | 다른 함수 호출 | `getWeather` 대신 `getNews` 호출 |
| 함수명 오류 | 철자 틀림 | `getWeathr` |
| 키 오류 | 없는 argument 생성 | `{"city": "서울"}` (정답: `location`) |
| 타입 오류 | 잘못된 타입 | 정수여야 하는데 실수 생성 |
| 값 오류 | 허용 범위 초과 | 쿼리에 없는 값 환각 |

---

#### Completion (결과 전달)

| 결과 | 조건 |
|-----|------|
| **Pass** | 함수 결과를 자연스러운 한국어로 전달, 의미 왜곡 없음 |
| **Fail** | JSON 그대로 출력, 의미 왜곡, 영어로만 응답 |

**예시:**

| 함수 결과 | Pass 응답 | Fail 응답 |
|----------|----------|----------|
| `{"temp": 20, "sky": "맑음"}` | "서울은 현재 맑고 20도입니다." | `{"temp": 20, "sky": "맑음"}` |

---

#### Slot (정보 요청)

| 결과 | 조건 |
|-----|------|
| **Pass** | 누락된 필수 정보를 **모두 빠짐없이** 질문 |
| **Fail** | 정보 누락 채 호출, 환각값 생성, 일부만 질문, 중복 질문 |

**예시:**

| 사용자 요청 | 필요 정보 | Pass 응답 | Fail 응답 |
|-----------|----------|----------|----------|
| "일정 추가해줘" | 제목, 날짜, 시간 | "일정 제목, 날짜, 시간을 알려주세요." | "언제요?" (일부만 질문) |

---

#### Relevance (관련성 판단)

| 결과 | 조건 |
|-----|------|
| **Pass** | 함수로 불가능함을 인지하고 거절/설명 |
| **Fail** | 불필요한 함수 호출, 할 수 없는 일을 했다고 거짓말 |

**예시:**

| 사용자 요청 | 제공된 함수 | Pass 응답 | Fail 응답 |
|-----------|-----------|----------|----------|
| "문자 보내줘" | 날씨, 일정, 메모 | "문자 전송 기능은 제공하지 않습니다." | 메모 함수 호출 |

---

## 평가 산식

### 기본 공식

```
Pass Rate = Pass 건수 / Total 건수
Accuracy = Pass Rate × 100%
```

### 데이터셋별 점수 계산

| 데이터셋 | 계산 방식 | 세부 |
|---------|---------|------|
| **Dialog** | 유형별 Pass Rate + Micro Average | call, completion, slot, relevance 각각 계산 후 전체 평균 |
| **SingleCall** | 난이도별 Pass Rate + 전체 Pass Rate | 1_exact, 4_random, 4_close, 8_random, 8_close 각각 |
| **CallDecision** | 카테고리별 Pass Rate + 전체 Pass Rate | CALL, COMPLETION, SLOT, RELEVANCE 각각 |

### 최종 Accuracy 예시

| 모델 | Dialog (200) | SingleCall (500) | CallDecision (606) | Total (1306) | Accuracy |
|-----|-------------|-----------------|-------------------|--------------|----------|
| 모델 A | 150 pass | 400 pass | 500 pass | 1050 pass | 80.4% |
| 모델 B | 120 pass | 350 pass | 450 pass | 920 pass | 70.4% |

---

## Tool 호출 지시 방법

모델에게 "어떤 함수를 어떤 인자로 호출하라"고 알려주는 방식입니다.

### 구성 요소

| 요소 | 역할 | 예시 |
|-----|------|-----|
| **System Prompt** | 모델의 행동 지침 | "적합한 function이 있으면 호출하세요" |
| **Tools Schema** | 사용 가능한 함수 정의 | `{"name": "getWeather", "parameters": {...}}` |
| **Messages** | 대화 맥락 | `[{"role": "user", "content": "서울 날씨"}]` |
| **tool_choice** | 호출 정책 | `"auto"` (모델이 판단) |

---

### 1. System Prompt

모든 평가에서 사용되는 시스템 프롬프트:

```
AI assistant로서, user와 한국어로 대화를 나누세요. 
적합한 function이 있으면, 자체 지식으로 답하지 말고 function 호출을 통해 user의 요청을 해결하세요. 
function 호출에 필요한 파라미터 값을 임의로 생성하지 마세요. 
필수 정보가 부족할 경우 user에게 질문해 정보를 얻으세요. 
누락된 필수 정보가 여러가지이면, 각각을 모두 빠짐없이 구체적으로 요청하세요. 
특별한 이유가 없다면, 파라미터 값을 생성할 때 user의 한국어 표현을 영어로 변경하지 마세요.
```

---

### 2. Tools Schema 예시

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

---

### 3. 전체 API 요청 흐름

```
┌─────────────────────────────────────────────────────────┐
│ 1. 요청 생성                                              │
│    - System Prompt + User Query + Tools Schema           │
│    - tool_choice: "auto"                                 │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 2. 모델 응답                                              │
│    A) 함수 호출: tool_calls 필드에 함수명 + arguments      │
│    B) 자연어 응답: content 필드에 텍스트                   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Judge 평가                                            │
│    - Ground Truth와 비교                                  │
│    - Rubric에 따라 pass/fail 판정                         │
└─────────────────────────────────────────────────────────┘
```

---

### 4. 모델 응답 형식

**함수 호출 시:**
```json
{
  "message": {
    "role": "assistant",
    "content": null,
    "tool_calls": [{
      "type": "function",
      "function": {
        "name": "informWeather",
        "arguments": "{\"location\": \"서울\"}"
      }
    }]
  }
}
```

**자연어 응답 시:**
```json
{
  "message": {
    "role": "assistant",
    "content": "날씨 조회 기능이 없어서 도움드리기 어렵습니다."
  }
}
```

---

---

## 결과 분석

### 🏆 최종 벤치마크 결과 (1,306건 전체 채점 완료)

모든 케이스에 대해 **Skip 없이 100% 채점**을 완료한 최종 결과입니다.

| 모델 (순위) | Dialog (200) | SingleCall (500) | CallDecision (606) | **Total Pass** | **Accuracy** |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **1. Qwen3-32B** | 95 (47.5%) | **429 (85.8%)** | 192 (31.7%) | **716 / 1306** | **54.8%** |
| **2. Qwen3-Next-80B** | 85 (42.5%) | 400 (80.0%) | **198 (32.7%)** | **683 / 1306** | **52.3%** |
| **3. Qwen3-14B** | 84 (42.0%) | 403 (80.6%) | 186 (30.7%) | **673 / 1306** | **51.5%** |
| **4. Llama-3.3-70B** | **96 (48.0%)** | 208 (41.6%) | 65 (10.7%) | **369 / 1306** | **28.3%** |
| **5. Mistral-Small-24B** | 94 (47.0%) | 80 (16.0%) | 192 (31.7%) | **366 / 1306** | **28.0%** |

### 🔍 주요 분석 포인트

1. **Qwen 시리즈의 Tool-Use 압도적 우위**
   - Qwen3 계열 모델들이 함수 선택(SingleCall)에서 타 모델 대비 2배 이상의 높은 성능을 보이며 상위권을 독식했습니다.
   - 특히 **Qwen3-32B**는 80B 모델보다도 높은 정확도를 기록하며 가성비와 성능 모두를 잡은 모습을 보여줍니다.

2. **Llama-3.3-70B의 양면성**
   - 대화 능력(Dialog)에서는 48.0%로 가장 높은 점수를 기록했으나, 복잡한 함수 호출 판단(CallDecision)에서 10.7%라는 낮은 점수를 기록하며 Tool-use 특화 튜닝의 부재를 드러냈습니다.

3. **함수 선택 vs 호출 판단**
   - Mistral-Small-24B는 호출 여부 판단(CallDecision) 능력은 준수(31.7%)하나, 정작 호출 시 어떤 함수를 쓸지(SingleCall, 16.0%)에서 가장 취약했습니다.

---

## 빠른 시작

### 설치

| 단계 | 명령어 |
|-----|-------|
| 1. 클론 | `git clone https://github.com/mink555/mcp-llm-bm-v1.git && cd mcp-llm-bm-v1` |
| 2. 의존성 | `cd FunctionChat-Bench && pip install -r requirements.txt && cd ..` |
| 3. 환경변수 | `.env` 파일에 `OPENROUTER_API_KEY=sk-or-v1-...` 추가 |

### 실행

| 목적 | 명령어 | 소요 시간 |
|-----|-------|----------|
| 퀵 테스트 | `python quick_test.py --sample-size 2` | 5-10분/모델 |
| 전체 평가 | `python run_evaluation.py` | 1-3시간/모델 |
| 리포트만 생성 | `python generate_excel_report.py` | 수 초 |

### 옵션

| 옵션 | 설명 | 예시 |
|-----|------|-----|
| `--models` | 특정 모델만 평가 | `--models "qwen/qwen3-14b"` |
| `--sample-size` | 샘플 크기 (퀵테스트) | `--sample-size 5` |
| `--skip-excel` | 엑셀 생성 스킵 | `--skip-excel` |

---

## 결과물

### 폴더 구조

| 폴더 | 내용 | Git 추적 |
|-----|------|---------|
| `reports/` | Excel 리포트 | X (gitignore) |
| `result/` | 모델 응답 JSONL | X (gitignore) |
| `score/` | Judge 평가 결과 TSV | X (gitignore) |

### Excel 리포트 구성

| 시트 | 내용 |
|-----|------|
| **Summary** | 전체 성능 요약, 카테고리별 점수 |
| **Details** | 테스트 케이스별 상세 (PASS/FAIL, 오류 유형) |
| **Ranking** | 모델 간 성능 순위 (통합 리포트) |
| **Category Matrix** | 카테고리별 모델 비교표 (통합 리포트) |

---

## 해결한 이슈

| 이슈 | 원인 | 해결 |
|-----|------|-----|
| **429 Rate Limit** | Judge API 호출 과다 | `--num-threads 1`, 지수 백오프 (4s→8s→16s...) |
| **402 크레딧 부족** | API 크레딧 소진 | 즉시 실패 처리, 해당 케이스 skip 후 계속 진행 |
| **JSON 파싱 오류** | 모델이 arguments를 잘못 생성 | 모델 실력 문제로 fail 처리 (정상 동작) |
| **Mistral tool_call_id** | ID 형식 불일치 | 9자리 영숫자로 normalize |
| **ZeroDivisionError** | 평가 건수 0 | 분모 0일 때 0.0 반환 |
| **API 키 노출** | config에 키 직접 저장 | `${ENV_VAR}` placeholder 지원 |

---

## FAQ

| 질문 | 답변 |
|-----|------|
| API 키 필요한가요? | 네, OpenRouter API 키 필요 (평가 모델 + Judge 모두 사용) |
| 평가 중단 시 재개 가능? | 네, 결과가 실시간 저장되어 이어서 진행 |
| Judge 모델 변경 가능? | `config/openai.cfg`에서 `api_version` 수정 |
| JSON 오류 많이 보이는데? | 모델의 Function Calling 능력 부족 (정상, fail 처리됨) |
| `tool_choice="auto"` 의미? | 모델이 스스로 함수 호출 여부 결정 |
| 특정 모델만 평가하려면? | `--models "모델명"` 옵션 사용 |
| Excel만 다시 생성하려면? | `python generate_excel_report.py` 실행 |

---

## 참고 자료

| 자료 | 링크 |
|-----|------|
| FunctionChat-Bench 원본 | [GitHub](https://github.com/kakao/FunctionChat-Bench) |
| 논문 (arXiv) | [arxiv.org/abs/2411.14054](https://arxiv.org/abs/2411.14054) |
| OpenRouter API | [openrouter.ai/docs](https://openrouter.ai/docs) |
| 평가 Rubric | `FunctionChat-Bench/data/rubric_*.txt` |

---

## 라이선스

이 프로젝트는 [FunctionChat-Bench](https://github.com/kakao/FunctionChat-Bench)를 기반으로 하며, **Apache 2.0 라이선스**를 따릅니다.

---

<div align="center">

**Based on [FunctionChat-Bench](https://github.com/kakao/FunctionChat-Bench) by Kakao**

</div>
