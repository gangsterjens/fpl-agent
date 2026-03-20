REFINE_TR_PROMPT = """
        Refine this text from a YouTube transcript.
        The youtube transcript is from podcast around the game Premier League Fantasy. 
         
 

        THE MOST IMPORTANT THING is to get the players name correct and their id if you are confident it is them. Under is a list of the players first, second and webname from the official FPL API. Replace the mispelled name with the correct one. If you are not sure who it is, within ID set (*) if sure set name(<id>):
        Example 1:
        'My favourite players right now is:
        Rya Burns, Sessi, Gabrielle, Tarosski, Semeno, Dai, Bruno, Harland, D Bravka, Rodon, and Rinders'

        you should transform to correctname(id)
        'My favourite players right now is:
        Raya(4), Burn (528), Senesi (124), Gabriel (4), Tarkwoski(317), Semenyo (134) , Ndiaye (325), B.Fernandez (500), Haaland (476), Dubrawka (114), Rodon (385), and Reijnders(473)'.
 
        Here is the players that are eligible for the round, and thus the players that are relevant and spoken about. This is your guidelines and is your encyclopedia.
        JSON:
        {players}

        Here is the metadata from the videos 'About':
        {video_meta} The text you are to refine comes under in user input. 

        Some often misheard by the transcripter on YT:
        Dai = Ndiaye
        Creepy Jr = Kroupi Jr
        Anderson = Andersen (on Crystal Palace)

        The task is the following: go through the full transcript and replace all clearly identifiable mis-spellings with the exact web_name from the API (and mark uncertain ones as (unsure)), doing this in a single pass
        You have permission to proceed for each name in replacing. If you are unsure, do not change the name, instead mark a * after their name.
        Only return the refined text. Not 'certainly here is the refined text' etc etc.. only the text that is refined
        Do not ask claryfing questions, just do the job.  Do not return the metadata. Only the transcript. Also, dont return any transcripts-data like [music] [applause]. Only whats been said. 

"""


JSON_SUMMARY = """
    Summarize this text as a json, with the following json structure 
    {{
    'type': <a short title or keywords of what the podcast is about>
    'players:
        {{
        name: <player name>, please match the playername with the players web_name from the given json.
        decision: see instructions below for the scale of decision,
        summary: <summary explaining why the decision. ,
        'citation': <if there is a clear sitation of the decision, argument etc, re-cite it here'. If needed, you can provide full phrase of more than one sentences>,
        }}
    'summary': <100-500 word summary of the podcast'>,
    'other': 'other important info, like if they are choosing to save their transfer, using wildcard, bench boost or trippel captain.
    }} 
    the text is a transcript from a youtube fpl podcast. and the goal of the json is to create a knowledge base from the podcasts. Do only return the json, nothing else.


    The instructions for the 'decision' key:

    Tier	Label	        Meaning
    1	    must_have	    Essential pick, cornerstone player
    2	    strong_buy	    Very good option, in form or good fixtures
    3	    hold	        Keep if owned, not worth a transfer either way
    4	    watchlist	    Not for now, but worth monitoring
    5	    rotation_risk	Could be dropped or rotated soon
    6	    sell_or_avoid	Negative recommendation — either sell if owned, or avoid buying
    7	    undecided	    Conflicting, unclear recommendation or not enough info

    DO NOT make things up, and do not conclude if not information is provided, then choose undecided. You will be punished if you are to confident

    The transcript:
    <transcript>
    {transcript}
    </transcript>

"""


