## [0.2.0] - not yet released

### Added

- `--line_numbers` command line option to show line numbers in the merged output
- `--encoding` command line argument to override system default encoding when reading files
- `--start` and `--end` command line arguments to specify start and end timestamps to select a
  specific time window from the merged logs
- support for direct merging of gzip-encoded files (such as `z.log.gz`)
- support for log timestamps with delimiting "T" between date and time
- support for log timestamps that are seconds (int or float) or milliseconds since epoch
- CHANGELOG.md file


## [0.1.0] - 2023-09-09

### Added

- Initial release functionality to merge multiple log files.
- Merged results can be displayed in tabular output, CSV, or in interactive terminal browser.
- Interactive browser will use the screen width by default, or accept a command-line argument.

[0.2.0]: https://github.com/ptmcg/log_merger/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ptmcg/log_merger/releases/tag/v0.1.0