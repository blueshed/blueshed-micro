Mongo
=====

Example of the blueshed.micro Server using Motor to connect to Mongodb.

The context links to mongodb via motor

.. code-block:: python

	from blueshed.micro.utils.base_context import BaseContext
	from blueshed.micro.orm import mongo_connection
	
	
	class Context(BaseContext):
	    '''
	        Extend Base context to include a Mongodb client
	    '''
	
	    @property
	    def motor(self):
	        return mongo_connection.client()


The project is saved to a collection and the result
broadcast to all clients.

.. code-block:: python

	from tornado import gen
	
	
	@gen.coroutine
	def save_project(context: 'micro_context', project: dict) -> dict:
	    ''' upserts a project to mongodb '''
	
	    # validate input
	    if not type(project) is dict:
	        raise Exception("argument project not a dict type")
	    assert project.get("title"), 'title required'
	
	    # connect to db
	    db = context.motor
	
	    # upsert
	    result = yield db.project_collection.update({"id": project["id"]},
	                                                project,
	                                                upsert=True)
	
	    if result.get('ok') is not 1:
	        raise Exception(result)
	
	    if result.get('updatedExisting') is True:
	        context.broadcast("project-changed", project)
	    else:
	        project["_id"] = result.get('upserted')
	        context.broadcast("project-added", project)
	    return str(result)


The server is configured like this:

.. code-block:: python

  from tornado.options import options
  import tornado.ioloop
  import tornado.web
  import logging

  from blueshed.micro.utils.service import Service
  from blueshed.micro.orm.mongo_connection import db_init
  from blueshed.micro.utils.utils import url_to_ws_origins
  from blueshed.micro.web.rpc_websocket import RpcWebsocket
  from blueshed.micro.web.rpc_handler import RpcHandler

  from modeling.config import load_config
  from modeling.actions.context import Context
  from modeling import actions


  def main():
      load_config("dev.env")

      if options.MONGODB_URI:
          db_init(options.MONGODB_URI)

      http_origins = options.CORS_URLS
      ws_origins = [url_to_ws_origins(u) for u in http_origins]

      handlers = [
          (r"/websocket", RpcWebsocket, {
              'ws_origins': ws_origins
          }),
          (r"/api(.*)", RpcHandler, {
              'http_origins': http_origins,
              'ws_url': options.WS_URL
          }),
          (r"/(.*)", tornado.web.StaticFileHandler, {
              "path": "." if options.DEBUG else "dist",
              "default_filename": "index.html"
          })
      ]
      settings = {
          'cookie_name':   options.COOKIE_NAME,
          'cookie_secret': options.COOKIE_SECRET,
          'services':      Service.describe(actions),
          'micro_context': Context,
          'allow_exception_messages': options.DEBUG,
          'gzip':          True,
          'debug':         options.DEBUG
      }

      app = tornado.web.Application(handlers, **settings)
      app.listen(options.PORT)

      logging.info("listening on port %s", options.PORT)
      if options.DEBUG:
          logging.info("running in debug mode")

      tornado.ioloop.PeriodicCallback(
          RpcWebsocket.keep_alive, 30000).start()

      tornado.ioloop.IOLoop.current().start()


  if __name__ == "__main__":
      main()
