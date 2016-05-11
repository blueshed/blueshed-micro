from pkg_resources import resource_filename  # @UnresolvedImport
from blueshed.micro.utils import config
from tornado.options import options, define
import os
import subprocess

define("db_url", default="three")
define('PORT',
       default=8080,
       type=int,
       help='port to listen on')
define("CORS_URLS",
       default=["http://localhost:8080", "https://petermac.local:8080"],
       help="access from where",
       multiple=True,
       callback=lambda v: v.split(',') if isinstance(v, str) else v)


def get_db_url():
    config.load_config()
    if options.PORT == 80 and options.db_url == "four":
        os._exit(os.EX_OK)
    else:
        os._exit(os.EX_DATAERR)


def test_config():
    config.load_config()
    assert options["db_url"] == "three"
    assert options["PORT"] == 8080


def test_config_file():
    config.load_config(resource_filename("tests", "test.env"))
    assert options["db_url"] == "two"
    assert options["CORS_URLS"] == ['http://localhost:8888',
                                    'https://localhost:8843']


def test_config_env():
    os.environ["db_url"] = "one"
    os.environ["PORT"] = "8081"
    os.environ["CORS_URLS"] = "http://localhost:8888,https://localhost:8843"
    config.load_config()
    assert options["db_url"] == "one"
    assert options["PORT"] == 8081
    assert options["CORS_URLS"] == ['http://localhost:8888',
                                    'https://localhost:8843']


def test_config_command_line():
    args = [
        "/Users/peterb/eclipse/dev-351/bin/python",
        '-m', 'tests.test_config_utils',
        '--db_url=four']
    p = subprocess.run(args, env={"PORT": "80"})
    print(p.returncode)
    assert p.returncode == os.EX_OK


def test_config_command_line_default():
    args = [
        "/Users/peterb/eclipse/dev-351/bin/python",
        '-m', 'tests.test_config_utils']
    p = subprocess.run(args)
    print(p.returncode)
    assert p.returncode == os.EX_DATAERR


if __name__ == "__main__":
    get_db_url()
