# SPDX-License-Identifier: MIT

import pytest
import os
from typing import Iterable, Any

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

class FakeIOObject:
    def __init__( self, readline_yields: Iterable[ Any ] ):
        self.readline_yields = readline_yields
        self.yield_on = 0

    def readline( self ):
        if len( self.readline_yields ) <= self.yield_on:
            raise StopIteration
        self.yield_on += 1
        return self.readline_yields[ self.yield_on - 1 ]
    
@pytest.fixture
def numerical_stream():
    return FakeIOObject( ( 1, ) )

@pytest.fixture
def non_utf8_stream():
    return FakeIOObject( ( "𐐷".encode( "utf-16" ), ) )