#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function


def _foam_cases(path):
    """Walk through sub-folders of path, return ones with system folder."""
    from os import walk
    from os.path import join, exists
    for root, dirs, files in walk(path):
        for d in dirs:
            case_path = join(root, d)
            system_folder = join(case_path, 'system')
            if exists(system_folder):
                yield case_path


def _plot_flow_field(path):
    """Plot sampled flow field."""
    pass


def _run_pimple_log_stats(path):
    """Collect running stats."""
    from subprocess import call
    import os
    from sys import stdout
    devnull = open(os.devnull, 'wb')
    log_file = os.path.join(path, 'log')
    if os.path.exists(log_file):
        print('  pimple-log-stats ... ', end='')
        stdout.flush()
        fout = open(os.path.join(path, 'exec-stats.dat'), 'w')
        fin = open(log_file, 'r')
        call(['pimple-log-stats'], stdout=fout, stdin=fin, stderr=devnull)
        fin.close()
        fout.close()
        print('done.')
    devnull.close()


def _run_sample(path, sample_dict, dialect='4.x'):
    """Sample flow field."""
    from subprocess import call
    import os
    from sys import stdout
    devnull = open(os.devnull, 'wb')
    print('  sample ... ', end='')
    stdout.flush()
    if dialect == '4.x':
        call(['postProcess', '-func', 'sampleDict', '-dict', sample_dict,
              '-case', path, '-time', '150'], stdout=devnull, stderr=devnull)
    elif dialect == '2.4.x':
        call(['sample', '-dict', sample_dict, '-case', path, '-time', '150'],
             stdout=devnull, stderr=devnull)
    else:
        raise RuntimeError('Unknown dialect')
    print('done.')
    stdout.flush()
    devnull.close()


def _run():
    from os import getcwd
    from sys import stdout
    import os.path
    sample_dict = os.path.join(getcwd(), 'sampleDict')

    version = os.path.basename(os.getenv('WM_PROJECT_DIR')).split('-').pop()

    for path in _foam_cases('.'):
        print('Post-processing {0}'.format(path))
        stdout.flush()
        _run_sample(path, sample_dict, dialect=version)
        _run_pimple_log_stats(path)
        _plot_flow_field(path)
    return 0


if __name__ == '__main__':
    from sys import exit as e
    e(_run())
