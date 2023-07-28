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
     "type": "object",
     "properties": {
       "version": {
         "OneOf": [ {
           "const": "Unreleased",
           "description": "Case Insensitive"
         }, {
           "type": "semver.Version",
           "description": "Python object from https://pypi.org/project/semver/"
         } ]
       },
       "date": {
         "OneOf": [ {
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
     "additionalProperties": false,
     "$defs": {
       "change_list": {
         "type": "array",
         "items": { "type": "string" }
       }
     }
   }
   ```
