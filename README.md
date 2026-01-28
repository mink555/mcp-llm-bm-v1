# FunctionChat-Bench OpenRouter 평가 프로젝트

> OpenRouter API를 통해 여러 LLM 모델의 **Tool-Use(Function Calling) 능력**을 평가하고, 전문적인 Excel 리포트를 자동 생성하는 프로젝트입니다.

[![FunctionChat-Bench](https://img.shields.io/badge/Based%20on-FunctionChat--Bench-blue)](https://github.com/kakao/FunctionChat-Bench)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](LICENSE)

---

## 목차

| 섹션 | 주요 내용 |
|:---|:---|
| [프로젝트 소개](#프로젝트-소개) | 벤치마크 목적 및 평가 철학 |
| [데이터셋 구성](#데이터셋-구성) | Dialog, SingleCall, CallDecision 상세 |
| [평가 프로세스](#평가-프로세스) | LLM-as-Judge 채점 흐름 및 기준 |
| [결과 분석](#결과-분석) | 1,306건 전체 채점 최종 결과 요약 |
| [사용 가이드](#사용-가이드) | 설치, 설정, 실행 단계별 안내 |
| [해결한 이슈 및 FAQ](#해결한-이슈-및-faq) | 트러블슈팅 및 자주 묻는 질문 |

---

## 프로젝트 소개

### 평가 개요
**FunctionChat-Bench**는 LLM이 한국어 대화 맥락 속에서 도구(함수)를 얼마나 정확하게 선택하고 사용하는지 측정합니다.

| 구분 | 상세 내용 |
|:---|:---|
| 원본 소스 | Kakao FunctionChat-Bench |
| 평가 언어 | 한국어 (Korean) |
| 채점 방식 | LLM-as-Judge (GPT-4.1 기반 자동 채점) |
| 전체 규모 | 총 1,306개의 테스트 케이스 |

### 평가 유형 및 정의
단순 호출 여부를 넘어, 대화 상황에 따른 4가지 핵심 능력을 평가합니다.

| 유형 | 정의 | 올바른 모델의 행동 |
|:---|:---|:---|
| **Call** | 도구 호출 | 정확한 함수 선택 및 인자(Arguments) 추출 |
| **Completion** | 결과 전달 | 도구 실행 결과를 자연스러운 한국어로 요약 응답 |
| **Slot** | 정보 요청 | 필수 인자가 누락된 경우 사용자에게 추가 질문 |
| **Relevance** | 관련성 판단 | 도구로 해결 불가능한 경우 적절히 거절 및 설명 |

---

## 데이터셋 구성

### 데이터셋 요약표
| 데이터셋 | 파일명 | 평가 건수 | 핵심 평가 요소 |
|:---|:---|:---|:---|
| **Dialog** | `FunctionChat-Dialog.jsonl` | 200건 | 다중 턴 대화 맥락에서의 복합적인 도구 사용 |
| **SingleCall** | `FunctionChat-Singlecall.jsonl` | 500건 | 다양한 후보군 중 정답 함수를 찾아내는 선택 능력 |
| **CallDecision** | `FunctionChat-CallDecision.jsonl` | 606건 | 현재 상황에서 함수 호출이 필요한지 여부 판단 |

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
모든 케이스에 대해 **Skip 없이 100% 채점**을 완료한 최종 순위입니다.

| 순위 | 모델명 | Dialog (200) | SingleCall (500) | CallDecision (606) | **Accuracy** |
|:---:|:---|:---:|:---:|:---:|:---:|
| **1** | **Qwen3-32B** | 47.5% | **85.8%** | 31.7% | **54.8%** |
| **2** | **Qwen3-Next-80B** | 42.5% | 80.0% | **32.7%** | **52.3%** |
| **3** | **Qwen3-14B** | 42.0% | 80.6% | 30.7% | **51.5%** |
| **4** | **Llama-3.3-70B** | **48.0%** | 41.6% | 10.7% | **28.3%** |
| **5** | **Mistral-Small-24B** | 47.0% | 16.0% | 31.7% | **28.0%** |

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

### 주요 실행 옵션
| 옵션명 | 설명 | 예시 |
|:---|:---|:---|
| `--models` | 평가할 특정 모델 지정 | `--models "qwen/qwen3-32b"` |
| `--sample-size` | 퀵 테스트 시 카테고리별 샘플 수 | `--sample-size 5` |
| `--skip-excel` | 평가 후 엑셀 생성 단계 건너뛰기 | `--skip-excel` |

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
| 평가 중단 시 처음부터 다시 하나요? | 아닙니다. 결과가 실시간 저장되어 중단 시점부터 재개됩니다. |
| Judge 모델을 바꿀 수 있나요? | `config/openai.cfg`의 `api_version`을 수정하여 변경 가능합니다. |
| 특정 데이터셋만 평가하고 싶을 때? | `run_evaluation.py` 내의 `EVALUATION_TYPES`를 수정하여 조절 가능합니다. |

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
