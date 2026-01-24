#!/usr/bin/env python3
"""
FunctionChat-Bench 평가 스크립트 (OpenRouter)

- 5개 모델을 OpenRouter(OpenAI-compatible)로 평가합니다.
- FunctionChat-Bench의 LLM-as-Judge(OpenAI) 평가를 수행합니다.
- 평가 산출물은 프로젝트 루트에 다음 구조로 저장됩니다.
  - result/  (모델 응답)
  - score/   (judge 결과/TSV)
  - reports/ (엑셀 리포트)
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import argparse
from dotenv import load_dotenv

# 환경 변수 로드 (파일이 없어도 계속 진행)
try:
    load_dotenv()
except Exception:
    pass  # .env 파일이 없거나 권한 문제가 있어도 계속 진행

DEFAULT_MODELS = [
    "meta-llama/llama-3.3-70b-instruct",
    "mistralai/mistral-small-3.2-24b-instruct",
    "qwen/qwen3-32b",
    "qwen/qwen3-14b",
    "qwen/qwen3-next-80b-a3b-instruct",
]

# 평가 타입 및 설정
EVALUATION_TYPES = {
    "dialog": {
        "input_path": "FunctionChat-Bench/data/FunctionChat-Dialog.jsonl",
        "system_prompt_path": "FunctionChat-Bench/data/system_prompt.txt",
        "tools_type": None
    },
    "singlecall": {
        "input_path": "FunctionChat-Bench/data/FunctionChat-Singlecall.jsonl",
        "system_prompt_path": "FunctionChat-Bench/data/system_prompt.txt",
        "tools_type": "all"  # all, exact, 4_random, 4_close, 8_random, 8_close
    },
    # FunctionChat-CallDecision은 FunctionChat-Bench CLI에서 `common` 옵션으로 실행합니다.
    "common": {
        "input_path": "FunctionChat-Bench/data/FunctionChat-CallDecision.jsonl",
        "system_prompt_path": None,
        "tools_type": None
    }
}

# 평가 설정
TEMPERATURE = 0.0
REPO_PATH = Path(__file__).parent.absolute()
FUNCTIONCHAT_BENCH_PATH = REPO_PATH / "FunctionChat-Bench"


def require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise SystemExit(
            f"[ERROR] 환경 변수 `{name}` 이(가) 없습니다. "
            f"프로젝트 루트에 `.env`를 생성하거나 export로 설정하세요."
        )
    return val


def update_openai_config(openai_api_key: str) -> str:
    """OpenAI 설정 파일 업데이트 (LLM-as-Judge용). 기존 내용을 반환(복원용)."""
    config_path = FUNCTIONCHAT_BENCH_PATH / "config" / "openai.cfg"
    original = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    config = {
        "api_type": "openai",
        "api_key": openai_api_key,
        "api_version": "gpt-4o-2024-08-06",  # 최신 GPT-4 모델 사용
        "temperature": 0.0,
        "max_tokens": 4096,
        "n": 3
    }
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"[OK] OpenAI judge config 업데이트: {config_path}")
    return original


def restore_openai_config(original_content: str):
    config_path = FUNCTIONCHAT_BENCH_PATH / "config" / "openai.cfg"
    if original_content:
        config_path.write_text(original_content, encoding="utf-8")
        print("[OK] OpenAI judge config 복원 완료")


def run_evaluation(eval_type, model, openrouter_api_key: str, base_url: str, tools_type=None):
    """단일 평가 실행"""
    eval_config = EVALUATION_TYPES[eval_type]
    
    cmd = [
        sys.executable,
        str(FUNCTIONCHAT_BENCH_PATH / "evaluate.py"),
        eval_type,
        "--input_path", str(REPO_PATH / eval_config["input_path"]),
        "--temperature", str(TEMPERATURE),
        "--model", model,
        "--api_key", openrouter_api_key,
        "--base_url", base_url,
        "--is_batch", "False"
    ]
    
    if eval_config["system_prompt_path"]:
        cmd.extend([
            "--system_prompt_path",
            str(REPO_PATH / eval_config["system_prompt_path"])
        ])
    
    if tools_type:
        cmd.extend(["--tools_type", tools_type])
    
    print(f"\n{'='*80}\n평가 실행: {eval_type} - {model}\n{'='*80}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(FUNCTIONCHAT_BENCH_PATH),
            check=True,
            capture_output=False
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 평가 실패: {e}")
        return False


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="FunctionChat-Bench 평가 실행 (OpenRouter)")
    parser.add_argument(
        "--models",
        default=",".join(DEFAULT_MODELS),
        help="쉼표로 구분된 모델 리스트. 기본값: 5개 모델",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        help="OpenRouter base URL (기본값: https://openrouter.ai/api/v1)",
    )
    parser.add_argument(
        "--skip-excel",
        action="store_true",
        help="평가만 수행하고 엑셀 리포트 생성을 건너뜁니다.",
    )
    args = parser.parse_args()

    openrouter_api_key = require_env("OPENROUTER_API_KEY")
    openai_api_key = require_env("OPENAI_API_KEY")

    print("=" * 80)
    print("FunctionChat-Bench 평가 시작 (OpenRouter)")
    print("=" * 80)

    original_cfg = update_openai_config(openai_api_key)
    try:
        models = [m.strip() for m in args.models.split(",") if m.strip()]
        for model in models:
            print("\n" + "#" * 80)
            print(f"모델 평가: {model}")
            print("#" * 80)

            print("\n[1/3] Dialog")
            run_evaluation("dialog", model, openrouter_api_key, args.base_url)

            print("\n[2/3] SingleCall (tools_type=all)")
            run_evaluation("singlecall", model, openrouter_api_key, args.base_url, tools_type="all")

            print("\n[3/3] CallDecision (common)")
            run_evaluation("common", model, openrouter_api_key, args.base_url)

        if not args.skip_excel:
            print("\n" + "=" * 80)
            print("엑셀 리포트 생성")
            print("=" * 80)
            subprocess.run([sys.executable, str(REPO_PATH / "generate_excel_report.py")], check=True)
    finally:
        restore_openai_config(original_cfg)

    print("\n" + "=" * 80)
    print("완료")
    print("=" * 80)


if __name__ == "__main__":
    main()
