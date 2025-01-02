#parses data from a ranks.txt file

import re # regular expressions library
import os # for file handling
import pandas as pd # for dataset handling
from pprint import pprint # Helps debug dictionaries by displaying them nicely
transcripts_folder = 'transcripts_new'

# returns a players dictionary made from the given players string
def parse_players(players_string):
    
    # Remove the "{" and "}" from the ends of the string
    players_string = players_string.replace("{", "").replace("}", "")
    
    # Split the string into list of individual player entries,
    player_entries = players_string.split(", ")
    #pprint(player_entries) # debugging: print player_entries list

    ## make a dictionary of players ##
    players={}
    for player in player_entries:
        # Split at colon to get key-value pairs
        key, value = player.split(": ")
        # add key & value to players dictionary (w/ quotes removed)
        players[key.strip("\'")] = value.strip("\'")
            
    return players

# given names and ranked list, returns avg percentile of given names
def average_percentile_rank(mafia_list, players):
    #print(f"searching for {mafia_list} in {players}") # debugging
    
    # Find the rank of each mafia (their index in the players list)
    mafia_ranks = [float(players.index(mafioso)) for mafioso in mafia_list]

    # Calculate the percentile of each rank
    total_players = float(len(players))
    mafia_percentiles = [(rank / total_players) * 100 for rank in mafia_ranks]
    
    # Calculate the average of the mafia_percentiles
    average_mafia_percentile = sum(mafia_percentiles) / len(mafia_percentiles)
    
    # Return the average percentile rank of the mafia members
    return average_mafia_percentile

# given file path, return dictionary with file info
def read_ranks_file(file_path):

    #record location of ranks file given file path
    ranks_location = os.path.join(file_path, 'ranks.txt')

    # Check if the 'ranks.txt' file exists in the specified location
    if os.path.isfile(ranks_location):
        # Read the contents of the file into a string variable
        with open(ranks_location, "r") as f:
            contents = f.read()
    else:
        print(f"Error: 'ranks.txt' file not found in {file_path}")
        return None
    
    # Split the contents into list of individual blocks; use tripple new lines as delimiters
    blocks = re.split("\n\n\n", contents)

    #pprint(blocks[0]) #debugging: print first block as a sample
    
    # Initialize an empty dictionary to store the dictionaries for each block
    sessions = {}
    
    # Iterate over each block and extract the relevant information
    for block in blocks[:-1]:

        # Split the block into individual lines using new line characters as delimiters
        lines = block.split("\n")

        #debugging: print the contents of the current block
        #print("Block: ",end='') 
        #pprint(block)

        '''
        This try catch statement will attempt to break the block string into multiple varaibles.
        If the text found is not exactly as expected it will throw an error.
        If that happens a message will be shown and the block will not be recorded
        and this session will be marked
        '''
        try:
            # Extract the file name from the first line
            file_name = re.search("File:\s*(\S+)", lines[0]).group(1).strip(".txt")

            #print(f"parsing file:{file_name}...",end="")
            #pprint(f"contents: \n{lines}")
            
            # Extract the session number from the second line
            session = int(re.search(r'\d+', lines[1]).group(0))
            #session = re.search("Session:\s*(\S+)", lines[1]).group(1)
            #print(session,end=', ')
            
            # Create a dictionary to store the information for this block
            dictionary = {"file_name": file_name, "session": session}

            # record true if aliases where used for names at prompt time
            dictionary["names_changed"] = "anonymized" in file_name
            
            # Extract the list of players from the last line
            players_line = lines[-1].strip()
            players = parse_players(players_line) #re.search("\[(.*?)\]", players_line).group(1)
            #dictionary["Players"] = players #{player: role for player, role in zip(players, ["town" if i % 2 == 0 else "mafia" for i in range(len(players))])}
            
            #mafia list
            mafia_list = [name for name, role in players.items() if role == 'mafia']
            dictionary["mafia"] = mafia_list
            
            ### Extract the rank information from the block ###
            ranks = []
            n=0
            for name in players:
                # find first mention of name. 
                if re.search(r'\b' + re.escape(name) + r'\b', block):  # \b ensures whole word matching
                    ranks.insert(n, name) # add name to the list in the correct position
                    n+=1
            
            #Sort ranks dictionary
            #ranks = {k: v for k, v in sorted(ranks.items(), key=lambda item: item[1])}

            # save ranks to dictionary.
            dictionary["ranks"] = ranks

            #debugging: print the contents of the ranks list
            #print("Ranks: ",end='')
            #print(ranks)
            
            #find average percentile rank of the mafia and save to dictionary
            dictionary['avg_mafia_rank']= average_percentile_rank(mafia_list,ranks)
            
            # Add this files dictionary to the dictionary of sessions
            sessions[file_name]=dictionary

            #print(f"parsed:{file_name}",end=". ") #debugging
        except Exception as e:
            print(f"Could not parse this block: {str(e)}")
            pprint(block)
            
        
    return {k: v for k, v in sorted(sessions.items(), key=lambda item: item[1]['session'])} # return session sorted by session num
"---"


# run the code
parsed_content = read_ranks_file(transcripts_folder)
pprint(parsed_content)

#pandas
#ranks_df = pd.DataFrame.from_dict(parsed_content, orient='index')
#ranks_df.set_index(['session','file_name']).sort_values(by='session')
