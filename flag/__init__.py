'''
A module used for automatically parsing command line flag arguments.
'''

from abc import ABC
from typing import Any, Dict, SupportsFloat, SupportsInt, TypeVar, Type
import re
import sys
import os

__all__ = ['IntFlag', 'StrFlag', 'BoolFlag', 'FloatFlag', 'parse', 'print_defaults']

FlagType = TypeVar('FlagType', str, int, bool, float)

class _Flag(ABC):
    @classmethod
    def _check_against(cls, value: FlagType, _type: Type):
        if not isinstance(value, _type):
            _write_exc(f'Invalid type for flag of type {_type}: {type(value).__name__}')

    @classmethod
    def _get_arg_name(cls, desc: str) -> str:
        matches = re.findall(r"'(.*?)'", desc)
        if not matches:
            return ''

        if len(matches) > 1:
            _write_exc(f'Argument names conflict in "{desc}", between: {", ".join(matches)}')

        return matches[0].replace("'", '')

    def __init__(self, name: str, default: FlagType, flag_type: Type, desc: str, mandatory: bool):
        _Flag._check_against(default, flag_type)

        self.name: str = name
        self.default: FlagType = default
        self.desc: str = desc
        self.mandatory: bool = mandatory
        self.type: Type = flag_type
        self.arg_name: str = _Flag._get_arg_name(self.desc)
        self._value: FlagType = self.default

        if self.arg_name:
            self.desc = self.desc.replace('\'', '')

        _register_flag(self)

    def description(self) -> None:
        '''
        Prints a description of the flag.
        '''

        if isinstance(self, BoolFlag):
            print(f'--{self.name}')
        else:
            print(f'-{self.name} {self.arg_name}')

        print(f'    {self.desc}{" (mandatory)" if self.mandatory else ""}')

    @property
    def is_default(self) -> bool:
        '''
        Returns true if flag is currently set to
        default value
        '''

        return self.value == self.default

    @property
    def value(self) -> FlagType:
        '''
        Current value of the flag
        '''

        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        try:
            conv = self.type(value)
        except ValueError:
            _write_exc(f'Cannot convert value "{value}" for {type(self).__name__} "{self.name}".\
                 (expected type: {self.type.__name__})')

        self._value = conv

    def __repr__(self) -> str:
        return str(self)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __str__(self) -> str:
        return str(self.value)

class IntFlag(_Flag, SupportsInt):
    '''
    A flag that supports integer values.
    '''

    def __init__(self, name: str, default: int, desc: str, *, mandatory: bool=False):
        super().__init__(name, default, int, desc, mandatory)

    def __int__(self) -> int:
        return self.value

    def __eq__(self, o: SupportsInt) -> bool:
        return self.value == int(o)

    def __ne__(self, o: SupportsInt) -> bool:
        return self.value != int(o)

    def __lt__(self, o: SupportsInt) -> bool:
        return self.value < int(o)

    def __le__(self, o: SupportsInt) -> bool:
        return self.value <= int(o)

    def __gt__(self, o: SupportsInt) -> bool:
        return self.value > int(o)

    def __ge__(self, o: SupportsInt) -> bool:
        return self.value >= int(o)

class FloatFlag(_Flag, SupportsFloat):
    '''
    A flag that supports floating point values.
    '''

    def __init__(self, name: str, default: float, desc: str, *, mandatory: bool=False):
        super().__init__(name, default, float, desc, mandatory)

    def __float__(self) -> float:
        return self.value

    def __eq__(self, o: SupportsFloat) -> bool:
        return self.value == float(o)

    def __ne__(self, o: SupportsFloat) -> bool:
        return self.value != float(o)

    def __lt__(self, o: SupportsFloat) -> bool:
        return self.value < float(o)

    def __le__(self, o: SupportsFloat) -> bool:
        return self.value <= float(o)

    def __gt__(self, o: SupportsFloat) -> bool:
        return self.value > float(o)

    def __ge__(self, o: SupportsFloat) -> bool:
        return self.value >= float(o)

class StrFlag(_Flag):
    '''
    A flag that supports string values.
    '''

    def __init__(self, name: str, default: str, desc: str, *, mandatory: bool=False):
        super().__init__(name, default, str, desc, mandatory)

    def __eq__(self, o: object) -> bool:
        return self.value == str(o)

    def __ne__(self, o: object) -> bool:
        return self.value != str(o)

class BoolFlag(_Flag):
    '''
    A flag that supports boolean values.
    '''

    def __init__(self, name: str, desc: str):
        super().__init__(name, False, bool, desc, False)

    def __eq__(self, o: object) -> bool:
        return self.value == bool(o)

    def __ne__(self, o: object) -> bool:
        return self.value != bool(o)

_flags_registered: Dict[str, _Flag] = {}
_unsatisfied_mandatory: Dict[str, _Flag] = {}

def _write_exc(exception: str) -> None:
    sys.stderr.write(f'Error: {exception}\n')
    print_defaults()
    sys.exit(1)

def _register_flag(flag: _Flag) -> None:
    if flag.name in _flags_registered:
        _write_exc(f'_Flag already registered: {flag.name}.')

    _flags_registered[flag.name] = flag

    if flag.mandatory:
        _unsatisfied_mandatory[flag.name] = flag

def print_defaults() -> None:
    '''
    Prints all flags usage informations.
    '''

    print(f'Usage of {os.path.basename(sys.argv[0])}:')

    for flag in _flags_registered.values():
        flag.description()

def parse() -> None:
    '''
    Parses given command line arguments and puts values
    into corresponding flags.
    '''

    argv = sys.argv.copy()

    argv.pop(0)

    flags_provided = []

    while len(argv) != 0:
        arg = argv.pop(0)
        real_name = ''
        value = None

        if '=' in arg:
            # support -name=value style flags
            real_name, value = arg.split('=')
        elif arg.startswith('--'):
            # support --name style boolean flags
            real_name = arg
            value = True
        elif arg.startswith('-'):
            # support -name value style flags
            real_name = arg
            value = argv.pop(0)
        else:
            _write_exc(f'Invalid flag format: {arg}.')

        name = real_name.replace('-', '')

        if name not in _flags_registered:
            _write_exc(f'Unknown flag: {name}.')

        matched_flag = _flags_registered[name]

        if isinstance(matched_flag, BoolFlag) and not real_name.startswith('--'):
            if '=' in arg:
                hint = '-flag_name=value'
            else:
                hint = '-flag_name value'
            _write_exc(f'Boolean flags have to be specified as "--flag_name" not "{hint}".')

        matched_flag.value = value
        flags_provided.append(name)

    for flag_name in flags_provided:
        _unsatisfied_mandatory.pop(flag_name, None)

    if len(_unsatisfied_mandatory) != 0:
        unsatisfied = list(_unsatisfied_mandatory.values())
        _write_exc(f'Mandatory flag "{unsatisfied[0].name}" not provided.')
