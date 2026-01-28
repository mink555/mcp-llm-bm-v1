# KAKAO-FunctionChat-Bench (OpenRouter)

> OpenRouter API를 통해 여러 LLM 모델의 **Tool-Use(Function Calling) 능력**을 평가하고, 전문적인 Excel 리포트를 자동 생성하는 프로젝트입니다.

[![FunctionChat-Bench](https://img.shields.io/badge/Based%20on-FunctionChat--Bench-blue)](https://github.com/kakao/FunctionChat-Bench)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](LICENSE)

---

## 목차

| 섹션 | 주요 내용 |
|:---|:---|
| [프로젝트 소개](#프로젝트-소개) | 벤치마크 목적 및 평가 철학 |
| [데이터셋 구성](#데이터셋-구성) | 싱글턴/멀티턴 데이터셋 상세 구조 |
| [평가 프로세스](#평가-프로세스) | LLM-as-Judge 채점 흐름 및 기준 |
| [결과 분석](#결과-분석) | 1,306건 전체 채점 최종 결과 요약 |
| [핵심 코드 파일](#핵심-코드-파일) | 주요 스크립트 역할 및 실행 방법 |
| [사용 가이드](#사용-가이드) | 설치, 설정, 실행 단계별 안내 |
| [해결한 이슈 및 FAQ](#해결한-이슈-및-faq) | 트러블슈팅 및 자주 묻는 질문 |

---

## 프로젝트 소개

### 평가 개요
**FunctionChat-Bench**는 LLM이 한국어 대화 맥락 속에서 도구(함수)를 얼마나 정확하게 선택하고 사용하는지 측정합니다. 특히 단순 호출을 넘어 **대화의 흐름을 유지하는 능력**을 중점적으로 평가합니다.

| 구분 | 상세 내용 |
|:---|:---|
| 원본 소스 | Kakao FunctionChat-Bench |
| 평가 언어 | 한국어 (Korean) |
| 채점 방식 | LLM-as-Judge (GPT-4.1 기반 자동 채점) |
| 전체 규모 | 총 1,306개의 테스트 케이스 |

### 평가 유형 및 정의
| 유형 | 정의 | 올바른 모델의 행동 |
|:---|:---|:---|
| **Call** | 도구 호출 | 정확한 함수 선택 및 인자(Arguments) 추출 |
| **Completion** | 결과 전달 | 도구 실행 결과를 자연스러운 한국어로 요약 응답 |
| **Slot** | 정보 요청 | 필수 인자가 누락된 경우 사용자에게 추가 질문 |
| **Relevance** | 관련성 판단 | 도구로 해결 불가능한 경우 적절히 거절 및 설명 |

---

## 데이터셋 구성

### 데이터셋 비교 (싱글턴 vs 멀티턴)
본 벤치마크는 단발성 호출뿐만 아니라 실제 서비스와 유사한 연속 대화 환경을 모두 포함합니다.

| 데이터셋 | 대화 유형 | 평가 건수 | 특징 |
|:---|:---:|:---:|:---|
| **SingleCall** | **싱글턴 (Single-turn)** | 500건 | 주어진 질문에 즉시 적절한 함수를 선택하는 능력 측정 |
| **Dialog** | **멀티턴 (Multi-turn)** | 200건 | 이전 대화 맥락을 유지하며 단계별로 도구를 사용하는 능력 측정 |
| **CallDecision** | 혼합 | 606건 | 현재 시점에서 함수 호출이 필요한 상황인지 판단하는 능력 측정 |

### 멀티턴(Dialog) 구조 상세
하나의 시나리오 안에서 대화가 누적되며 평가가 진행됩니다.

```
[ 대화 흐름 예시 ]

Turn 1 (Slot 평가)
  User: "새 계정을 만들고 싶어요."
  Assistant: "성함과 이메일을 알려주시겠어요?" (필수 정보 요청)

Turn 2 (Call 평가)
  User: "이름은 홍길동, 이메일은 hong@example.com 입니다."
  Assistant: tool_calls: create_user(name="홍길동", ...) (함수 호출)

Turn 3 (Completion 평가)
  Tool: {"status": "success"}
  Assistant: "계정 생성이 완료되었습니다." (결과 요약 응답)
```

### SingleCall 난이도 구성
| 난이도 타입 | 후보 함수 구성 | 평가 목적 |
|:---|:---|:---|
| `1_exact` | 정답 1개 | 기본적인 함수 호출 형식 준수 여부 |
| `4_random` | 정답 1개 + 무관한 함수 3개 | 명확한 차이가 있는 상황에서의 선택 능력 |
| `4_close` | 정답 1개 + 유사 도메인 함수 3개 | 미세한 기능 차이를 구분하는 정밀도 |
| `8_random` | 정답 1개 + 무관한 함수 7개 | 많은 선택지 속에서의 검색 효율성 |
| `8_close` | 정답 1개 + 유사 도메인 함수 7개 | 고난도 상황에서의 최적 함수 선택 능력 |

---

## 평가 프로세스

### 시스템 아키텍처 흐름도
```
[ 입력 데이터 ] ─────────┐
(Query + Tools)         │
                        ▼
[ 평가 대상 모델 ] ─────── (OpenRouter API 호출)
(Response 생성)         │
                        ▼
[ 1차 검증 ] ─────────── (Exact Match 확인)
(정답과 일치 여부)        │
                        ▼
[ 2차 채점 ] ─────────── (LLM-as-Judge: GPT-4.1)
(Rubric 기반 평가)       │
                        ▼
[ 결과 산출 ] ─────────── (TSV 저장 및 Excel 리포트 생성)
```

### 채점 기준 (Pass/Fail)
| 평가 항목 | Pass 기준 | Fail 주요 원인 |
|:---|:---|:---|
| **Call** | 함수명 및 모든 인자(Key/Value) 일치 | 함수 오선택, 인자 누락, 환각(Hallucination) 값 생성 |
| **Completion** | 결과값을 왜곡 없이 자연스럽게 전달 | JSON 형식 그대로 출력, 의미 왜곡, 영어 응답 |
| **Slot** | 누락된 모든 필수 정보를 질문 | 일부 정보만 질문, 질문 없이 임의 값으로 호출 |
| **Relevance** | 불가능함을 인지하고 적절히 거절 | 무관한 함수 호출, 할 수 없는 일을 했다고 거짓말 |

---

## 결과 분석

### 최종 벤치마크 결과 (1,306건 전체 채점 완료)
| 순위 | 모델명 | Dialog (200) | SingleCall (500) | CallDecision (606) | **Accuracy** |
|:---:|:---|:---:|:---:|:---:|:---:|
| **1** | **Qwen3-32B** | 47.5% | **85.8%** | 31.7% | **54.8%** |
| **2** | **Qwen3-Next-80B** | 42.5% | 80.0% | **32.7%** | **52.3%** |
| **3** | **Qwen3-14B** | 42.0% | 80.6% | 30.7% | **51.5%** |
| **4** | **Llama-3.3-70B** | **48.0%** | 41.6% | 10.7% | **28.3%** |
| **5** | **Mistral-Small-24B** | 47.0% | 16.0% | 31.7% | **28.0%** |

---

## 핵심 코드 파일

### 프로젝트 구조
```
KAKAO-FunctionChat-Bench/
├── run_evaluation.py          # [1] 전체 평가 자동화 스크립트
├── quick_test.py              # [2] 빠른 검증용 테스트 스크립트
├── generate_excel_report.py   # [3] Excel 리포트 생성기
├── .env                       # API 키 설정 (git 제외)
│
└── FunctionChat-Bench/
    ├── evaluate.py            # [4] 벤치마크 엔진 (CLI 엔트리)
    ├── config/
    │   └── openai.cfg         # [5] Judge 모델 설정
    └── src/
        ├── api_executor.py        # [6] API 호출 및 재시도 로직
        └── evaluation_handler.py  # [7] LLM-as-Judge 채점 로직
```

### 핵심 파일 상세 설명
| 번호 | 파일명 | 역할 | 실행 방법 |
|:---:|:---|:---|:---|
| **1** | `run_evaluation.py` | 5개 모델 전체 평가 + 리포트 생성 자동화 | `python run_evaluation.py` |
| **2** | `quick_test.py` | 카테고리별 샘플링 후 빠른 검증 | `python quick_test.py --sample-size 2` |
| **3** | `generate_excel_report.py` | TSV 결과를 Excel 리포트로 변환 | `python generate_excel_report.py` |
| **4** | `evaluate.py` | 개별 데이터셋 평가 (Dialog/SingleCall/Common) | 아래 상세 명령어 참조 |
| **5** | `openai.cfg` | Judge 모델 및 API 엔드포인트 설정 | 직접 편집 |
| **6** | `api_executor.py` | OpenRouter API 연동 + 지수 백오프 재시도 | 내부 모듈 (직접 실행 X) |
| **7** | `evaluation_handler.py` | GPT-4.1 Judge 호출 + 실시간 결과 저장 | 내부 모듈 (직접 실행 X) |

### evaluate.py 개별 실행 명령어
```bash
# Dialog (멀티턴) 평가
python evaluate.py dialog \
  --input_path data/FunctionChat-Dialog.jsonl \
  --system_prompt_path data/system_prompt.txt \
  --model "qwen/qwen3-32b" \
  --api_key $OPENROUTER_API_KEY \
  --base_url "https://openrouter.ai/api/v1"

# SingleCall (싱글턴) 평가
python evaluate.py singlecall \
  --input_path data/FunctionChat-Singlecall.jsonl \
  --system_prompt_path data/system_prompt.txt \
  --tools_type all \
  --model "qwen/qwen3-32b" \
  --api_key $OPENROUTER_API_KEY \
  --base_url "https://openrouter.ai/api/v1"

# CallDecision (호출 판단) 평가
python evaluate.py common \
  --input_path data/FunctionChat-CallDecision.jsonl \
  --model "qwen/qwen3-32b" \
  --api_key $OPENROUTER_API_KEY \
  --base_url "https://openrouter.ai/api/v1"
```

---

## 사용 가이드

### 단계별 실행 절차
| 단계 | 작업 내용 | 실행 명령어 / 방법 |
|:---:|:---|:---|
| **1** | 환경 구축 | `git clone` 및 `pip install -r requirements.txt` |
| **2** | API 설정 | `.env` 파일 생성 및 `OPENROUTER_API_KEY` 입력 |
| **3** | 테스트 실행 | `python quick_test.py --sample-size 2` (검증용) |
| **4** | 전체 평가 | `python run_evaluation.py` (전체 채점) |
| **5** | 리포트 확인 | `reports/` 폴더 내 생성된 Excel 파일 확인 |

---

## 해결한 이슈 및 FAQ

### 트러블슈팅 요약
| 현상 | 원인 | 해결 방안 |
|:---|:---|:---|
| **429 Rate Limit** | Judge API 호출 속도 제한 | `--num-threads 1` 설정 및 지수 백오프 적용 |
| **402 Insufficient Credits** | API 잔액 부족 | 즉시 실패 처리 후 다음 케이스로 진행 (Skip 방지) |
| **JSON 파싱 오류** | 모델의 출력 형식 불일치 | 모델의 능력 부족으로 판단하여 Fail 처리 |
| **API 키 노출 위험** | 설정 파일 내 평문 저장 | `${ENV_VAR}` 형식을 통한 환경변수 주입 지원 |

### 자주 묻는 질문 (FAQ)
| 질문 | 답변 |
|:---|:---|
| 멀티턴 대화는 어떻게 평가하나요? | 이전 대화 이력이 모두 포함된 상태에서 모델의 다음 행동을 채점합니다. |
| 평가 중단 시 처음부터 다시 하나요? | 아닙니다. 결과가 실시간 저장되어 중단 시점부터 재개됩니다. |
| Judge 모델을 바꿀 수 있나요? | `config/openai.cfg`의 `api_version`을 수정하여 변경 가능합니다. |

---

## 참고 자료 및 라이선스

| 항목 | 내용 |
|:---|:---|
| **원본 저장소** | [Kakao FunctionChat-Bench](https://github.com/kakao/FunctionChat-Bench) |
| **관련 논문** | [arXiv:2411.14054](https://arxiv.org/abs/2411.14054) |
| **라이선스** | Apache License 2.0 |

<div align="center">
Based on FunctionChat-Bench by Kakao
</div>
