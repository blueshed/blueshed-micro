import pytest

from concurrent.futures.process import ProcessPoolExecutor
from urllib.parse import urlencode

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.concurrent import DummyExecutor
from tornado.websocket import websocket_connect

from blueshed.micro.utils.service import Service
from blueshed.micro.web.rpc_handler import RpcHandler
from blueshed.micro.orm import db_connection
from blueshed.micro.orm.orm_utils import drop_all, create_all, Base
from blueshed.micro.utils.executor import pool_init
from blueshed.micro.web.rpc_websocket import RpcWebsocket

from tests import actions
from tests.actions.context import Context
from tests.actions import model

pool_init(ProcessPoolExecutor(2))

application = tornado.web.Application([
        (r"/websocket", RpcWebsocket),
        (r"/(.*)", RpcHandler)
    ],
    services=Service.describe(actions),
    micro_context=Context,
    cookie_name='blueshed-test',
    cookie_secret='-it-was-a-dark-and-blueshed-night-',
    allow_exception_messages=True)


db_connection.db_init("mysql+pymysql://root:root@localhost:8889/test")
with db_connection.session() as session:
    drop_all(session)
create_all(Base, db_connection._engine_)
with db_connection.session() as session:
    session.add(model.User(name="admin", email="admin", password="admin"))
    session.commit()


@pytest.fixture
def app():
    return application


@pytest.mark.gen_test
def test_hello_world_get(http_client, base_url):
    response = yield http_client.fetch(base_url)
    print(response.headers)
    print(response.body)
    assert response.code == 200
    assert response.headers[
        "content-type"] == "application/json; charset=UTF-8"


@pytest.mark.gen_test
def test_hello_world_json(http_client, base_url):
    response = yield http_client.fetch(base_url + "/save_group",
                                       method="POST",
                                       headers={
                                           "content-type": "application/json; charset=UTF-8"
                                       },
                                       body='{ "name": "foobar1" }')
    assert response.code == 200
    assert response.headers[
        "content-type"] == "application/json; charset=UTF-8"
    result = json_decode(response.body)
    print(result)
    assert result.get('result')['name'] == 'foobar1'


@pytest.mark.gen_test
def test_hello_world_plain(http_client, base_url):
    response = yield http_client.fetch(base_url + "/save_group",
                                       method="POST",
                                       body=urlencode({"name": "foobar2"}))
    assert response.code == 200
    assert response.headers[
        "content-type"] == "application/json; charset=UTF-8"
    result = json_decode(response.body)
    print(result)
    assert result.get('result')['name'] == 'foobar2'


@pytest.mark.gen_test
def test_hello_world_login(http_client, base_url):
    response = yield http_client.fetch(base_url + "/login",
                                       method="POST",
                                       body=urlencode({"email": "admin", "password": "admin"}))
    assert response.code == 200
    assert response.headers[
        "content-type"] == "application/json; charset=UTF-8"
    print(dict(response.headers))
    assert response.headers.get("set-cookie").startswith(application.settings['cookie_name'])
    result = json_decode(response.body)
    print(result)
    assert result.get('result')['name'] == 'admin'


@pytest.mark.gen_test
def test_hello_world_filter(http_client, base_url):
    response = yield http_client.fetch(base_url + "/filter_groups",
                                       method="POST",
                                       headers={
                                           "content-type": "application/json; charset=UTF-8"
                                       },
                                       body='{ "term": "foobar" }')
    assert response.code == 200
    assert response.headers[
        "content-type"] == "application/json; charset=UTF-8"
    result = json_decode(response.body)
    print(result)
    assert len(result.get('result')) == 2


@pytest.mark.gen_test
def test_websocket(http_client, base_url):
    conn = yield websocket_connect(base_url.replace("http://","ws://") + "/websocket")
    conn.write_message(json_encode({'requests':[(1, 'filter_groups', {})]}))
    while True:
        msg = yield conn.read_message()
        if msg is None:
            break
        response = json_decode(msg)
        print(response)
        if response.get("id") == 1:
            assert response.get('status_code') == 200
            assert len(response.get('result')) == 2
            conn.write_message(json_encode({'requests': [(2, 'save_group', {'name': None})]}))
        elif response.get("id") == 2:
            assert response.get("error") is not None
            break


@pytest.mark.gen_test
def test_hello_world_inline(http_client, base_url):
    pool_init(None)
    response = yield http_client.fetch(base_url + "/filter_groups",
                                       method="POST",
                                       headers={
                                           "content-type": "application/json; charset=UTF-8"
                                       },
                                       body='{ "term": "foobar" }')
    assert response.code == 200
    assert response.headers[
        "content-type"] == "application/json; charset=UTF-8"
    result = json_decode(response.body)
    print(result)
    assert len(result.get('result')) == 2


@pytest.mark.gen_test
def test_hello_world_dummy(http_client, base_url):
    pool_init(DummyExecutor())
    response = yield http_client.fetch(base_url + "/filter_groups",
                                       method="POST",
                                       headers={
                                           "content-type": "application/json; charset=UTF-8"
                                       },
                                       body='{ "term": "foobar" }')
    assert response.code == 200
    assert response.headers[
        "content-type"] == "application/json; charset=UTF-8"
    result = json_decode(response.body)
    print(result)
    assert len(result.get('result')) == 2
