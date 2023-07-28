import changelog
import pytest

def test_example( project_example_changelog_path ):
    with open( project_example_changelog_path, "rb" ) as fp:
        changes = changelog.load( fp )
    assert len( changes ) == 15
    min_keys = { "version", "date", "yanked" }
    max_keys = min_keys | { "added", "changed", "depreciated", "removed", "fixed", "security", "compare_url" }
    for change in changes:
        assert min_keys <= change.keys() <= max_keys

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
        ( "## [1.1.1] 2023-03-05", "Version must be enclosed with square brackets (at line 1, column 22)", 1, 22 ),
        ( "## [1.1.1]  - 2023-03-05", "Extra space(s) after version (at line 1, column 11)", 1, 11 ),
        ( "## [1.1.1] ", "Extra space(s) at end of line (at line 1, column 11)", 1, 11 ),
        ( "## [1.1.1", "Version must be enclosed with square brackets (at line 1, column 10)", 1, 10 ),
        ( "## 1.1.1]", "Version must be enclosed with square brackets (at line 1, column 4)", 1, 4 ),
        ( "## [asdfasdf]", 'Failed parsing semver version, "asdfasdf"; asdfasdf is not valid SemVer '
            'string (at line 1, column 5)', 1, 5 ),
        ( "## [Unreleased]\nasdf", 'Unrecognized line pattern, "asdf" (at line 2)', 2, None ),
        ( "## [Unreleased]\n### asdf", 'Invalid change type, "asdf" (at line 2, column 5)', 2, 5 ),
        ( "## [Unreleased]\n\n### asdf", 'Invalid change type, "asdf" (at line 3, column 5)', 3, 5 )
    ])
def test_basic_error_line_patterns( changelog_contents, error_message, msg_line_no, msg_col_no ):
    try:
        changelog.loads( changelog_contents )
    except Exception as e:
        assert isinstance( e, changelog.ChangelogParsingError )
        assert str( e ) == error_message
        assert e.line_no == msg_line_no
        assert e.column_no == msg_col_no
    else:
        pytest.fail( "Loading CHANGELOG did raise an exception" )
