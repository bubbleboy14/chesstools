chesstools 0.2.4.11

A library of tools for writing chess AI's, as well as servers, clients, and any other software that requires a chess engine. Speaks proper FEN, SAN, and long algebraic notation. Supports standard chess and chess960 (Fischer-random). Handles move validation and checkmate/ stalemate/ repetition/ 50-move-rule checking. Features server-side timekeeping with optional latency compensation.

The compact minimax AI framework utilizes alpha-beta pruning and transposition tables under the hood. This enables the developer to produce a modern custom bot by simply overriding AI.evaluate. Additionally, chesstools.book provides an intuitive interface for building opening book databases for use in conjunction with an ai.

AI developers are encouraged to install [psyco](http://psyco.sourceforge.net/), which will significantly speed up bot performance.

For sample code, see [MICS](https://github.com/bubbleboy14/micserver) and [MICC](https://github.com/bubbleboy14/micclient). Tutorials [here](http://mariobalibrera.com/mics).
