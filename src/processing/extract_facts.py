import os
import time

import pandas as pd
from dotenv import load_dotenv

from src.db import supabase_client as sc
from src.fpl import fpl_api as fpl
from src.processing.llm import llm
from src.processing import prompts
from src.processing.json_parser import tekst2json

load_dotenv()


def _get_gw_cutoff() -> str:
    """Return the current GW deadline as an ISO date string."""
    try:
        start_gw, _ = fpl.get_between_gw()
        return pd.Timestamp(start_gw).isoformat()
    except Exception:
        return "2025-08-01"


def extract_facts() -> None:
    sb = sc.SupabaseClient(os.getenv('SB_API_KEY'), os.getenv('SB_URL'))
    gw_cutoff = _get_gw_cutoff()
    print(f'Only processing videos published after {gw_cutoff}')

    # Get videos published after the current GW deadline
    videos = sb.get_data('videos')
    if not videos.data:
        print('No videos found')
        return
    valid_video_ids = {
        row['video_id'] for row in videos.data
        if row.get('published_at', '') >= gw_cutoff
    }

    # Get all transcripts
    transcripts = sb.get_data('transcripts')
    if not transcripts.data:
        print('No transcripts found')
        return

    # Get video_ids that already have facts extracted
    existing_facts = sb.get_data('transcript_facts')
    existing_ids = {row['video_id'] for row in existing_facts.data} if existing_facts.data else set()

    # Filter to transcripts that have a recent video and don't yet have facts
    pending = [t for t in transcripts.data
               if t['video_id'] in valid_video_ids and t['video_id'] not in existing_ids]
    if not pending:
        print('All transcripts already have facts extracted')
        return

    print(f'Extracting facts for {len(pending)} transcripts')

    for el in pending:
        video_id = el['video_id']
        text = el['text']
        start_time = time.time()

        print(f'Processing video_id: {video_id}')

        prompt = prompts.EXTRACT_FACTS_PROMPT.format(transcript=text)
        raw_result = llm(
            prompt,
            system_prompt='You are a helpful assistant that only returns valid JSON as instructed.',
            reasoning_effort='low',
        )
        facts = tekst2json(raw_result)

        row = {
            'video_id': video_id,
            'overthoughts': facts.get('overthoughts', []),
            'players': facts.get('players', []),
        }

        sb.upsert_data(
            table_name='transcript_facts',
            data=row,
            unique_column='video_id',
            not_refresher=False,
        )

        elapsed = time.time() - start_time
        print(f'  Done in {elapsed:.1f}s — {len(facts.get("players", []))} players extracted')


if __name__ == '__main__':
    extract_facts()
