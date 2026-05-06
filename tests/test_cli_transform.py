"""Tests for envoy_lite.cli_transform."""
import io
import textwrap

import pytest

from envoy_lite.cli_transform import build_transform_parser, cmd_transform


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(textwrap.dedent("""\
        GREETING=hello
        NAME=world
        SECRET=  padded  
    """))
    return str(p)


def _make_args(env_file, transformers, keys=None, dry_run=False):
    parser = build_transform_parser()
    argv = ["-f", env_file]
    for t in transformers:
        argv += ["-t", t]
    if keys:
        for k in keys:
            argv += ["-k", k]
    if dry_run:
        argv.append("--dry-run")
    return parser.parse_args(argv)


class TestBuildTransformParser:
    def test_returns_parser(self):
        p = build_transform_parser()
        assert p is not None

    def test_defaults(self):
        p = build_transform_parser()
        args = p.parse_args([])
        assert args.file == ".env"
        assert args.transformers == []
        assert args.keys is None
        assert args.dry_run is False


class TestCmdTransform:
    def test_upper_all_keys(self, env_file):
        args = _make_args(env_file, ["upper"])
        out = io.StringIO()
        rc = cmd_transform(args, out=out)
        assert rc == 0
        output = out.getvalue()
        assert "GREETING=HELLO" in output
        assert "NAME=WORLD" in output

    def test_strip_selected_key(self, env_file):
        args = _make_args(env_file, ["strip"], keys=["SECRET"])
        out = io.StringIO()
        rc = cmd_transform(args, out=out)
        assert rc == 0
        output = out.getvalue()
        assert "SECRET=padded" in output
        # Other keys should be unchanged
        assert "GREETING=hello" in output

    def test_missing_file_returns_1(self, tmp_path):
        parser = build_transform_parser()
        args = parser.parse_args(["-f", str(tmp_path / "nope.env"), "-t", "upper"])
        err = io.StringIO()
        rc = cmd_transform(args, err=err)
        assert rc == 1
        assert "not found" in err.getvalue()

    def test_no_transformers_returns_1(self, env_file):
        parser = build_transform_parser()
        args = parser.parse_args(["-f", env_file])
        err = io.StringIO()
        rc = cmd_transform(args, err=err)
        assert rc == 1
        assert "transformer" in err.getvalue()

    def test_unknown_transformer_returns_1(self, env_file):
        args = _make_args(env_file, ["does_not_exist"])
        err = io.StringIO()
        rc = cmd_transform(args, err=err)
        assert rc == 1
        assert "error" in err.getvalue()

    def test_output_is_sorted(self, env_file):
        args = _make_args(env_file, ["lower"])
        out = io.StringIO()
        cmd_transform(args, out=out)
        lines = [l for l in out.getvalue().splitlines() if l]
        keys = [l.split("=")[0] for l in lines]
        assert keys == sorted(keys)
