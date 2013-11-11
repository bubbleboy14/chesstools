from setuptools import setup

setup(
    name='chesstools',
    version='0.1.8',
    author='Mario Balibrera',
    author_email='mario.balibrera@gmail.com',
    license='MIT License',
    url="http://www.mariobalibrera.com/mics",
    download_url="http://code.google.com/p/chesstools/downloads/list",
    description="A library of tools for writing chess AI's, as well as servers, clients, and any other software that requires a chess engine.",
    long_description='Speaks proper FEN, SAN, and long algebraic notation. Supports standard chess and chess960 (Fischer-random). Handles move validation and checkmate/ stalemate/ repetition/ 50-move-rule checking. Features server-side timekeeping with optional latency compensation. The compact minimax AI framework utilizes alpha-beta pruning and transposition tables under the hood. This enables the developer to produce a modern custom bot by simply overriding AI.evaluate. Additionally, chesstools.book provides an intuitive interface for building opening book databases for use in conjunction with an ai.',
    packages=[
        'chesstools',
    ],
    entry_points = '''
        [console_scripts]
        buildchessbook = chesstools.book:_build_command_line
    ''',
    install_requires = [
        'sqlalchemy' # should be >= 0.5, but doesn't work properly
    ],
    zip_safe = False,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
