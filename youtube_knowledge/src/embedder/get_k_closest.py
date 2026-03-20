from . import embedd_texts as et
import os

#from src import supabase_client as sc

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SB_URL')
SUPABASE_SERVICE_KEY = os.getenv('SB_API_KEY')

print(type(SUPABASE_URL), type(SUPABASE_SERVICE_KEY))


vector_store = et.VectorStore(supabase_key=SUPABASE_SERVICE_KEY, supabase_url=SUPABASE_URL)



result = vector_store.query(
    query_text=input('Enter your query: '), min_date='2026-01-01', k=50)

for res in result:
    #print(res['metadata'])
    print('-----------content--------')
    print(res['content']) 
    print('-------------------')