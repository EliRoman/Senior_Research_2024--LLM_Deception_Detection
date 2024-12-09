
# !!!first install ollama in the terminal!!!
# pip install -U ollama (-U to update)

# next set up ollama in the terminal
# ollama serve (if not set up automatically)

## imports ##
import os
import ollama
#https://github.com/ollama/ollama-python
#https://github.com/ollama/ollama

# setup the client that will run model via Ollama
local_host='http://localhost:11434'
client = ollama.Client(host=local_host, timeout=120)
print(f"running Ollama client at {local_host}...")




# Inputs: name of model and location of transcripts folder
# For each transcript in the folder;
#   Generates a prompt
#   prompts ollama to rank perticipants in order of 'most likely to be in the deceptive role'
#   prints the response
# records the responses to a ranks.txt file
def ollama_rank(model_name='llama3.2', transcripts_folder='transcripts'):
    if not os.path.exists(transcripts_folder):
        print(f"Error: The folder '{transcripts_folder}' does not exist.")
        return
    
    # pull the model you wish to run from meta
    print(f"Pulling model: {model_name}")
    client.pull(model_name) #ollama pull <model_name>

    #create/open ranks.txt file to record upcoming responses
    with open(os.path.join(transcripts_folder, 'ranks.txt'), 'w') as output_file:
        
        # for every record in the given folder
        for transcript_file in os.listdir(transcripts_folder):
            
            # Skip the output file if found
            if transcript_file == 'ranks.txt':
                continue
            
            #confirm that the file path is valid
            file_path = os.path.join(transcripts_folder, transcript_file)
            if os.path.isfile(file_path) and transcript_file.endswith('.txt'):
                
                print(f"Processing file: {transcript_file}...")
                try:
                    #generate prompt and Players dictionary
                    prompt, Players = prompt_maker(file_path)
                    print(f"Generated prompt")
                    
                    #pass prompt and record response
                    response = ollama_response(model_name, prompt)
                    print(f"Model response: \n{response}\n")
                    
                    # record the response to the ranks file with player roles added
                    output_file.write(f"File: {transcript_file}\n{response}\n{Players}\n\n\n")
                    
                except Exception as e:
                    print(f"Error processing file {transcript_file}: {e}")
    print("Complete!")

# returns a dictionary of players and their roles from the given string
def parse_players(players_string):
    #print(f"Parsing last line:{players_string}")
    
    # Remove the "Players: [" and "]" from the ends of the string
    players_string = players_string.replace("Players: [", "").replace("]", "")
    
    # Split the string into list of individual player entries, remove quotes
    player_entries = [player.strip("\'") for player in players_string.split(", ")]
    #print(player_entries)
    ## make a dictionary of players ##
    players={}
    for player in player_entries:
        # Split at colon to get key-value pairs
        key, value = player.split(":")
        players[key] = value # Assign key value
            
    return players

# Print a sample parse
#print(parse_players("Players: ['Ryan Hodges:mafia', 'Mary Trujillo:town', 'Christopher Smith:town', 'Diana Pennington:town', 'Christina Rollins:town', 'Troy Thomas:town', 'Natalie Morris:mafia']"))

# Returns (as string) a prompt for the model based on info from the given file
def prompt_maker(file_location):

    # read data from file and save as local variable
    with open(file_location, 'r') as file:
        lines = file.readlines()
    
    # raise error if file is empty
    if not lines:
        raise ValueError(f"The file {file_location} is empty.")
    
    # Extract the list of players from the last line
    players_line = lines[-1].strip()
    if not players_line.startswith("Players:"): # if no players list, undo
        lines.append(players_line)
        raise ValueError(f"The last line of the file {file_location} does not contain the expected 'Players:' format.")
    else:
        # ToDo: Modify this to use dictionary instead of list
        players = parse_players(players_line)
        players_list = list( players.keys() )
        # save the last line in the file as a list of players
        #players = eval(players_line.split(': ')[1])
        print(f"Players extracted: {players_list}")
        
    
    # Save the rest of the file as the transcript
    transcript = ''.join(lines[:-1])
    print(f"Transcript extracted")

    # Define the main question and output format
    main_question = 'Rank the players in order of most likely to be in the deceptive role.'
    output_format = '''
    Please only answer in the following format:
    Session: session_number
    Rank:
    <Player Name>
    <Player Name>
    ...
    <Player Name>
    
    Actualy likely to be Mafia: <Player Names or 'none'>
    '''

    # Create and return the prompt
    prompt = f'''
    The game of Mafia is a social deduction game where players try to identify the members of the mafia among them. The names given are aliases and not the real player names.
    The following is a transcript from the first round of a particular session of Mafia.
    File: {os.path.basename(file_location)}
    Transcript:
    {transcript}
    The players are: {', '.join(players_list)}
    {main_question}
    {output_format}
    '''
    return prompt, players

# generate a sample prompt for demonstration purposes
def sample_prompt(transcripts_folder='transcripts', transcript_file='session_1.txt'):
    file_path = os.path.join(transcripts_folder, transcript_file)
    sample_prompt, Players = prompt_maker(file_path) #return promptand players dict
    print(f"--A sample prompt-- \n{sample_prompt}")
    print("---End of sample prompt---")
    print(f"Players: {Players}")
    return sample_prompt

# sample prompt usage:
#sample_prompt("transcripts_new",'session_1.txt')

#print a sample

# given a model name and a prompt 
# prompts the model and returns the response given
def ollama_response(model_name, prompt):
    
    # run the model, generate and record the response
    print(f"Prompting the model...")
    response = client.generate(model_name, prompt)
    print(f"Model response complete.")
    
    #return the model's response
    return response['response']

# sample usage:
# ollama_response('llama3.2','What is a double rainbow? Answer in one sentance, please.')


# to run the code
#ollama_rank()

# alternatively
#ollama_rank("mistral", "transcripts_a")
#ollama_rank("qwq", "transcripts_b")
#ollama_rank("dolphin-llama3", "transcripts_c")
#ollama_rank("llama3.2", "transcripts_z")
#ollama_rank("llama3.2", "transcripts_new")