import json
import os
import api
import formatting

from extra import *


if not os.path.isfile('osdg.json'):
    data = api.error_handling('https://a.4cdn.org/g/thread/109900686.json')

    if data != 'ERROR':
        data = json.loads(api.download(data, 'osdg'))
    else:
        print("error: couldn't get file")
else:
    with open('osdg.json', 'r') as f:
        data = json.load(f)

syntax = """
Syntax
-----------------
Available commands: thread, board, image, listboards
<--LB-->
/listboards              -> lists all boards
/board [board] [page]    -> goes to specified board, optionally you can select a page
/thread [board] [number] -> goes to thread index as specified in [number] of chosen board
/image [board] [number]  -> works like /thread but instead opens external media in mpv
<--LB-->
Sample commands
-----------------
/listboards
/board v
/board g 3
/thread v 8
/image g 5
"""

formatted_data = formatting.format(data, 'posts')
string = formatting.strformat(syntax)
message = chunks2lines(string, 120)
thread = chunks2lines(formatted_data, 120)

print('\n'.join(''.join(chunk[0] for chunk in line) for line in message))
