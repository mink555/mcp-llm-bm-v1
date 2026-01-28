#!/usr/bin/env python3
"""
FunctionChat-Bench 퀵 테스트 스크립트
각 평가 카테고리별로 2개씩 샘플링하여 빠르게 테스트합니다.
"""

import os
import sys
import json
import subprocess
import random
import argparse
from pathlib import Path
from dotenv import load_dotenv

REPO_PATH = Path(__file__).parent.absolute()
FUNCTIONCHAT_BENCH_PATH = REPO_PATH / "FunctionChat-Bench"

# 환경 변수 로드 (파일이 없어도 계속 진행)
try:
    load_dotenv()
except Exception:
    pass  # .env 파일이 없거나 권한 문제가 있어도 계속 진행

def require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise SystemExit(
            f"[ERROR] 환경 변수 `{name}` 이(가) 없습니다. "
            f"프로젝트 루트에 `.env`를 생성하거나 export로 설정하세요."
        )
    return val

# OpenRouter API 설정
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

# 테스트할 모델 목록
TEST_MODELS = [
    "meta-llama/llama-3.3-70b-instruct",
    "mistralai/mistral-small-3.2-24b-instruct",
    "qwen/qwen3-32b",
    "qwen/qwen3-14b",
    "qwen/qwen3-next-80b-a3b-instruct",
]

# 평가 설정
TEMPERATURE = 0.0
DEFAULT_SAMPLE_SIZE = 2  # 각 카테고리별 샘플 수


def sample_data(input_file, output_file, sample_size, filter_func=None):
    """데이터 파일에서 샘플링"""
    samples = []
    with open(input_file, 'r', encoding='utf-8') as f:
        all_data = [json.loads(line) for line in f]
    
    if filter_func:
        filtered_data = [d for d in all_data if filter_func(d)]
    else:
        filtered_data = all_data
    
    if len(filtered_data) <= sample_size:
        samples = filtered_data
    else:
        samples = random.sample(filtered_data, sample_size)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    
    return len(samples)


def create_dialog_samples(sample_size: int):
    """Dialog 데이터 샘플링 (각 type_of_output별 2개씩)"""
    input_file = FUNCTIONCHAT_BENCH_PATH / "data" / "FunctionChat-Dialog.jsonl"
    output_file = FUNCTIONCHAT_BENCH_PATH / "data" / "FunctionChat-Dialog-sample.jsonl"
    
    with open(input_file, 'r', encoding='utf-8') as f:
        all_dialogs = [json.loads(line) for line in f]
    
    samples = []
    type_counts = {"call": 0, "completion": 0, "slot": 0, "relevance": 0}
    
    for dialog in all_dialogs:
        for turn in dialog.get("turns", []):
            output_type = turn.get("type_of_output")
            if output_type in type_counts and type_counts[output_type] < sample_size:
                # 해당 dialog 전체를 포함
                if dialog not in samples:
                    samples.append(dialog)
                type_counts[output_type] += 1
                if all(count >= sample_size for count in type_counts.values()):
                    break
        if all(count >= sample_size for count in type_counts.values()):
            break
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    
    print(f"[OK] Dialog 샘플 생성: {len(samples)}개 다이얼로그")
    return output_file


def create_singlecall_samples(sample_size: int):
    """SingleCall 데이터 샘플링 (각 tools_type별 2개씩)"""
    input_file = FUNCTIONCHAT_BENCH_PATH / "data" / "FunctionChat-Singlecall.jsonl"
    output_file = FUNCTIONCHAT_BENCH_PATH / "data" / "FunctionChat-Singlecall-sample.jsonl"
    
    with open(input_file, 'r', encoding='utf-8') as f:
        all_data = [json.loads(line) for line in f]
    
    samples = []
    type_counts = {}
    
    for data in all_data:
        tools_type = data.get("tools_type", "unknown")
        if tools_type not in type_counts:
            type_counts[tools_type] = 0
        
        if type_counts[tools_type] < sample_size:
            samples.append(data)
            type_counts[tools_type] += 1
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    
    print(f"[OK] SingleCall 샘플 생성: {len(samples)}개 (tools_type별 {sample_size}개씩)")
    return output_file


def create_calldecision_samples(sample_size: int):
    """CallDecision 데이터 샘플링 (2개)"""
    input_file = FUNCTIONCHAT_BENCH_PATH / "data" / "FunctionChat-CallDecision.jsonl"
    output_file = FUNCTIONCHAT_BENCH_PATH / "data" / "FunctionChat-CallDecision-sample.jsonl"
    
    count = sample_data(input_file, output_file, sample_size)
    print(f"[OK] CallDecision 샘플 생성: {count}개")
    return output_file


def update_openai_config(openai_api_key: str) -> str:
    """OpenAI 설정 파일 업데이트 (LLM-as-Judge용)"""
    config_path = FUNCTIONCHAT_BENCH_PATH / "config" / "openai.cfg"
    original = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    config = {
        "api_type": "openai",
        "api_key": openai_api_key,
        "api_version": "gpt-4.1",  # GPT-4.1 judge
        "temperature": 0.0,
        "max_tokens": 256,
        "n": 1
    }
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print("[OK] OpenAI judge config 업데이트 완료")
    return original


def restore_openai_config(original_content: str):
    config_path = FUNCTIONCHAT_BENCH_PATH / "config" / "openai.cfg"
    if original_content:
        config_path.write_text(original_content, encoding="utf-8")
        print("[OK] OpenAI judge config 복원 완료")


def run_evaluation(eval_type, model, input_file, openrouter_api_key: str, base_url: str, system_prompt_path=None, tools_type=None):
    """단일 평가 실행"""
    cmd = [
        sys.executable,
        str(FUNCTIONCHAT_BENCH_PATH / "evaluate.py"),
        eval_type,
        "--input_path", str(input_file),
        "--temperature", str(TEMPERATURE),
        "--model", model,
        "--api_key", openrouter_api_key,
        "--base_url", base_url,
        "--is_batch", "False",
        "--reset", "True",
        "--num-threads", "1"
    ]
    
    if system_prompt_path:
        cmd.extend(["--system_prompt_path", str(system_prompt_path)])
    
    if tools_type:
        cmd.extend(["--tools_type", tools_type])
    
    print(f"\n{'='*80}")
    print(f"평가 실행: {eval_type} - {model}")
    print(f"입력 파일: {input_file}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(FUNCTIONCHAT_BENCH_PATH),
            check=True,
            capture_output=False
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ 평가 실패: {e}")
        return False


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="FunctionChat-Bench 퀵 테스트 (샘플링)")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help="카테고리별 샘플 수 (기본값: 2)",
    )
    parser.add_argument(
        "--models",
        default=",".join(TEST_MODELS),
        help="쉼표로 구분된 모델 리스트 (기본값: 5개 모델)",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("OPENROUTER_BASE_URL", DEFAULT_BASE_URL),
        help="OpenRouter base URL",
    )
    args = parser.parse_args()

    openrouter_api_key = require_env("OPENROUTER_API_KEY")
    openai_api_key = require_env("OPENAI_API_KEY")

    print("="*80)
    print("FunctionChat-Bench 퀵 테스트 (5개 모델)")
    print("="*80)
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    print("\n테스트 대상 모델:")
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")
    print()
    
    original_cfg = update_openai_config(openai_api_key)
    try:
        # 샘플 데이터 생성
        print("\n[Step 1] 샘플 데이터 생성 중...")
        sample_size = max(1, int(args.sample_size))
        dialog_sample = create_dialog_samples(sample_size)
        singlecall_sample = create_singlecall_samples(sample_size)
        calldecision_sample = create_calldecision_samples(sample_size)
    
    system_prompt_path = FUNCTIONCHAT_BENCH_PATH / "data" / "system_prompt.txt"
    
    # 각 모델별 평가 실행
    total_models = len(models)
    for idx, model in enumerate(models, 1):
        print("\n" + "#"*80)
        print(f"# [{idx}/{total_models}] 모델 평가: {model}")
        print("#"*80)
        
        print("\n  [1/3] Dialog 평가 실행 중...")
        run_evaluation("dialog", model, dialog_sample, openrouter_api_key, args.base_url, system_prompt_path)
        
        print("\n  [2/3] SingleCall 평가 실행 중...")
        run_evaluation("singlecall", model, singlecall_sample, openrouter_api_key, args.base_url, system_prompt_path, tools_type="all")
        
        print("\n  [3/3] CallDecision 평가 실행 중...")
        run_evaluation("common", model, calldecision_sample, openrouter_api_key, args.base_url)
        
        print(f"\n  [{model}] 완료!")
    
        # 엑셀 리포트 생성
        print("\n" + "="*80)
        print("[Final] 엑셀 리포트 생성 중...")
        print("="*80)
        subprocess.run([sys.executable, str(REPO_PATH / "generate_excel_report.py")], check=True)
        print("[OK] 엑셀 리포트 생성 완료")
    finally:
        restore_openai_config(original_cfg)
    
    print("\n" + "="*80)
    print("퀵 테스트 완료!")
    print("="*80)
    print(f"\n결과 파일 위치:")
    print(f"  - 모델 응답: {REPO_PATH / 'result'}")
    print(f"  - 평가 점수: {REPO_PATH / 'score'}")
    print(f"  - 엑셀 리포트: {REPO_PATH / 'reports'}")
    print(f"\n평가된 모델 수: {total_models}개")


if __name__ == "__main__":
    main()
