import chess

# Opprett et nytt brett
board = chess.Board()

# Dine variabler (eksempel)
fra = "e2"
til = "e4"

# Sett sammen til en UCI-streng (e2e4)
trekk_streng = fra + til

# Gjør om strengen til et Move-objekt
move = chess.Move.from_uci(trekk_streng)

# Sjekk om trekket er lovlig før du utfører det
if move in board.legal_moves:
    board.push(move)
    print("Trekk utført!")
else:
    print("Ulovlig trekk!")

# Vis brettet (i tekstform)
print(board)