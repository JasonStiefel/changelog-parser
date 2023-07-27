import changelog

def test_basic( project_basic_changelog_path ):
    with open( project_basic_changelog_path, "rb" ) as fp:
        inst = changelog.load( fp )
