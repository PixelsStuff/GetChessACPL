
import chess
import chess.engine
import time
import chess.pgn
import io
import re
import asyncio

#SETTINGS#
stockfish_path = '/Users/[user]]/stockfish' #Change this to your own stockfish path
Logging = False 

ExamplePGN = '''
e4 d6 2. d4 Nf6 3. Nc3 g6 4. Nf3 Bg7 5. Bd3 Bg4 6. h3 Bxf3 7. Qxf3 Nc6 8. Ne2 e5 9. d5 Nd4 10. Qg3 Nxc2+ 11. Bxc2 Nh5 12. Qb3 b6 13. Qb5+ Qd7 14. Qxd7+ Kxd7 15. Ba4+ Ke7 16. Bc6 Rab8 17. O-O Rhd8 18. Bg5+ f6 19. Be3 Kf8 20. g4 Nf4 21. Nxf4 exf4 22. Bxf4 f5 23. exf5 gxf5 24. f3 fxg4 25. fxg4 Bxb2 26. Be5+ Kg8 27. Bxb2 Rf8 28. Rxf8+ Rxf8 29. Rf1 Rxf1+ 30. Kxf1 Kf7 31. Kf2 Kg6 32. Kf3 Kg5 33. Bg7 Kg6 34. Bf8 Kf7 35. Bh6 Kg6 36. Bf4 Kf7 37. Kg3 Kg6 38. Kh4 Kf7 39. Kh5 Kf6 40. Bg5+ Kf7 41. Bd8 Kg7 42. Bxc7 Kf6 43. Bxd6 Kg7 44. Bb8 Kf7 45. Bxa7'''

async def analyze_position(fen: str, time_limit=0.5, stockfish_path=stockfish_path):
    """
    Asynchronously analyzes a chess position using Stockfish.
    """
    board = chess.Board(fen)
    
    # Use asyncio's run_in_executor for the synchronous call
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,  # None uses the default ThreadPoolExecutor
        lambda: _analyze_sync(board, time_limit, stockfish_path)
    )
    return result
def _analyze_sync(board, time_limit, stockfish_path):
    """
    Helper function to run Stockfish analysis synchronously.
    """
    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
        try:
            result = engine.analyse(board, chess.engine.Limit(time=time_limit))
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
async def getevals(pgn,timepermove=0.5): # All evals are from the perspective of white
    evals = []
    board = chess.Board()
    pgn_io = io.StringIO(pgn)
    pgn = chess.pgn.read_game(pgn_io)
    tasks = []
    for move in pgn.mainline_moves():
        board.push(move)
        fen = board.fen()
        tasks.append(analyze_position(fen, time_limit=timepermove))
        #eval = phrase_stockfish_score(str(analyze_position(fen,time_limit=timepermove)))
    results = await asyncio.gather(*tasks)
    for result in results:
        if result:
            eval = phrase_stockfish_score(str(result))
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
async def getascpl(pgn,enginetime=0.5,cap=1000): #Retuns whites acpl, blacks acpl and then the cpl per move for white, and cpl for move for black
    cplsW = []
    cplsB = []
    evalsW = await getevals(pgn,timepermove=enginetime)
    evalsB = []
    for eval in evalsW:
        evalsB.append(0-eval)
    for i in range(1,len(evalsB)-1,2):
        cpl = min(evalsB[i]-evalsB[i-1],0)
        if Logging:
            print(evalsB[i],evalsB[i-1],cpl)
        if cpl < -cap:
            cpl = -cap
        cplsB.append(cpl)
    for i in range(2,len(evalsW)-1,2):
        cpl = min(evalsW[i]-evalsW[i-1],0)
        if Logging:
            print(evalsW[i],evalsW[i-1],cpl)
        if cpl < -cap:
            cpl = -cap
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
'''
Cur = time.time()
print(asyncio.run(getascpl(ExamplePGN,enginetime=1)))
print(time.time()-Cur)
'''
