"""Run from backend: python -m app.agent_cli 'What does PMDA publish?'"""
import argparse
import json
from app.agent_harness import investigate


def main():
    parser = argparse.ArgumentParser(description='Bounded local evidence investigation; no answer synthesis')
    parser.add_argument('question')
    args = parser.parse_args()
    print(json.dumps(investigate(args.question), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
