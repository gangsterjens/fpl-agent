REFINE_TR_PROMPT = """
        Refine this text from a YouTube transcript.
        The youtube transcript is from podcast around the game Premier League Fantasy. 
         
 

        THE MOST IMPORTANT THING is to get the players name correct. Under is a list of the players first, second and webname from the official FPL API. Replace the mispelled name with the correct one. If you are not sure who it is, set (unsure):
        Example 1:
        'My favourite players right now is:
        Rya Burns, Sessi, Gabrielle, Tarosski, Semeno, Dai, Bruno, Harland, D Bravka, Rodon, and Rinders'

        you should transform to
        'My favourite players right now is:
        Raya, Burns, Senesi, Gabriel, Tarkwoski, Semeno , Diaye, Bruno Fernandez, Haaland, Dubrawka, Rodon, and Reijnders'.

        Here is the players that are eligible for the round, and thus the players that are relevant and spoken about. This is your guidelines and is your encyclopedia.
        JSON:
        {players}

        Here is the metadata from the videos 'About':
        {video_meta} The text you are to refine comes under in user input. 

        The task is:go through the full transcript and replace all clearly identifiable mis-spellings with the exact web_name from the API (and mark uncertain ones as (unsure)), doing this in a single pass
        You have permission to proceed for each name in replacing. If you are unsure, do not change the name, instead mark a * after their name.
        Only return the refined text. Not 'certainly here is the refined text' etc etc.. only the text that is refined
        Do not ask claryfing questions, just do the job. 

"""