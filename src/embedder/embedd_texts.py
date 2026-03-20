from langchain_community.vectorstores import SupabaseVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from supabase import create_client

from dotenv import load_dotenv
from src.db import supabase_client as sc
from datetime import datetime, timezone
import os
load_dotenv()
SUPABASE_URL = os.getenv('SB_URL')
SUPABASE_SERVICE_KEY = os.getenv('SB_API_KEY')


class VectorStore:
    def __init__(self, supabase_url: str = SUPABASE_URL, supabase_key: str = SUPABASE_SERVICE_KEY):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small")
        self.SUPABASE_URL = supabase_url
        self.SUPABASE_SERVICE_KEY = supabase_key

        self.supabase = create_client(
            self.SUPABASE_URL,
            self.SUPABASE_SERVICE_KEY
        )

        self.vectorstore = SupabaseVectorStore(
            client=self.supabase,
            embedding=self.embeddings,
            table_name="embedded_documents",
            query_name="match_embedded_documents",
        )


    def embed_text(self, doc: str, metadata: dict):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50,
        )

        docs = splitter.create_documents(
            texts=[doc],
            metadatas=[metadata],
        )

        self.vectorstore.add_documents(
            docs
        )

    def query(self, query_text: str, k=5, min_date='2025-08-01', max_date='2099-12-31'):
        query_embedding = self.embeddings.embed_query(query_text)
        response = self.supabase.rpc(
            "match_embedded_documents",
            {
                "query_embedding": query_embedding,
                "match_count": k,
                "min_published_at": min_date,
                "filter": {}
            }
        ).execute()
        return response.data

    def hybrid_query(self, query_text: str, k=5, min_date='2025-08-01', max_date='2099-12-31',
                     full_text_weight=1.0, semantic_weight=1.0, rrf_k=50):
        query_embedding = self.embeddings.embed_query(query_text)
        response = self.supabase.rpc(
            "hybrid_search_embedded_documents",
            {
                "query_text": query_text,
                "query_embedding": query_embedding,
                "match_count": k,
                "min_published_at": min_date,
                "max_published_at": max_date,
                "full_text_weight": full_text_weight,
                "semantic_weight": semantic_weight,
                "rrf_k": rrf_k,
            }
        ).execute()
        return response.data

def embed_new_videos():
    sb_client = sc.SupabaseClient(
        os.getenv('SB_API_KEY'),
        os.getenv('SB_URL')
    )

    videos = sb_client.get_data(
        'videos', where_statement=('has_vectors', False)
    )

    if not videos.data:
        print('No new videos to embed')
        return

    vector_store = VectorStore()

    for el in videos.data:
        transcript = sb_client.get_data(
            'transcripts', where_statement=('video_id', el['video_id'])
        )
        if len(transcript.data) < 1:
            print(f'No transcript for video_id: {el["video_id"]}')
            continue

        print(f'Processing video_id: {el["video_id"]}, title: {el["title"]}')
        video_id = el['video_id']
        text = transcript.data[0]['text']
        metadata = {
            'video_id': video_id,
            'channel_name': el['channel_name'],
            'title': el['title'],
            'description': el['description'],
            'published_at': el['published_at']
        }
        print(metadata)
        vector_store.embed_text(
            doc=text,
            metadata=metadata
        )

        sb_client.set_column_by_id(
            table_name="videos",
            row_id=video_id,
            column_name="has_vectors",
            value=True,
            id_column="video_id"
        )


if __name__ == "__main__":
    embed_new_videos()