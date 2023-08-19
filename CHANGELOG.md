# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.6] - 2023-08-19

### Added

- `dump` and `dumps` examples

## [0.0.5] - 2023-08-06

### Fixed

- Schema should be a list, not an object

## [0.0.4] - 2023-08-06

### Changed

- Case insensitive "unreleased" version value to fixed case `Unreleased`

### Added

- `dump` and `dumps` functions

## [0.0.3] - 2023-08-01

### Fixed

- Error message regarding version/data separation in titles
- A few line/column numbering mismatches

## [0.0.2] - 2023-07-31

### Changed

- `*_no` ChangelogParsingError properties to `line_number` and `column_number`

## [0.0.1] - 2023-07-28

### Fixed

- Some links

## [0.0.0] - 2023-07-28

### Added

- `load` / `loads` functions to convert a CHANGELOG.md to a python object
- `ChangelogParsingError` exception to specify line/column of parsing problems