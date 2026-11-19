import argparse
import json
from pathlib import Path

from .desk import assess
from .review import review


def load_case(case_path, registry_path):
    case = json.loads(case_path.read_text(encoding='utf-8'))
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    return assess(case, registry)


def load_review(case_path, registry_path):
    case = json.loads(case_path.read_text(encoding='utf-8'))
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    return review(case, registry)


def main():
    parser = argparse.ArgumentParser(description='核对受理路径与所缺材料')
    parser.add_argument('action', nargs='?', default='assess', choices=['assess', 'review'])
    parser.add_argument('--case', type=Path, default=Path('fixtures/work.json'))
    parser.add_argument('--registry', type=Path, default=Path('fixtures/business.json'))
    args = parser.parse_args()
    try:
        if args.action == 'review':
            result = load_review(args.case, args.registry)
        else:
            result = load_case(args.case, args.registry)
    except (OSError, KeyError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
