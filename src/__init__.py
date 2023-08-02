# SPDX-License-Identifier: MIT

__version__ = '0.0.3'

import re
from datetime import date
from semver import Version
from typing import ( Optional, Any )
from io import ( IOBase, StringIO )

class ChangelogParsingError( Exception ):
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
                    msg = f'Unable to decode line using encoding, "{ encoding }"; { e }',
                    line_number = line_no
                )
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
                        msg = f'Unable to parse changelog entry date, "{ change_date }"; { e }',
                        line_number = line_no,
                        column_number = len( line + sep ) + 1
                    )

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
            try:
                changes[ -1 ][ "version" ] = line if line.lower() == "unreleased" else Version.parse( line )
            except Exception as e:
                raise ChangelogParsingError( f'Failed parsing semver version, "{ line }"; { e }', line_no, 5 )

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
                version = match.group( 1 )
            else:
                try:
                    version = Version.parse( match.group( 1 ) )
                except Exception as e:
                    raise ChangelogParsingError(
                        msg = f'Failed parsing semver version, "{ match.group( 1 ) }"; { e }',
                        line_number = line_no,
                        column_number = 2
                    )

            for change in changes:
                if isinstance( change[ "version" ], str ) and isinstance( version, str ):
                    if change[ "version" ].lower() == version.lower():
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
                f'After compare URL definitions have started, no other line types are allowed',
                line_number = line_no
            )

        else:
            raise ChangelogParsingError( f'Unrecognized line pattern, "{ line }"', line_no )

    if section is not None and changes[ -1 ][ section ]:
        changes[ -1 ][ section ][ -1 ] = changes[ -1 ][ section ][ -1 ].rstrip()

    return changes

def loads( input: str )-> list[ dict[ str, Any ] ]:
    """
    Parse data from a changelog provided as a string

    :param input: the string parse as a changelog
    :return: a list of dictionaries with changelog data (see README.md for structure)
    """
    return load( StringIO( input ) )


__all__ = [
    '__version__',
    'ChangelogParsingError',
    'load',
    'loads'
]

def __dir__() -> list[str]:
    return __all__
