# GetChessACPL
Function that retuns (whites acpl, blacks acpl, cpl per move for white, cpl for move for black) given an input PGN.
# Set up the program:
First, change the 'stockfish_path' to the path of stockfish that you can download at https://stockfishchess.org

# Use of main function- getascpl(): 
Input of this function is a PGN, and the time per move an engine spends time thinking(deault is 0.5), and the maximum centipawn loss that can occur (lichess uses 1000 and so will this program by default)

Output -> (WhitesACPL, BlacksACPL, list of CPL per move for white, list of CPL peer move for black) 

To test this out, you can try adding print(asyncio.run(getacpl(ExamplePGN)))

# Use of other functions:
This program contains 3 other functions that the main function (getacpl()) relies on.

The first one, analyze_position takes the inputs of a (FEN, time_limt- optional as default is 0.5 and stockfish path that is default to the path you entered)
This returns the best move and the eval. 

phrase_stockfish_score takes in the inputs of (engines response, maxeval) , takes in stockfishes responses and gives it an eval value. Mates are set to be 
slightly above the maximum eval that by default is 2500

getevals() uses the previous two functions to create a list of evals in the perspective of white and returns the list. 

