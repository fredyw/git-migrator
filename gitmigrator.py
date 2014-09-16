#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014 Fredy Wijaya
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#  
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys, os, subprocess, logging, argparse, shutil, stat, errno

logger = None

def execute(cmd):
    logger.info('Command: %s' % ' '.join(cmd))
    subprocess.check_call(cmd)

def execute_output(cmd):
    branches = []
    out = subprocess.check_output(cmd)
    for line in out.split(os.linesep):
        stripped_line = line.strip()
        if stripped_line.startswith('remotes/origin'):
            if stripped_line.startswith('remotes/origin/HEAD'): continue
            branches.append(os.path.basename(stripped_line))
    return branches

# this workaround is needed for Windows
def handle_remove_readonly(func, path, exc):
    excvalue = exc[1]
    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
        func(path)
    else:
        raise

def migrate(src_repo, dest_repo):
    tmp_repo = '.tmprepo'
    new_remote = 'newremote'
    old_cwd = os.getcwd()
    try:
        if os.path.exists(tmp_repo):
            shutil.rmtree(tmp_repo, ignore_errors=False, onerror=handle_remove_readonly)
        execute(['git', 'clone', src_repo, tmp_repo])
        os.chdir(tmp_repo)
        branches = execute_output(['git', 'branch', '-a'])
        execute(['git', 'remote', 'add', new_remote, dest_repo])
        for branch in branches:
            execute(['git', 'push', new_remote,
                     '+refs/remotes/origin/' + branch + ':' +
                     'refs/heads/' + branch])
        execute(['git', 'push', new_remote, '--tags'])
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(tmp_repo, ignore_errors=False, onerror=handle_remove_readonly)

def configure_logger():
    global logger
    FORMAT = '%(asctime)s [%(levelname)-5s] %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)
    logger = logging.getLogger('gitmigrator')

def help_formatter():
    return lambda prog: argparse.HelpFormatter(prog, max_help_position=30)
 
def validate_args():
    parser = argparse.ArgumentParser(formatter_class=help_formatter())
    parser.add_argument('--source', type=str, required=True,
                        help='source repository URL')
    parser.add_argument('--destination', type=str, required=True,
                        help='destination repository URL')
    return parser.parse_args()
    
if __name__ == '__main__':
    configure_logger()
    args = validate_args()
    try:
        migrate(args.source, args.destination)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)
