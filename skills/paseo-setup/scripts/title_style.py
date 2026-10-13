#!/usr/bin/env python3
"""Paseo 자동 제목을 한국어 짧은 이름으로 바꾸는 지시문을 repo의 paseo.json에 넣는다.

Paseo는 워크스페이스 제목을 만들 때 repo 루트 paseo.json의
metadataGeneration.title.instructions를 디스크에서 읽는다(전역 설정 없음).

  title_style.py <repo>...            추적되지 않는 paseo.json만 로컬 전용으로 생성·갱신
  title_style.py --tracked <repo>...  Git이 추적하는 paseo.json도 작업 트리에서 수정(커밋은 하지 않음)
"""
import json
import subprocess
import sys
from pathlib import Path

INSTRUCTIONS = (
    "한국어로 쓴 10자 이내(공백 포함)의 짧은 작업 이름. 10자를 넘으면 단어를 줄인다. "
    "핵심 대상과 작업만 남기고 명사형으로 끝낸다. 문장부호·따옴표·이모지는 쓰지 않는다. "
    "PR·이슈 번호나 고유 명칭은 작업을 구분하는 데 꼭 필요할 때만 넣는다. "
    '예: "현금영수증 취소", "KPI 화면 분석", "로그인 복구".'
)


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def apply(repo, include_tracked):
    if git(repo, "rev-parse", "--show-toplevel").returncode != 0:
        return "SKIP    Git repo가 아님(Paseo가 지시문을 읽지 않음)"
    config = repo / "paseo.json"
    tracked = git(repo, "ls-files", "--error-unmatch", "paseo.json").returncode == 0
    in_history = bool(git(repo, "log", "--all", "-1", "--format=%h", "--", "paseo.json").stdout.strip())
    if (tracked or in_history) and not include_tracked:
        return "TRACKED 팀이 공유하는 파일 — 커밋 여부를 정한 뒤 --tracked로 적용"

    data = json.loads(config.read_text()) if config.exists() else {}
    fresh = "metadataGeneration" not in data
    title = data.setdefault("metadataGeneration", {}).setdefault("title", {})
    if title.get("instructions") == INSTRUCTIONS:
        return "OK      이미 적용됨"
    title["instructions"] = INSTRUCTIONS
    rendered = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    text = config.read_text().rstrip() if config.exists() else ""
    if fresh and text.endswith("}"):
        # 기존 서식을 건드리지 않도록 마지막 중괄호 앞에 블록만 끼워 넣는다.
        block = json.dumps({"metadataGeneration": data["metadataGeneration"]}, indent=2, ensure_ascii=False)
        patched = text[:-1].rstrip() + ",\n" + block[2:-2] + "\n}\n"
        try:
            if json.loads(patched) == data:
                rendered = patched
        except json.JSONDecodeError:
            pass
    config.write_text(rendered)
    if tracked or in_history:
        return "EDITED  작업 트리만 수정 — 커밋 필요"

    common = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip())
    exclude = common / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    lines = exclude.read_text().splitlines() if exclude.exists() else []
    if "/paseo.json" not in lines:
        exclude.write_text("\n".join([*lines, "/paseo.json"]) + "\n")
    return "LOCAL   로컬 전용으로 적용(.git/info/exclude)"


def main(argv):
    include_tracked = "--tracked" in argv
    repos = [Path(arg).expanduser().resolve() for arg in argv if arg != "--tracked"]
    if not repos:
        print(__doc__)
        return 2
    for repo in repos:
        print(f"{apply(repo, include_tracked)}  {repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
