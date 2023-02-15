# Changelog

We are currently working on porting this changelog to the specifications in
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Version 1.2.0 - Unreleased

### Added
* `before_embed` callback to EmbedOnException

### Changed
* Switched to scriptconfig ModalCLI


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
