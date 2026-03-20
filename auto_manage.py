"""
Autonomous FPL team management — cron-ready entry point.

Usage:
    python auto_manage.py              # full pipeline + agent
    python auto_manage.py --skip-pipeline  # agent only

Cron example (Friday 8 AM before Saturday deadline):
    0 8 * * 5 cd /path/to/fpl-agent && .venv/bin/python auto_manage.py >> logs/cron.log 2>&1
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv()


def setup_logging() -> logging.Logger:
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f'auto_manage_{datetime.now().strftime("%Y-%m-%d")}.log'

    logger = logging.getLogger('auto_manage')
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def run_pipeline(logger: logging.Logger) -> None:
    logger.info('Running data pipeline...')

    from src.youtube import get_transcript as gt
    from src.embedder.embedd_texts import embed_new_videos
    from src.processing.extract_facts import extract_facts

    logger.info('Step 1/3: Fetching latest transcripts')
    gt.fill_up_latest()

    logger.info('Step 2/3: Embedding new videos')
    embed_new_videos()

    logger.info('Step 3/3: Extracting player facts')
    extract_facts()

    logger.info('Pipeline complete.')


def run_agent(logger: logging.Logger) -> None:
    logger.info('Starting autonomous FPL agent...')

    from src.agents.orchestrator import build_autonomous_graph

    graph = build_autonomous_graph()

    prompt = (
        "Manage my FPL team for the upcoming gameweek. "
        "Review my squad, check player form and fixtures, consult podcast recommendations, "
        "make transfers if beneficial, and set the optimal lineup with captain."
    )

    result = graph.invoke({'messages': [HumanMessage(content=prompt)]})

    # Log all messages (tool calls and responses)
    for msg in result.get('messages', []):
        role = msg.__class__.__name__
        content = getattr(msg, 'content', '')
        if content:
            logger.info(f'[{role}] {content[:2000]}')

        # Log tool calls
        for tc in getattr(msg, 'tool_calls', []):
            logger.info(f'[ToolCall] {tc["name"]}({tc.get("args", {})})')

    # Final summary is the last AI message
    messages = result.get('messages', [])
    if messages:
        final = messages[-1]
        logger.info(f'\n{"="*60}\nFINAL SUMMARY\n{"="*60}\n{getattr(final, "content", "")}')


def main():
    parser = argparse.ArgumentParser(description='Autonomous FPL team manager')
    parser.add_argument('--skip-pipeline', action='store_true',
                        help='Skip the data pipeline and run agent only')
    args = parser.parse_args()

    logger = setup_logging()
    logger.info('='*60)
    logger.info('Auto-manage started')

    try:
        if not args.skip_pipeline:
            run_pipeline(logger)
        else:
            logger.info('Skipping pipeline (--skip-pipeline)')

        run_agent(logger)
    except Exception:
        logger.exception('Auto-manage failed')
        sys.exit(1)

    logger.info('Auto-manage completed successfully.')


if __name__ == '__main__':
    main()
