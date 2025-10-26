from supabase import create_client, Client

class SupabaseClient:
    def __init__(self, key, url):
        self.client = create_client(url, key)

    def insert_data(self, table_name, data):
        self.client.table(table_name).insert(data).execute()

    def get_data(self, table_name, where_statement: tuple = None):
        query = self.client.table(table_name).select("*")

        if where_statement:
            # If a single tuple is passed, wrap it in a list
            if isinstance(where_statement, tuple):
                where_statement = [where_statement]

            # Loop through each (column, value) pair
            for col, value in where_statement:
                query = query.eq(col, value)

        return query.execute()
    
    def upsert_data(self, table_name: str, data: dict, unique_column: str = None):
        self.client.table(table_name).upsert(
            data,
            on_conflict=unique_column,
            ignore_duplicates=True,  
            ).execute()