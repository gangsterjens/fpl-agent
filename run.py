from src.youtube import get_transcript as gt
from src.embedder.embedd_texts import embed_new_videos
from src.processing.extract_facts import extract_facts


if __name__ == "__main__":
    gt.fill_up_latest()
    embed_new_videos()
    extract_facts()
