# SPDX-License-Identifier: MIT

import pytest
import os

@pytest.fixture
def projects_path():
    return os.path.realpath( os.path.join( __file__, "..", "projects" ) )

def generate_changelog_path_fixture( project_name ):
    @pytest.fixture
    def fixture( projects_path ):
        return os.path.join( projects_path, project_name, "CHANGELOG.md" )
    return fixture

for project_name in os.listdir( os.path.realpath( os.path.join( __file__, "..", "projects" ) ) ):
    fixture_prefix = f'project_{ project_name.replace( "-", "_" ) }'
    globals()[ f'{ fixture_prefix }_changelog_path' ] = generate_changelog_path_fixture( project_name )
