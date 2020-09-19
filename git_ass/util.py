import os
import subprocess

class Commander:
    def __init__(self, **options):
        self.options = options

    def run(self, args, options={}):
        merged = {
            'cwd': None,
            'capture': True,
            'ensure_success': True,
            'debug': os.environ.get('DEBUG'),
        }
        merged.update(self.options)
        merged.update(options)
        if merged['debug']:
            print('$', ' '.join(args))
        kw = {
            'cwd': merged['cwd'],
        }
        if merged['capture']:
            kw['capture_output'] = True
            kw['encoding'] = 'utf-8'
        process = subprocess.run(args, **kw)
        if merged['ensure_success'] and process.returncode:
            raise Exception('Command failed: ' + ' '.join(args))
        return process

    def test(self, args, options={}):
        options = options.copy()
        options['ensure_success'] = True
        try:
            self.run(args, options)
            return True
        except:
            return False

    def read(self, args, options={}):
        options = options.copy()
        options['capture'] = True
        return self.run(args, options).stdout.strip()

COLOR_MAP = {
    'red': 31,
    'green': 32,
    'yellow': 33,
}
def colored_text(text, color):
    color = COLOR_MAP[color]
    return f'\x1b[1;{color}m' + text + '\x1b[0m'
