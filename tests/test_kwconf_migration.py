def test_legacy_comma_list_cli_semantics():
    """Comma-separated CLI values remain structured after the kwconf port."""
    from xdev.cli.cli_formatter import CLIFormatterCLI
    from xdev.cli.main import XdevCLI

    expected_filters = {
        'include': ['a', 'b'],
        'exclude': ['x', 'y'],
        'dirblocklist': ['d1', 'd2'],
    }
    filter_argv = [
        '--include=a,b',
        '--exclude=x,y',
        '--dirblocklist=d1,d2',
    ]

    for cli_cls in [XdevCLI.SedCLI, XdevCLI.FindCLI]:
        config = cli_cls.cli(argv=filter_argv, strict=True)
        assert {key: config[key] for key in expected_filters} == expected_filters

    tree_config = XdevCLI.TreeCLI.cli(
        argv=['--dirblocklist=d1,d2'], strict=True
    )
    assert tree_config.dirblocklist == ['d1', 'd2']

    formatter_config = CLIFormatterCLI.cli(
        argv=['--output-type=yaml,dict'], strict=True
    )
    assert formatter_config.output_type == ['yaml', 'dict']


def test_kwconf_flag_and_counter_semantics():
    from xdev.cli.dirstats import DirectoryStatsCLI

    config = DirectoryStatsCLI.cli(
        argv=['-vv', '--no-ignore', '--no-parse-content'], strict=True
    )
    assert config.verbose == 2
    assert config.respect_gitignore is False
    assert config.parse_content is False


def test_dirstats_programmatic_comma_patterns():
    from xdev.cli.dirstats import DirectoryStatsCLI

    config = DirectoryStatsCLI.cli(
        argv=False, data={'exclude_fnames': 'one,two'}, strict=True
    )
    assert config.exclude_fnames[:2] == ['one', 'two']
