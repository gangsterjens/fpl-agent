from supabase import create_client, Client

class SupabaseClient:
    def __init__(self, key, url):
        self.client = create_client(url, key)

    def insert_data(self, table_name, data):
        self.client.table(table_name).insert(data).execute()

    def get_data(self, table_name, where_statement=None):
        if where_statement:
            return self.client.table(table_name).select("*").eq(where_statement).execute()
        else:
            return self.client.table(table_name).select("*").execute()
        return self.client.table(table_name).select("*").execute()
    
    def upsert_data(self, table_name: str, data: dict, unique_column: str = None):
        self.client.table(table_name).upsert(
            data,
            on_conflict=unique_column,
            ignore_duplicates=True,   # translates to DO NOTHING
            ).execute()