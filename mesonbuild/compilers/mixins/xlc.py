# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 The Meson development team

from __future__ import annotations

"""Mixins for the z/OS IBM XL C/C++ compilers."""

import os
import typing as T


if T.TYPE_CHECKING:
    from ...environment import Environment
    from ...compilers.mixins.clike import CLikeCompiler
else:
    # This is a bit clever, for mypy we pretend that these mixins descend from
    # Compiler, so we get all of the methods and attributes defined for us, but
    # for runtime we make them descend from object (which all classes normally
    # do). This gives up DRYer type checking, with no runtime impact
    CLikeCompiler = object

xlc_optimization_args: T.Dict[str, T.List[str]] = {
    'plain': [],
    '0': [],
    'g': [],
    '1': ['-O'],
    '2': ['-O2'],
    '3': ['-O3'],
    's': ['-O'],
}

xlc_debug_args: T.Dict[bool, T.List[str]] = {
    False: [],
    True: [],
}

xlc_warnings: T.Dict[int, T.List[str]] = {
    0: [],
    1: [],
    2: ['gen', 'cmp', 'cnd', 'cnv', 'rea', 'trd'],
    3: ['cmp', 'eff', 'par', 'use', 'pro'],
}

class XlcCompiler(CLikeCompiler):

    id = 'xlc'

    LINKER_PREFIX = '-Wl,'

    def __init__(self) -> None:
        # Assembly
        self.can_compile_suffixes.add('s')
        if self.info.is_zos():
            # Linker commands file
            self.can_compile_suffixes.add('x')
            # Pr-Linker output
            self.can_compile_suffixes.add('p')
            # IPA output
            self.can_compile_suffixes.add('I')

        def default_warnings(level: int) -> T.List[str]:
            warnings = []
            for l in range(0, level + 1):
                warnings.extend(xlc_warnings[l])
            return ['-qinfo' + ':'.join([])]

        self.warn_args = {'0': default_warnings(0),
                          '1': default_warnings(1),
                          '2': default_warnings(2),
                          '3': default_warnings(3),
                          'everything': ['-qinfo=all']}

    def get_always_args(self) -> T.List[str]:
        if self.info.is_zos():
            return ['-qgoff', '-qnocsect', '-qxplink', '-qdll=nocba']
        return []

    def get_linker_always_args(self) -> T.List[str]:
        if self.info.is_zos():
            return ['-qxplink'] + super().get_linker_always_args()
        else:
            return super().get_linker_always_args()

    def get_std_shared_lib_link_args(self) -> T.List[str]:
        if self.info.is_zos():
            return ['-Wl,dll']
        return super().get_std_shared_lib_link_args()

    def get_output_args(self, outputname: str) -> T.List[str]:
        return ['-o', outputname]

    def get_compile_debugfile_args(self, rel_obj: str, pch: bool = False) -> T.List[str]:
        if self.info.is_zos():
            # TODO: Also enables debug info, pass through is_debug
            return [f'-qdebug=file={rel_obj}.dbg', f'-qlist={rel_obj}.lst']
        return []

    def get_compile_only_args(self) -> T.List[str]:
        return ['-c']

    def get_depfile_suffix(self) -> str:
        return 'd'

    def get_preprocess_only_args(self) -> T.List[str]:
        return ['-E', '-P']

    def get_include_args(self, path: str, is_system: bool) -> T.List[str]:
        if not path:
            path = '.'
        if is_system:
            return ['-isystem' + path]
        return ['-I' + path]

    def get_no_stdinc_args(self) -> T.List[str]:
        if self.info.is_zos():
            return ['-qnosearch']
        else:
            return ['-qnostdinc']

    def get_pic_args(self) -> T.List[str]:
        if self.info.is_zos():
            # z/OS does not support absolute addressing
            return []
        else:
            return ['-qpic']

    def get_pie_args(self) -> T.List[str]:
        if self.info.is_zos():
            # z/OS does not support absolute addressing
            return []
        else:
            return super().get_pie_args()

    def get_dependency_gen_args(self, outtarget: str, outfile: str) -> T.List[str]:
        return ['-M', '-MQ', outtarget, '-MF', outfile]

    def openmp_flags(self, env: Environment) -> T.List[str]:
        return ['-qsmp=explicit,opt']

    def get_optimization_args(self, optimization_level: str) -> T.List[str]:
        return xlc_optimization_args[optimization_level]

    def get_debug_args(self, is_debug: bool) -> T.List[str]:
        return xlc_debug_args[is_debug]

    def compute_parameters_with_absolute_paths(self, parameter_list: T.List[str], build_dir: str) -> T.List[str]:
        for idx, i in enumerate(parameter_list):
            if i[:9] == '-I':
                parameter_list[idx] = i[:9] + os.path.normpath(os.path.join(build_dir, i[9:]))

        return parameter_list

    def get_werror_args(self) -> T.List[str]:
        sev = '4' if self.info.is_zos() else 'w'
        return ['-qhalt=' + sev]

    def gnu_symbol_visibility_args(self, vistype: str) -> T.List[str]:
        if self.info.is_zos():
            if vistype == 'default':
                return ['-qexportall']
            return []

        return [f'-qvisibility={vistype}']
