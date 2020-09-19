import os
import sys
import json
import argparse
import subprocess
from .util import Commander, GitAssError

parser = argparse.ArgumentParser(description='Git branch helper')
parser.set_defaults(name=None, handle=None)
subparsers = parser.add_subparsers()

commander = Commander()

class Command:
    def __init__(self, handle, name, *k, **kw):
        self.name = name
        self.parser = subparsers.add_parser(name, *k, **kw)
        self.handle = handle
        self.parser.set_defaults(handle=self)
        if hasattr(handle, '__params__'):
            for k, kw in handle.__params__:
                self.add_argument(*k, **kw)
            del handle.__params__

    def __call__(self, *k, **kw):
        try:
            return self.handle(*k, **kw)
        except (AssertionError, GitAssError):
            if not args.silent: raise

    def add_argument(self, *k, **kw):
        self.parser.add_argument(*k, **kw)

def command(parser_name, *k, **kw):
    def wrap(handle):
        command = Command(handle, parser_name, *k, **kw)
        command.add_argument('-s', '--silent', help='Suppress errors', action='store_true')
        return command
    return wrap

def argument(*k, **kw):
    def wrap(handle):
        if isinstance(handle, Command):
            handle.add_argument(*k, **kw)
        else:
            if not hasattr(handle, '__params__'):
                handle.__params__ = []
            handle.__params__.append((k, kw))
        return handle
    return wrap

def branch_property(key):
    def getx(self):
        return self.data.get(key) or ''
    def setx(self, value=None):
        self.data[key] = value
    def delx(self):
        self.data.pop(key, None)
    return property(getx, setx, delx)

def get_branch_info(args = ()):
    stdout = commander.read(['git', 'branch', *args])
    current = None
    branch_list = set()
    for item in stdout.split('\n'):
        if not item.strip(): continue
        branch_name = item[2:].strip()
        if item.startswith('* '):
            current = branch_name
        branch_list.add(branch_name)
    return current, branch_list

class Branch:
    TYPE_REL = 'release'
    TYPE_DEV = 'development'

    name = branch_property('name')
    desc = branch_property('desc')
    alias = branch_property('alias')
    base = branch_property('base')

    def __init__(self, store, **kw):
        self.store = store
        self.data = {}
        self.data.update(kw)

    def __repr__(self):
        return f'<Branch name={self.name} alias={self.alias}>'

    def __str__(self):
        alias = f'({self.alias})' if self.alias else ''
        base = f'[{self.base}]' if self.base else ''
        return f'{self.name} {alias}\t{base}\t{self.desc}'

    def dump(self):
        return self.data.copy()

    def update(self, info):
        for key, value in info.items():
            if value is None: continue
            self.data[key] = value

    def copy(self):
        return Branch(self.store, **self.data)

class Store:
    def __init__(self, filename=None):
        self.filename = filename
        self.data = {}
        self.alias = {}
        try:
            self.store = json.load(open(filename, encoding='utf-8'))
        except FileNotFoundError:
            self.store = {}
        branch_list = self.store.get(cwd, ())
        for branch_info in branch_list:
            branch = Branch(self, **branch_info)
            self.data[branch.name] = branch
            alias = branch.alias
            if alias:
                self.alias[alias] = branch

    def add(self, merge=True, **branch_info):
        name = branch_info['name']
        old_branch = self.data.get(name)
        if old_branch is None:
            branch = Branch(self, **branch_info)
        else:
            if not merge:
                raise ValueError('Branch already exists')
            alias = old_branch.alias
            if alias:
                self.alias.pop(alias, None)
            branch = old_branch.copy()
            branch.update(branch_info)
        self.data[name] = branch
        alias = branch.alias
        if alias:
            self.alias[alias] = branch
        return branch, old_branch

    def remove(self, name):
        branch = self.data.pop(name, None)
        if branch is not None:
            alias = branch.alias
            if alias:
                self.alias.pop(alias, None)

    def dump(self):
        return [branch.dump() for branch in self.data.values()]

    def dump_to_file(self):
        data = self.dump()
        self.store[cwd] = data
        json.dump(self.store, open(self.filename, 'w', encoding='utf-8'), ensure_ascii=False)

    def find(self, name):
        return self.data.get(name) or self.alias.get(name)

def get_current_branch_name():
    return commander.read(['git', 'rev-parse', '--abbrev-ref', '@'])

def get_branch(name=None):
    branch = store.find(name or get_current_branch_name())
    assert branch is not None, f'Branch {name} not found'
    return branch

@command('info', help='Show information of specified branch')
@argument('-p', '--property', help='Specify property name')
@argument('branch', help='The name or alias of the target branch', nargs='?')
def info():
    branch = get_branch(args.branch)
    if args.property is None:
        ancestors = [branch]
        names = set()
        names.add(branch.name)
        base = branch
        while True:
            assert base.base not in names
            names.add(base.base)
            base = store.find(base.base)
            if base is None: break
            ancestors.append(base)
        for i, branch in enumerate(reversed(ancestors)):
            print('  ' * i, branch, sep='')
    else:
        print(getattr(branch, args.property, None) or '')

@command('add', aliases=['update'], help='Add or update information of specified branch')
@argument('-B', '--base', help='Set base branch')
@argument('-a', '--alias', help='Set alias of current branch')
@argument('-d', '--description', help='Set description of a branch')
@argument('branch', help='The name or alias of the target branch', nargs='?')
def add():
    base = None
    if args.base:
        base_branch = store.find(args.base)
        assert base_branch, 'Base branch not found'
        base = base_branch.name
    branch, old_branch = store.add(
        alias=args.alias,
        base=base,
        name=args.branch or get_current_branch_name(),
        desc=args.description)
    if old_branch is None:
        print('New branch added:')
    else:
        print('Branch updated:')
    print(branch)
    store.dump_to_file()

@command('find', aliases=['f'], help='Find branch by alias')
@argument('branch', help='The name or alias of the target branch', nargs='?')
def find():
    branch = get_branch(args.branch)
    print(branch.name)

@command('remove', aliases=['rm'], help='Remove information of specified branch')
@argument('branch', help='The name or alias of the target branch', nargs='?')
def remove():
    branch = get_branch(args.branch)
    store.remove(branch.name)
    print('Branch removed:')
    print(branch)
    store.dump_to_file()

@command('rebase', help='Rebase current branch on top of its base branch')
def rebase():
    current_branch = get_branch()
    base_name = current_branch.base or current_branch.name
    commander.run(['git', 'fetch'])
    commander.run(['git', 'rebase', f'origin/{base_name}'])

@command('list', help='List branches of interest')
def list_branches():
    current_branch_name = get_current_branch_name()
    parent_map = {}
    child_map = {}
    for branch in store.data.values():
        base_branch = store.find(branch.base)
        if base_branch is not None:
            parent_map[branch.name] = branch.base
            child_map.setdefault(branch.base, []).append(branch.name)
        parent_map.setdefault(branch.name, None)
    def dump_branch(branch_name, indent=0):
        branch = store.find(branch_name)
        mark = '* ' if branch_name == current_branch_name else '  '
        print(mark, '  ' * indent, branch, sep='')
        children = child_map.get(branch_name)
        if children:
            for child in sorted(children):
                dump_branch(child, indent + 1)
    for branch_name in sorted(key for (key, value) in parent_map.items() if value is None):
        dump_branch(branch_name)

@command('checkout', aliases=['co'], help='Check out a branch based on name or alias')
@argument('branch', help='The name or alias of the target branch', nargs='?')
def checkout():
    branch = get_branch(args.branch)
    commander.run(['git', 'checkout', branch.name])

@command('prune', help='Prune inexistent branches')
def prune():
    commander.run(['git', 'fetch', '--all', '--prune'])
    _, remote_branches = get_branch_info(('-r',))
    _, local_branches = get_branch_info()
    remote_branches = set(name.partition('/')[2] for name in remote_branches)
    to_remove = set()
    to_drop_base = set()
    for branch in store.data.values():
        branch_name = branch.name
        if '/' in branch_name:
            # local branch
            if branch_name not in local_branches:
                to_remove.add(branch_name)
        else:
            # remote branch
            if branch_name not in remote_branches:
                to_remove.add(branch_name)
    for branch in store.data.values():
        branch_base = branch.base
        if branch_base in to_remove:
            to_drop_base.add(branch)
    if to_remove:
        print('Prune branches:')
        for branch_name in sorted(to_remove):
            print('-', branch_name)
            store.remove(branch_name)
        if to_drop_base:
            print('Drop base:')
            for branch in sorted(to_drop_base, key=lambda b: b.name):
                print('-', branch.name)
                del branch.base
        store.dump_to_file()
    else:
        print('No branch to prune')

@command('purge', help='Remove locally merged branches')
def purge():
    current, local_branches = get_branch_info()
    print('Purge local branches:')
    for branch_name in local_branches:
        if branch_name == current: continue
        print('-', branch_name, end='')
        ret = commander.run(['git', 'branch', '-d', branch_name], capture=True, ensure_success=False)
        if ret.returncode:
            if ' is not fully merged.' in ret.stderr:
                # branch is not fully merged
                print(' - not fully merged, skipped')
                continue
            error = ret.stderr
        else:
            error = None
        if error is not None:
            print(' - error')
            print(error)
        else:
            print(' - ok')

@command('push', aliases=['p'], help='Push to remote and check if code is changed')
def push():
    commander.run(['git', 'push', *unknown])
    commander.run(['git', 'fetch'])
    remote = commander.read(['git', 'rev-parse', '--symbolic-full-name', '@{u}'])
    ret = commander.run(['git', 'diff', remote, '--exit-code'], ensure_success=False)
    if ret.returncode:
        print(
            '\n\x1b[31m' +
            f'Your branch is different from `{remote}`,\nit is likely that malicious commits are injected.' +
            '\x1b[0m'
        )
        exit(1)

@command('autocomplete', add_help=False)
@argument('commands', nargs='*', default=())
def autocomplete():
    def get_command(index):
        if index < len(args.commands):
            return args.commands[index]
        return ''
    first = get_command(0)
    if not first:
        items = []
        choices = subparsers.choices
        for key in sorted(choices.keys()):
            parser = choices[key]
            if parser.add_help:
                items.append(key)
        complete = ' '.join(items)
        print(f'2: :({complete})')
    else:
        if first in ('info', 'add', 'update', 'remove', 'rm', 'checkout', 'co', 'find', 'f'):
            complete = ' '.join(list(store.alias.keys()) + list(store.data.keys()))
            print(f'*: :({complete})')

appdir = os.path.dirname(os.path.dirname(__file__))
datadir = os.path.join(appdir, 'data')
cwd = os.getcwd()

os.makedirs(datadir, exist_ok=True)
store = Store(os.path.join(datadir, 'data.json'))

args, unknown = parser.parse_known_args()

if args.handle is None:
    parser.print_help()
else:
    args.handle()
