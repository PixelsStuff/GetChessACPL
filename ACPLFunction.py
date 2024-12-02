
import chess
import chess.engine
import time
import chess.pgn
import io
import re

#SETTINGS#
stockfish_path = '/Users/[yourusername]]/engines/stockfish' #Change this to your own stockfish path
Logging = False 

ExamplePGN = '''
[Event "Live Chess"]
[Site "Chess.com"]
[Date "2024.11.26"]
[Round "-"]
[White "Wins"]
[Black "Abandonad"]
[Result "1-0"]
[Timezone "UTC"]
[ECO "A13"]
[ECOUrl "https://www.chess.com/openings/English-Opening-Agincourt-Defense-2.Nf3"]
[UTCDate "2024.11.26"]
[UTCTime "18:57:16"]
[WhiteElo "1982"]
[BlackElo "1979"]
[TimeControl "60"]
[Termination "Wins won on time"]
[StartTime "18:57:16"]
[EndDate "2024.11.26"]
[EndTime "18:59:27"]

1. Nf3 e6 2. c4 Ne7 $6 3. d4 b6 $6 4. Nc3 Bb7 $6 5. e4 d5 $2 6. e5 $2 Nbc6 7. cxd5 Nxd5
8. Bb5 a6 9. Bd3 Qd7 $6 10. O-O O-O-O 11. a4 $2 Kb8 $6 12. Rb1 $2 f6 $6 13. Bd2 $6 fxe5 $2
14. Nxe5 $4 Nxe5 15. dxe5 Qc6 $9 16. Be4 $6 Qc4 $9 17. Nxd5 $4 Qxe4 $1 18. Ne3 Bc5 19.
Qe2 Bxe3 20. fxe3 Rd5 $6 21. Bc3 Rhd8 $9 22. Rf2 $4 Rd3 $9 23. Rbf1 Rxe3 24. Qd2 $2
Rxd2 25. Rxd2 Rd3 26. Rdf2 h5 27. h3 h4 28. Rf3 Rxf3 29. Rxf3 Qe2 30. Rf2 Qe3
31. Kf1 g5 32. Rf8+ Ka7 33. Rf3 1-0'''

def analyze_position(fen: str, time_limit=0.5 ,stockfish_path=stockfish_path):
    """
    Analyzes a chess position using Stockfish.

    Args:
        fen (str): The FEN string representing the board position
        time_limit (float): Time in seconds for Stockfish to analyze the position. I set this to 1 second by default.
        stockfish_path (str): Path to the Stockfish - should be done automatically from this file
        

    Returns:
        tuple: A tuple containing the evaluation (`chess.engine.PovScore`) and the best move (`chess.Move`).
    """
    # Set up the board from the FEN string
    board = chess.Board(fen)
    
    # Start Stockfish
    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
        try:
            # Analyze the position
            result = engine.analyse(board, chess.engine.Limit(time=time_limit))
            # Extract evaluation and best move
            evaluation = result['score']
            best_move = result['pv'][0]
            return evaluation, best_move
        except Exception as e:
            if Logging:
                print(e)
            return None
def phrase_stockfish_score(response,maxeval = 2500):
    """
    Extracts the score and color from a Stockfish response.
    
    Args:
        response (str): The Stockfish response string, e.g., "PovScore(Cp(+45), WHITE)".
    
    Returns:
        tuple: A tuple containing:
            - score (int): The numerical evaluation score.                  
            - color (str): The color ("WHITE" or "BLACK").
    """
    # Define the regex pattern
    pattern = r"PovScore\(Cp\(([-+]?\d+)\), (WHITE|BLACK)\)"
    pattern2 = r"PovScore\(Mate\(([-+]?\d+)\), (WHITE|BLACK)\)"
    
    # Perform regex search
    match = re.search(pattern, response)
    match2 = re.search(pattern2, response)
    if match:
        score = int(match.group(1))  # First capture group is the score
        color = match.group(2)      # Second capture group is the color
        if score > maxeval:
            score = maxeval #This is done to prevent massive drops from evals like +6800 (Which had occured once during testing)
        else:
            if score < (0-maxeval):
                score = -(maxeval)
        return score, color
    elif match2:
        score = int(match2.group(1))  
        color = match2.group(2)
        if score > 0:
            weightscore = maxeval + 30//score #I needed a materal value for mates- decided to set it to the max value with slgihtly greater scores for faster mates
        else:
            weightscore = (-maxeval) + (30//score)
        return weightscore, color
    else:
        if response != None:
            if Logging:
                print("Invalid response or game has ended")
        return None
def getevals(pgn,timepermove=0.5): # All evals are from the perspective of white
    evals = []
    board = chess.Board()
    pgn_io = io.StringIO(pgn)
    pgn = chess.pgn.read_game(pgn_io)
    for move in pgn.mainline_moves():
        board.push(move)
        fen = board.fen()
        eval = phrase_stockfish_score(str(analyze_position(fen,time_limit=timepermove)))
        if eval != None:
            if eval[1] == 'BLACK':
                eval = -eval[0]
            else:
                 eval = eval[0]
            if Logging:
                print(board,eval,move)
            evals.append(eval)
            if Logging:
                print(evals)
            #print('\n\n\n\n\n\n')
    return evals
def getascpl(pgn,enginetime=0.5): #Retuns whites acpl, blacks acpl and then the cpl per move for white, and cpl for move for black
    cplsW = []
    cplsB = []
    evalsW = getevals(pgn,timepermove=enginetime)
    evalsB = []
    for eval in evalsW:
        evalsB.append(0-eval)
    for i in range(1,len(evalsB)-1,2):
        cpl = min(evalsB[i]-evalsB[i-1],0)
        if Logging:
            print(evalsB[i],evalsB[i-1],cpl)
        cplsB.append(cpl)
    for i in range(2,len(evalsW)-1,2):
        cpl = min(evalsW[i]-evalsW[i-1],0)
        if Logging:
            print(evalsW[i],evalsW[i-1],cpl)
        cplsW.append(cpl)
    Bsum = 0
    for item in cplsB:
        Bsum += item
    acplB = Bsum//len(cplsB)

    Wsum = 0
    for item in cplsW:
        Wsum += item
    acplW = Wsum//len(cplsW)

    # I decided to reverse all the values to make sure the centipawn losses are in positive numbers
    flipthese = [cplsW,cplsB]
    fliped = []
    for toreverse in flipthese:
        tempresponse = []
        for item in toreverse:
            tempresponse.append(0-item)
        fliped.append(tempresponse)
    cplsW = fliped[0]
    cplsB = fliped[1]


    return 0-acplW,0-acplB,cplsW,cplsB


