# changelog-parser
Yet another python changelog parser.
* Loads data from a [`CHANGELOG.md` file](https://keepachangelog.com/en/1.1.0/) using code like:
   ```python
   import changelog

   with open( "CHANGELOG.md", 'rb' ) as fp:
     changes = changelog.load( fp )
   ```
   or
   ```python
   import changelog

   with open( "CHANGELOG.md", 'r' ) as fp:
     changes = changelog.loads( fp.read() )
   ```
* Returns it in the following schema (some types are Python objects and not valid JSON schema):
   ```js
   {
     "$schema": "https://json-schema.org/draft-07/schema#",
     "title": "Loaded Changelog",
     "type": "array",
     "items": {
       "type": "object",
       "properties": {
         "version": {
           "oneOf": [ {
             "const": "Unreleased"
           }, {
             "type": "semver.Version",
             "description": "Python object from https://pypi.org/project/semver/"
           } ]
         },
         "date": {
           "oneOf": [ {
             "const": null
           }, {
             "type": "datetime.date",
             "description": "Python object from https://docs.python.org/3/library/datetime.html#date-objects; parsed using \"fromisoformat\""
           } ]
         },
         "yanked": {
           "type": "boolean"
         },
         "added": { "$ref": "#/$defs/change_list" },
         "changed": { "$ref": "#/$defs/change_list" },
         "depreciated": { "$ref": "#/$defs/change_list" },
         "removed": { "$ref": "#/$defs/change_list" },
         "fixed": { "$ref": "#/$defs/change_list" },
         "security": { "$ref": "#/$defs/change_list" },
         "compare_url": {
           "type": "string",
           "pattern": "^https?:\\/\\/.+"
         }
       },
       "required": [ "version", "date", "yanked" ],
       "additionalProperties": false
     },
     "$defs": {
       "change_list": {
         "type": "array",
         "items": { "type": "string" }
       }
     }
   }
   ```
* Dumps data, structured like that above, to a [`CHANGELOG.md` file](https://keepachangelog.com) using code like
   ```python
   import changelog
   import semver
   from datetime import date

   with open( "CHANGELOG.md", 'rb' ) as fp:
     changes = changelog.load( fp )

   changes.insert( 0, {
      "version": semver.Version( major = 0, minor = 0, patch = 6 ),
      "date": date.today(),
      "added": [ "`dump` and `dumps` examples" ]
   } )

   with open( "CHANGELOG.md", 'rb' ) as fp:
     changelog.dump( changes, fp )
   ```
   or
   ```python
   import changelog
   ...
   changelog_contents = changelog.dumps( changes )
   with open( "CHANGELOG.md", 'r' ) as fp:
     fp.write( changelog_contents )
   ```
