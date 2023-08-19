# SPDX-License-Identifier: MIT

"""
A tool for managing changelog formatted data and objects (see
keepachangelog.com). In Python, the data is managed as a list of
dictionaries (see README.md for the dictionaries' structure)
"""

__version__ = '0.0.6'

import re
import textwrap
from datetime import date
from typing import ( Optional, Any )
from io import ( IOBase, TextIOBase, StringIO )
from semver import Version

class ChangelogParsingError( Exception ):
    """
    An error used when changelog data isn't formatted as the parser expects
    """
    @property
    def line_number( self )-> Optional[ int ]:
        """
        Parse the line number from the error message, if defined
        """
        if ( match := re.search( r' \(at line (\d+)(?:, column \d+)?\)$', str( self ) ) ):
            return int( match.group( 1 ) )

    @property
    def column_number( self )-> Optional[ int ]:
        """
        Parse the column number from the error message, if defined
        """
        if ( match := re.search( r' \(at (?:line \d+, )?column (\d+)\)$', str( self ) ) ):
            return int( match.group( 1 ) )

    def __init__( self, msg: str, line_number: Optional[ int ] = None, column_number: Optional[ int ] = None ):
        specifications = (
            *( ( f'line { line_number }', ) if isinstance( line_number, int ) else () ),
            *( ( f'column { column_number }', ) if isinstance( column_number, int ) else () )
        )
        super().__init__( msg + ( f' (at { ", ".join( specifications ) })' if specifications else '' ) )

def load( fp: IOBase, encoding: str = 'utf-8' )-> list[ dict[ str, Any ] ]:
    """
    Parse changelog data from a stream

    :param input: a stream that outputs changelog data (eg. a file opened for reading)
    :param encoding: if the stream outputs binary data, decode it using this encoding
    :return: a list of dictionaries with changelog data (see README.md for structure)
    """
    line_no, changes, section, in_compare_urls = 0, [], None, False

    while ( line := fp.readline() ):
        line_no += 1
        if isinstance( line, bytes ):
            try:
                line = line.decode( encoding )
            except Exception as e:
                raise ChangelogParsingError(
                    msg = f'Unable to decode line using encoding, "{ encoding }"',
                    line_number = line_no
                ) from e
        if isinstance( line, str ):
            line = line.removesuffix( '\n' )
        else:
            raise ChangelogParsingError(
                f'Parameter\'s "readline" function call returned unreadable type, "{ type( line ).__name__ }"'
            )

        if line.startswith( '## ' ) and not in_compare_urls:
            if section is not None:
                if changes[ -1 ][ section ]:
                    changes[ -1 ][ section ][ -1 ] = changes[ -1 ][ section ][ -1 ].rstrip()
                section = None

            changes.append( { "date": None,  } )

            if line.rstrip() != line:
                raise ChangelogParsingError(
                    msg = "Extra space(s) at end of line",
                    line_number = line_no,
                    column_number = len( line.rstrip() ) + 1
                )
            if line.endswith( " [YANKED]" ):
                changes[ -1 ][ "yanked" ] = True
                line = line.removesuffix( " [YANKED]" )
            else:
                changes[ -1 ][ "yanked" ] = False

            if line.rstrip() != line:
                raise ChangelogParsingError( "Extra space(s) after date", line_no, len( line.rstrip() ) + 1 )
            line, sep, change_date = line.partition( ' - ' )
            if change_date.lstrip() != change_date:
                raise ChangelogParsingError( "Extra space(s) before date", line_no, len( line + sep ) + 1 )
            if "]" in line and not line.rstrip().endswith( "]" ):
                raise ChangelogParsingError(
                    msg = 'Version and date must be separated by " - "',
                    line_number = line_no,
                    column_number = line.find( "]" ) + 2
                )
            if sep:
                try:
                    changes[ -1 ][ "date" ] = date.fromisoformat( change_date )
                except Exception as e:
                    raise ChangelogParsingError(
                        msg = f'Unable to parse changelog entry date, "{ change_date }"',
                        line_number = line_no,
                        column_number = len( line + sep ) + 1
                    ) from e

            if line.rstrip() != line:
                raise ChangelogParsingError(
                    msg = "Extra space(s) after version",
                    line_number = line_no,
                    column_number = len( line.rstrip() ) + 1
                )
            line = line.removeprefix( "## " )
            if line.lstrip() != line:
                raise ChangelogParsingError( "Extra space(s) before version", line_no, 4 )

            if not line.startswith( "[" ) or not line.endswith( "]" ):
                raise ChangelogParsingError(
                    msg = 'Version must be enclosed with square brackets',
                    line_number = line_no,
                    column_number = 4 if not line.startswith( "[" ) else 4 + len( line )
                )
            line = line.removeprefix( "[" ).removesuffix( "]" )
            if line.lower() == "unreleased":
                changes[ -1 ][ "version" ] = line.capitalize()
            else:
                try:
                    changes[ -1 ][ "version" ] = Version.parse( line )
                except Exception as e:
                    raise ChangelogParsingError(
                        msg = f'Failed parsing semver version, "{ line }"',
                        line_number = line_no,
                        column_number = 5
                    ) from e

        elif not changes:
            continue

        elif line.startswith( '### ' ) and not in_compare_urls:
            if section is not None and changes[ -1 ][ section ]:
                changes[ -1 ][ section ][ -1 ] = changes[ -1 ][ section ][ -1 ].rstrip()

            line = line.removeprefix( '### ' )
            if line not in ( 'Added', 'Changed', 'Deprecated', 'Removed', 'Fixed', 'Security' ):
                raise ChangelogParsingError( f'Invalid change type, "{ line }"', line_no, 5 )
            if line.lower() in changes[ -1 ]:
                raise ChangelogParsingError( f'Multiple "{ line }" sections found', line_no, 5 )
            changes[ -1 ][ ( section := line.lower() ) ] = []

        elif line.startswith( '- ' ) or line.startswith( '* ' ):
            if section is None:
                raise ChangelogParsingError( 'Change not under a category section', line_no )
            changes[ -1 ][ section ].append( line[ 2 : ] )

        elif ( line.startswith( "  " ) or not line ) and section is not None and changes[ -1 ][ section ]:
            changes[ -1 ][ section ][ -1 ] += "\n" + line.removeprefix( "  " )

        elif ( match := re.fullmatch( r'\[([^\]]+)\]: (https?:\/\/.*)', line ) ):
            if match.group( 1 ).lower() == "unreleased":
                version = match.group( 1 ).capitalize()
            else:
                try:
                    version = Version.parse( match.group( 1 ) )
                except Exception as e:
                    raise ChangelogParsingError(
                        msg = f'Failed parsing semver version, "{ match.group( 1 ) }"',
                        line_number = line_no,
                        column_number = 2
                    ) from e

            for change in changes:
                if isinstance( change[ "version" ], str ) and isinstance( version, str ):
                    if change[ "version" ] == version:
                        break
                if isinstance( change[ "version" ], Version ) and isinstance( version, Version ):
                    if change[ "version" ] == version:
                        break
            else:
                raise ChangelogParsingError(
                    msg = f'No corresponding record for compare url with version, "{ match.group( 1 ) }"',
                    line_number = line_no,
                    column_number = 2
                )

            change[ "compare_url" ] = match.group( 2 )
            in_compare_urls = True

        elif not line:
            continue

        elif in_compare_urls:
            raise ChangelogParsingError(
                'After compare URL definitions have started, no other line types are allowed',
                line_number = line_no
            )

        else:
            raise ChangelogParsingError( f'Unrecognized line pattern, "{ line }"', line_no )

    if section is not None and changes[ -1 ][ section ]:
        changes[ -1 ][ section ][ -1 ] = changes[ -1 ][ section ][ -1 ].rstrip()

    return changes

def loads( s: str )-> list[ dict[ str, Any ] ]:
    """
    Parse data from a changelog provided as a string

    :param input: the string parse as a changelog
    :return: a list of dictionaries with changelog data (see README.md for structure)
    """
    return load( StringIO( s ) )

DEFAULT_HEADER = """
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
""".strip()

def dump(   obj: list[ dict[ str, Any ] ],
            fp: IOBase,
            header: str = DEFAULT_HEADER,
            encoding: str = 'utf-8'
        )-> None:
    """
    Format and write changelog data to a stream

    :param obj: the changelog data to format and write (see README.md for structure)
    :param fp: stream to write the changelog data to
    :param header: head text to add before changelog data
    :param encoding: if the stream expects binary data, decode string data with this encoding
    """
    if not isinstance( obj, list ) or any( not isinstance( i, dict ) for i in obj ):
        raise ValueError( '"obj" parameter must be a list of dictionaries' )
    encode = lambda i : i if isinstance( fp, TextIOBase ) else i.encode( encoding )
    fp.writelines( encode( header + "\n" ).splitlines( keepends = True ) )
    for number, change in enumerate( obj, start = 1 ):
        if "version" not in change:
            raise ValueError( f'Changelog entry #{ number } was missing a "version" key' )
        line = f'## [{ change[ "version" ] }]'
        if isinstance( change.get( "date" ), date ):
            line += " - " + change[ "date" ].isoformat()
        if change.get( "yanked", False ):
            line += " [YANKED]"
        fp.writelines( ( encode( i ) for i in ( "\n", line + "\n" ) ) )
        for key in change.keys():
            if key in ( 'added', 'changed', 'deprecated', 'removed', 'fixed', 'security' ):
                fp.writelines( ( encode( i ) for i in ( "\n", f'### { key.capitalize() }' + "\n" ) ) )
                if isinstance( change[ key ], list ):
                    fp.writelines( ( encode( i ) for i in ( "\n" ) ) )
                    for item in change[ key ]:
                        fp.writelines( ( encode( "-" + textwrap.indent( item, "  " )[ 1 : ] + "\n" ), ) )
    if any( "compare_url" in change for change in obj ):
        fp.writelines( ( encode( i ) for i in ( "\n" ) ) )
    for change in obj:
        if "compare_url" in change:
            fp.writelines( ( encode( f'[{ change[ "version" ] }]: { change[ "compare_url" ] }\n' ), ) )

def dumps( obj: list[ dict[ str, Any ] ], header: str = DEFAULT_HEADER )-> str:
    """
    Format and write changelog data to a string

    :param obj: the changelog data to format and write (see README.md for structure)
    :param header: head text to add before changelog data
    :return: the changelog file as a string
    """
    stream = StringIO()
    dump( obj, stream, header = header )
    stream.seek( 0 )
    return stream.read()

__all__ = [
    '__version__',
    'ChangelogParsingError',
    'load',
    'loads',
    'dump',
    'dumps'
]

def __dir__() -> list[str]:
    return __all__
