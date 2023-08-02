import changelog
import pytest
import semver
from datetime import date

def test_example( project_example_changelog_path ):
    with open( project_example_changelog_path, "rb" ) as fp:
        changes = changelog.load( fp )

    assert len( changes ) == 15

    min_keys = { "version", "date", "yanked" }
    max_keys = min_keys | { "added", "changed", "depreciated", "removed", "fixed", "security", "compare_url" }
    for change in changes:
        assert min_keys <= change.keys() <= max_keys

    assert changes[ -2 ] == {
        "version": semver.Version( 0, 0, 2 ),
        "date": date( 2014, 7, 10 ),
        "yanked": False,
        "added": [ "Explanation of the recommended reverse chronological release ordering." ],
        "compare_url": "https://github.com/olivierlacan/keep-a-changelog/compare/v0.0.1...v0.0.2"
    }

@pytest.mark.parametrize(
    ( "changelog_contents", "error_message", "msg_line_no", "msg_col_no" ),
    [
        ( "## [1.1.1] - 2023-03-05 [YANKED] ", "Extra space(s) at end of line (at line 1, column 33)", 1, 33 ),
        ( "## [1.1.1] - 2023-03-05  [YANKED]", "Extra space(s) after date (at line 1, column 24)", 1, 24 ),
        ( "## [1.1.1] - 2023-03-05 [ASDF]", 'Unable to parse changelog entry date, "2023-03-05 [ASDF]"; '
            'Invalid isoformat string: \'2023-03-05 [ASDF]\' (at line 1, column 14)', 1, 14 ),
        ( "## [1.1.1] - 2023-03-05 ", "Extra space(s) at end of line (at line 1, column 24)", 1, 24 ),
        ( "## [1.1.1] - hjksdgfwiuehf", 'Unable to parse changelog entry date, "hjksdgfwiuehf"; '
            'Invalid isoformat string: \'hjksdgfwiuehf\' (at line 1, column 14)', 1, 14 ),
        ( "## [1.1.1] -  2023-03-05", "Extra space(s) before date (at line 1, column 14)", 1, 14 ),
        ( "## [1.1.1] 2023-03-05", 'Version and date must be separated by " - " (at line 1, column 11)', 1, 11 ),
        ( "## [1.1.1]  - 2023-03-05", "Extra space(s) after version (at line 1, column 11)", 1, 11 ),
        ( "## [1.1.1] ", "Extra space(s) at end of line (at line 1, column 11)", 1, 11 ),
        ( "## [1.1.1", "Version must be enclosed with square brackets (at line 1, column 10)", 1, 10 ),
        ( "## 1.1.1]", "Version must be enclosed with square brackets (at line 1, column 4)", 1, 4 ),
        ( "##  [1.1.1] - 2023-03-05", 'Extra space(s) before version (at line 1, column 4)', 1, 4 ),
        ( "## [asdfasdf]", 'Failed parsing semver version, "asdfasdf"; asdfasdf is not valid SemVer '
            'string (at line 1, column 5)', 1, 5 ),
        ( "## [Unreleased]\nasdf", 'Unrecognized line pattern, "asdf" (at line 2)', 2, None ),
        ( "## [Unreleased]\n### asdf", 'Invalid change type, "asdf" (at line 2, column 5)', 2, 5 ),
        ( "## [Unreleased]\n\n### asdf", 'Invalid change type, "asdf" (at line 3, column 5)', 3, 5 ),
        ( "## [Unreleased]\n\n- Change", 'Change not under a category section (at line 3)', 3, None ),
        ( "## [Unreleased]\n\n### Added\n\n### Added", 'Multiple "Added" sections found (at line 5, column 5)', 5, 5 ),
        ( '## [Unreleased]\n\n[1.1.1]: https://asdf', 'No corresponding record for compare url with version, '
            '"1.1.1" (at line 3, column 2)', 3, 2 ),
        ( '## [Unreleased]\n\n[1.a.1]: https://asdf', 'Failed parsing semver version, "1.a.1"; 1.a.1 is '
            'not valid SemVer string (at line 3, column 2)', 3, 2 ),
        ( '## [1.1.1]\n\n[1.1.1]: https://asdf\n\n## [Unreleased]', 'After compare URL definitions have started, '
            'no other line types are allowed (at line 5)', 5, None )
    ] )
def test_basic_error_line_patterns( changelog_contents, error_message, msg_line_no, msg_col_no ):
    try:
        changelog.loads( changelog_contents )
    except Exception as e:
        assert isinstance( e, changelog.ChangelogParsingError )
        assert str( e ) == error_message
        assert e.line_number == msg_line_no
        assert e.column_number == msg_col_no
    else:
        pytest.fail( "Loading CHANGELOG did not raise an exception" )

def test_dir():
    assert "__version__" in changelog.__dir__()

def test_invalid_streams( numerical_stream ):
    try:
        changelog.load( numerical_stream )
    except Exception as e:
        assert isinstance( e, changelog.ChangelogParsingError )
        assert str( e ) == 'Parameter\'s "readline" function call returned unreadable type, "int"'
        assert e.line_number is None
        assert e.column_number is None
    else:
        pytest.fail( "Loading invalid stream did not raise an exception" )

def test_non_utf_8_input_object( non_utf8_stream ):
    try:
        changelog.load( non_utf8_stream )
    except Exception as e:
        assert isinstance( e, changelog.ChangelogParsingError )
        assert str( e ) == ( 'Unable to decode line using encoding, "utf-8"; \'utf-8\' codec '
            'can\'t decode byte 0xff in position 0: invalid start byte (at line 1)' )
        assert e.line_number == 1
        assert e.column_number is None
    else:
        pytest.fail( "Loading non-utf-8 stream did not raise an exception" )