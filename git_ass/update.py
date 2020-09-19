'''
Copyright (c) 2020 Gerald <i@gerald.top>

Update all repositories in a directory.

Usage:

    python3 -m git_ass.update MyGitRepos
'''

import asyncio
import concurrent
import io
import os
import sys
from .util import Commander, colored_text

def check_repo(project_dir):
    stream = io.StringIO()
    stream.write('> ')
    stream.write(os.path.basename(project_dir).ljust(24))
    if not working:
        stream.write(colored_text('aborted', 'yellow'))
        return stream.getvalue()
    commander = Commander(cwd=project_dir, capture=True)
    if not os.path.isdir(os.path.join(project_dir, '.git')):
        stream.write(colored_text('invalid repo, skipped', 'yellow'))
        return stream.getvalue()
    try:
        commander.run(['git', 'fetch'])
    except Exception as e:
        stream.write(colored_text('Error', 'red'))
        stream.write('\n')
        stream.write(str(e))
        return stream.getvalue()
    dirty = not commander.test(['git', 'diff', '--exit-code'])
    if dirty:
        stream.write(colored_text('dirty, skipped', 'yellow'))
    else:
        upstream = commander.read(['git', 'rev-parse', '--abbrev-ref', '@{upstream}'])
        if commander.test(['git', 'diff', upstream, '--exit-code']):
            stream.write(colored_text('up to date', 'green'))
        elif commander.test(['git', 'pull', '--ff-only']):
            stream.write(colored_text('updated, fast-forwarded', 'green'))
        else:
            stream.write(colored_text('cannot fast-forward, skipped', 'red'))
    return stream.getvalue()

async def work(projects):
    loop = asyncio.get_event_loop()
    futures = {}
    finished = 0
    total = len(projects)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        for project in projects:
            future = loop.run_in_executor(pool, check_repo, project)
            futures[future] = os.path.basename(project)
        pending = list(futures.keys())
        while pending and working:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for future in done:
                result = await future
                if result is None: result = ''
                finished += 1
                print(f'({finished}/{total}) {result}')

root = sys.argv[1]
working = True
try:
    asyncio.run(work([os.path.join(root, project) for project in os.listdir(root)]))
except KeyboardInterrupt:
    print('Shutting down...')
    working = False
