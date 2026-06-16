# Stockfish Binary

Download Stockfish separately and place the executable here:

```text
engines/stockfish/stockfish.exe
```

Do not commit the Stockfish binary to Git.

For Stockfish 18, `UCI_Elo` is valid from 1320 to 3190. If you want an
opponent weaker than 1320, use `Skill Level` or a different engine, but do not
label that setting as standard Elo.

If your executable has a different file name or lives in another location, update the `cmd` field in:

```text
configs/stockfish_levels.json
```
