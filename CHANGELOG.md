# Changelog

We are currently working on porting this changelog to the specifications in
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## Version 1.5.4 - Unreleased

### Added:
* `set_overlaps` will now count duplicate values if non-sets are given as input
* Add `WarningsWithTracebacks`. 

### Fix:
* Handle embed with PEP667 changes in Python 3.13


## Version 1.5.3 - Released 2024-09-23

### Added:
* Pint CLI can now handle "GB", "GiB" for gigabytes and gibibytes as well as other short common byte aliases.

### Fixed:
* Pandas deprecation

### Changed:
* Remove 3.6 and 3.7 from availpkg tables

## Version 1.5.2 - Released 2024-05-31 

### Added
* Ported `kwutil.datetime`, `kwutil.timedelta`, and `kwutil.ensure_rng`
* Added features to pyversion CLI

### Changed
* Change default of dirstats `parse_content` to False.


## Version 1.5.1 - Released 2024-02-10 

### Added

* Add `parse` backend to Pattern

### Changed

* Moved `DirectoryWalker` to a top-level class
* Changed `DirectoryWalker` `block_dnames` to `exclude_dnames`
* Changed `DirectoryWalker` `block_fnames` to `exclude_fnames`

## Version 1.5.0 - Released 2024-01-23 

### Added

* Add `xdev.snapshot`
* Add attributes `file_paths` and `dir_paths` to `DirectoryWalker`.
* Add `ignore_empty_dirs` argument to `DirectoryWalker`.

### Fixed:

* Fixed issue in `DirectoryWalker` with rich links.


## Version 1.4.0 - Released 2023-08-18 

### Added
* Add dirstats CLI
* Add dirblocklist to sed CLI

### Fixed

* Fixed issue in availpkg
* bug in editfile
* bug in find CLI dirblocklist


### Changed

* `tree_repr` now uses dirstats as the backend.


## Version 1.3.3 - Released 2023-06-14 

### Added

* Add `editfile` to the xdev CLI

### Changed

* Support more default editors in `editfile`.
* Update format quotes to parso.
* Lower numpy requirement.
* Update scriptconfig requirement.


## Version 1.2.0 - Released 2023-04-04 

### Added
* `before_embed` callback to EmbedOnException

### Changed
* Switched to scriptconfig ModalCLI
* `xdev.embed` now stops any rich live context that may running.
* Switch default backend of format-quotes from redbaron to parso


## Version 1.1.1 - Released 2023-02-06 

### Added
* `pyversion` cli
* `pyfile` cli
* `max_depth` to `xdev.tree_repr` and corresponding CLI.
* Added initial experimental port of the `available_package_versions` script


### Changed
* More / cleaner docs in CLI tools.
* Expose `freshpyenv.sh` as an xdev CLI program.


## Version 1.1.0 - Released 2023-01-13 

### Added
* `tree` CLI
* `pint` CLI
* `modpath` CLI


## Version 1.0.0 - Released 2022-09-09 

### Added: 
* experimental `xdev doctypes`
* experimental `freshpyenv.sh` script


### Changed:
* Added type stubs
* Modified signature of `find` and `tree_repr`
* xcookie module structure
* `tree_repr` now uses rich and has more features

### Fixed:
* StopIteration issue in InteractiveIter


## Version 0.3.1 - Released 2022-03-26

### Fixed
* Fixed incorrect usage of deprecated parameter in ubelt


## Version 0.3.0 - Released 2022-03-25

### Changed

* Dropped Support for Python < 3.6

### Added

* Added `xdev.patterns` to abstract away regex vs glob style patterns
* Added `xdev.regex_builder` for building regular expressions
* Initial CLI with `sed`, `grep`, `find`, and `codeblock` support
* Can now specify `XDEV_PROFILE` environment variable to get profiling enable instead of using `--profile` on the command line.


## Version 0.2.4 - Released 2021-10-06
* `profile_now`  will now print results even if there is an exception.
* Add experimental `autojit`
* Add experimental `format_quotes`


## Version 0.2.3 - Released 2021-03-15

### Added
* Added `sedfile` and `grepfile`.


## Version 0.2.2 - Released 2021-01-21

### Added
* Added `nested_type`
* Added `difftext`


## Version 0.0.1 - Released 2018-11-08

### Added
* Initial version
* Added auto-generation imports
* Added `embed`
* Added `embed_on_exception`
* Added `fix_embed_globals`
* Added `InteractiveIter`
