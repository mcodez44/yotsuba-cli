import urllib.request
import urllib.error
import json
import subprocess

class APIError(Exception): 
    pass

class MediaError(Exception):
    pass

def get_json(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        raise APIError(f'HTTP {e.code}: {url}')
    except urllib.error.URLError as e:
        raise APIError(f'Network Error {e.reason}')

# write flags are a placeholder in case downloading is fully implemented
def download(data, name):
    raw = json.loads(data)

    with open(f'{name}.json', 'w') as f:
        json.dump(raw, f, indent=4)

def get_boards(write=False): 
    return get_json('https://a.4cdn.org/boards.json')

def get_index(board, page, write=False):
    return get_json(f'https://a.4cdn.org/{board}/{page}.json')

def get_thread(board, thread, write=False):
    return get_json(f'https://a.4cdn.org/{board}/thread/{thread}.json')

def get_media(board, tim):
    data = get_json(f'https://a.4cdn.org/{board}/thread/{tim}.json')

    mpv_command = ['mpv', '--pause', '--no-terminal']

    media_info = []

    for post in data['posts']:
        if 'tim' in post:
                media_info.append(('https://i.4cdn.org/' + 
                                    board + '/' + 
                                    str(post['tim']) + 
                                    post['ext'], 
                                    post['filename'] + 
                                    post['ext']))

    if not media_info:
        raise MediaError('no media found')

    for url, filename in media_info:
        mpv_command += ['--{', f'--force-media-title={filename}', url, '--}']

    try:
        subprocess.Popen(mpv_command)
    except FileNotFoundError:
        raise MediaError('mpv not found')
    except OSError as e:
        raise MediaError(str(e))

    # everything works
    return None
