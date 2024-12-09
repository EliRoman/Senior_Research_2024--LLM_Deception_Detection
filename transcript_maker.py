import os
import pandas as pd
import random
import string

dataset_folder = './dataset'
transcripts_folder = './transcripts'
os.makedirs(transcripts_folder, exist_ok=True)

# Generate a dictionary mapping unique player names to aliases.
def generate_names(session_data):
    
    # Extract all unique names from rows where type is 'text' or 'vote'
    unique_names = set()
    for _, row in session_data.iterrows():
        if row['type'] in {'text', 'vote'}:
            try:
                player_name = row['contents'].split(': ')[0]
                unique_names.add(player_name)
            except IndexError:
                pass  # Skip rows with unexpected format

    #create list of randomly sorted letters
    available_letters = list(string.ascii_uppercase)
    random.shuffle(available_letters)
    
    # Create aliases in the format "Player_{letter}" and assign them to each unique name
    aliases = {}
    for name in unique_names:
        if available_letters:
            aliases[name] = f"Player_{available_letters.pop()}"
        else:
            raise ValueError("Not enough unique letters to assign aliases to all players.")

    return aliases

#Returns 2 dictionaries;
#   Player names with their roles
#   Player aliases with their role
#Given 
#   aliases dictionary and
#   node.csv path
def find_roles(aliases, node_path):
    node_data = pd.read_csv(node_path) # read node.csv
    # List of players that have the 'mafioso' role
    mafia_list = node_data[node_data['type']=='mafioso']['property1'].to_list()
    # List of aliases of players that have the 'mafioso' role
    anonymized_mafia_list = [ aliases[name] for name in mafia_list if name in aliases ]

    # Dictionary of player names with their roles
    player_roles = {name:("mafia" if name in mafia_list else "town") for name in aliases}
    # Dictionary of player aliases with their roles
    anonymized_player_roles = {aliases[name]: role for name, role in player_roles.items() if name in aliases}

    return player_roles, anonymized_player_roles

def process_transmissions(dataset_folder, transcripts_folder):
    session_num = 1  # Start numbering transcripts
    
    # Iterate over each subdirectory in the dataset folder
    for root, dirs, files in os.walk(dataset_folder):
        if 'info.csv' in files:
            csv_path = os.path.join(root, 'info.csv')
            print('info.csv found at ' + csv_path)
            data = pd.read_csv(csv_path)
            
            # Ensure data is sorted by creation_time to process chronologically
            data = data.sort_values(by='creation_time')
            
            # Filter rows where 'contents' contains the phase change markers
            daytime_rows = data[data['contents'].str.contains("Phase Change to Daytime", na=False)]
            nighttime_rows = data[data['contents'].str.contains("Phase Change to Nighttime", na=False)]
            
            # If both daytime and nighttime transitions are found
            if not daytime_rows.empty and not nighttime_rows.empty:
                
                # Get the index of the first "Phase Change to Daytime" row
                daytime_start = daytime_rows.index[0]
                print('  start time: ', daytime_start)
                
                # Try to find the next "Phase Change to Nighttime" after daytime_start
                nighttime_candidates = nighttime_rows[nighttime_rows.index > daytime_start]
                if not nighttime_candidates.empty:
                    
                    # Get the first nighttime index after the daytime_start
                    nighttime_end = nighttime_candidates.index[0]
                    print('  end time: ', nighttime_end)
                    
                    # Select rows within this daytime-to-nighttime range
                    session_data = data.loc[daytime_start:nighttime_end]
                    
                    # Generate aliases for players in this session
                    aliases = generate_names(session_data)

                    # Prepare list of lines for both transcripts (regular and anonymized)
                    transcript_lines = []
                    anonymized_lines = []
                    
                    ## transcribing data to formated strings ##
                    # iterate through data contents
                    for _, row in session_data.iterrows():
                        
                        # every vote is saved as "{player_voting} votes for {player_voted}!"
                        if row['type'] == 'vote':
                            try:
                                player_voting, player_voted = row['contents'].split(': ')
                                formatted_content = f"{player_voting} votes for {player_voted}!"
                                anonymized_content = f"{aliases.get(player_voting, 'silent_player')} votes for {aliases.get(player_voted, 'silent_player')}!"
                            except ValueError:
                                formatted_content = anonymized_content = row['contents']
                        
                        # every chat message is saved as "{player}: {message}"
                        elif row['type'] == 'text':
                            try:
                                player, message = row['contents'].split(': ', 1)
                                formatted_content = f"{player}: {message}"
                                anonymized_content = f"{aliases.get(player, player)}: {message}"
                            except ValueError:
                                formatted_content = anonymized_content = row['contents']
                        
                        # Use original content for other types
                        else:
                            formatted_content = anonymized_content = row['contents']
                        
                        # save formatted content to list of lines. (for txt transcript later)
                        transcript_lines.append(formatted_content)
                        anonymized_lines.append(anonymized_content)
                    
                    # Player dictionary with names and roles
                    mafia_names, mafia_aliases = find_roles(aliases, os.path.join(root, 'node.csv'))

                    # Join all lines into single transcript texts and add the list of players at the bottom
                    transcript = '\n'.join(transcript_lines) + f'\nPlayers: {[ f"{name}:{role}" for name, role in mafia_names.items() ]}'
                    anonymized_transcript = '\n'.join(anonymized_lines) + f'\nPlayers: {[ f"{name}:{role}" for name, role in mafia_aliases.items() ]}'
                    
                    # Write the regular transcript
                    transcript_path = os.path.join(transcripts_folder, f'session_{session_num}.txt')
                    with open(transcript_path, 'w') as f:
                        f.write(transcript)
                    print(f'Transcript created: session_{session_num}.txt')
                    
                    # Write the anonymized transcript
                    anonymized_transcript_path = os.path.join(transcripts_folder, f'session_{session_num}_anonymized.txt')
                    with open(anonymized_transcript_path, 'w') as f:
                        f.write(anonymized_transcript)
                    print(f'Anonymized transcript created: session_{session_num}_anonymized.txt')
                    
                    # Increment session number for the next file
                    session_num += 1
                else:
                    print(f"No 'Nighttime' phase found after 'Daytime' in session {session_num}")
                
            else:
                print(f"Skipping session {session_num}: incomplete daytime/nighttime markers")

    print(f"Process complete! See {transcripts_folder} for results.")

process_transmissions(dataset_folder, transcripts_folder)