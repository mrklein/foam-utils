#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Utility to convert pimpleFoam-family solver log-file into data for plotting.

SYNOPSIS

    pimple-log-stats.py [-f] [-r] [-i FILE] [-o FILE]

DESCRIPTION

    Read log-file, parse useful information, and write it to multi-column
    file for further analysis. By default log is read from stdin and output is
    written to stdout. This can be overridden by -i and -o flags
    correspondingly.

    -i, --input=FILE
            Read log from file

    -o, --output=FILE
            Write output to file

    -f, --force
            Overwrite output file

    -r, --residuals
            Parse linear solvers residuals information and write it to separate
            files (currently is not implemented)

COPYRIGHT
    Copyright (C) 2016 Alexey Matveichev. License: MIT <https://opensource.org/licenses/MIT>.
"""

import sys


class NoMoreItems(Exception):
    """Exception raised upon the end of log file."""
    pass


class EndOfItem(Exception):
    """Exception raised upon reaching the end of time step item."""
    pass


class LogLineRegexp(object):

    """Object which matches line with regular expression."""

    def __init__(self, regex, var, *args, **kwargs):
        """Constructor

        :param regexp: -- string, regular expression to match
        :param var: -- string, variable name to set, all non-keyword arguments
                       are added to the list of variables
        Keyword arguments:
        :param end: -- boolean, set regular expression as the end of time step
                       item, if matches EndOfItem exception is risen.
        :match: -- string, name of boolean variable to set in case of regular
                   expression match
        """
        import re

        self._regex = regex
        self._re = re.compile(regex)
        self._vars = [var]
        for arg in args:
            self._vars.append(arg)
        if self._re.groups != len(self._vars):
            raise UserWarning('Number of groups in regular expression '
                              'should be equal to number of variables')
        if 'end' in kwargs:
            self._end = kwargs['end']
        else:
            self._end = False

        if 'match' in kwargs:
            self._match = kwargs['match']
        else:
            self._match = None

    def __call__(self, line, obj):
        """Perform search of regular expression in supplied line.

        In case of match set properties of object.

        :param line: -- line to match
        :param obj: -- object where properties as set
        """
        r = self._re.search(line)
        if r is None:
            return False
        else:
            for i, v in enumerate(r.groups()):
                setattr(obj, self._vars[i], v)
            if self._end:
                raise EndOfItem()
            if self._match is not None:
                setattr(obj, self._match, True)
            return True

    def __str__(self):
        return self._regex


class LogItemParser(object):

    """Raw data items collector."""

    def __init__(self, fin=sys.stdin, fout=sys.stdout, residuals=None):
        # Input and output file objects
        self._fin = fin
        self._fout = fout
        # Whether we collect residual information
        self._write_residuals = residuals

        # Time step item content
        self._courant_number_mean = 0
        self._courant_number_max = 0
        self._delta_t = -1
        self._time = -1
        self._time_index = 0
        self._converged = False
        self._converged_in = -1
        self._niterations = -1
        self._continuity_errors_local = -1
        self._continuity_errors_global = -1
        self._continuity_errors_cumulative = -1
        self._residuals = {}
        self._execution_time = -1
        self._clock_time = -1

        # Regular expressions for different parts of item
        self._line_regexps = [
            LogLineRegexp('^ExecutionTime = (.+) s  ClockTime = (.+) s$',
                          'execution_time', 'clock_time', end=True),
            LogLineRegexp('^Courant Number mean: (.+) max: (.+)$',
                          'courant_number_mean', 'courant_number_max'),
            LogLineRegexp('^deltaT = (.+)$', 'delta_t'),
            LogLineRegexp('^Time = (.+)$', 'time'),
            LogLineRegexp('^time step continuity errors : sum local = (.+), '
                          'global = (.+), cumulative = (.+)$',
                          'continuity_errors_local',
                          'continuity_errors_global',
                          'continuity_errors_cumulative'),
            LogLineRegexp('^PIMPLE: converged in (\d+) iterations$',
                          'niterations', match='converged'),
            LogLineRegexp('^PIMPLE: not converged within (\d+) iterations$',
                          'niterations', match='not_converged')
        ]

    @property
    def time_index(self):
        return self._time_index

    @property
    def courant_number_mean(self):
        return self._courant_number_mean

    @courant_number_mean.setter
    def courant_number_mean(self, val):
        self._courant_number_mean = val


    @property
    def delta_t(self):
        return self._delta_t

    @delta_t.setter
    def delta_t(self, val):
        self._delta_t = val

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, val):
        self._time = val

    @property
    def niterations(self):
        return self._niterations

    @niterations.setter
    def niterations(self, val):
        self._niterations = val

    @property
    def converged(self):
        return self._converged

    @converged.setter
    def converged(self, val):
        self._converged = val

    @converged.setter
    def not_converged(self, val):
        self._converged = not val

    @property
    def continuity_errors_local(self):
        return self._continuity_errors_local

    @continuity_errors_local.setter
    def continuity_errors_local(self, val):
        self._continuity_errors_local = val

    @property
    def continuity_errors_global(self):
        return self._continuity_errors_global

    @continuity_errors_global.setter
    def continuity_errors_global(self, val):
        self._continuity_errors_global = val

    @property
    def continuity_errors_cumulative(self):
        return self._continuity_errors_cumulative

    @continuity_errors_cumulative.setter
    def continuity_errors_cumulative(self, val):
        self._continuity_errors_cumulative = val

    def slurp(self):
        """Read one item from input file."""
        try:
            while True:
                line = self._fin.next()
                for regex in self._line_regexps:
                    regex(line, self)
        except EndOfItem:
            self._time_index += 1
        except StopIteration:
            raise NoMoreItems()

    def spit(self):
        """Write item to output file."""
        self._fout.write(
            '{0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10} {11}\n'.format(
                self.time_index, self.time, self.delta_t,
                self.courant_number_mean,
                self.courant_number_max, self.continuity_errors_local,
                self.continuity_errors_global,
                self.continuity_errors_cumulative, self.niterations,
                '1' if self.converged else 0,  self.execution_time,
                self.clock_time
        ))
        if self._write_residuals:
            pass

    def header(self):
        """Return string with column names."""
        return '# 0_step# 1_time 2_dt 3_Co_mean 4_Co_max 5_err_local ' \
            '6_err_global 7_err_cumulative 8_niter 9_converged? ' \
            '10_exec_time 11_clock_time'


def _run():
    from os.path import exists
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-i', '--input', nargs=1, action='store', type=str,
                        help='Read log from file instead of stdin')
    parser.add_argument('-o', '--output', nargs=1, action='store', type=str,
                        help='Write output to file instead of stdout')
    parser.add_argument('-f', '--force', action='store_true',
                        help='Overwrite output file if it exists')
    parser.add_argument('-r', '--residuals', action='store_true',
                        help='Write residuals data into '
                        '<output>_<field name> files')
    args = parser.parse_args()

    fin = sys.stdin
    fout = sys.stdout
    rout = None
    if args.input is not None:
        if not exists(args.input[0]):
            raise IOError('{0} does not exist'.format(args.input))
        fin = open(args.input[0], 'r')
    if args.output is not None:
        if exists(args.output[0]) and not args.force:
            raise IOError('{0} exists, wont overwrite'.format(args.output))
        fout = open(args.output[0], 'w')
    if args.residuals:
        if args.output is not None:
            rout = args.output
        else:
            rout = 'residual'
    log_parser = LogItemParser(fin, fout, rout)
    try:
        fout.write('{0}\n'.format(log_parser.header()))
        while True:
            log_parser.slurp()
            log_parser.spit()
    except NoMoreItems:
        sys.stderr.write('Finished parsing log file.\n')
        return 0


if __name__ == '__main__':
    sys.exit(_run())
