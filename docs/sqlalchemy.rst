SqlAchemy
=========

Example of the blueshed.micro Server using SQLAlchemy to connect to MySQL.

The model:

.. code-block:: python

	from blueshed.micro.orm.orm_utils import Base
	from sqlalchemy.sql.schema import Column
	from sqlalchemy.sql.sqltypes import Integer, String
	
	
	class User(Base):
	
	    id = Column(Integer, primary_key=True)
	    name = Column(String(128))
	    email = Column(String(128), unique=True)
	    password = Column(String(80))
	
	
	class Group(Base):
	
	    id = Column(Integer, primary_key=True)
	    name = Column(String(128), nullable=False)


The context class:

.. code-block:: python

	from blueshed.micro.orm import db_connection
	from blueshed.micro.utils.base_context import BaseContext
	
	
	class Context(BaseContext):
	    """ Extend BaseContext to include a db session """
	
	    @property
	    def session(self):
	        return db_connection.session()
	    
	    
The action for login:

.. code-block:: python

	from tests.actions import model
	
	
	def login(context: 'micro_context', email: str, password: str) -> dict:
	    ''' returns a user object on success '''
	    with context.session as session:
	        person = session.query(model.User).\
	            filter(model.User.email == email,
	                   model.User.password == password).\
	            first()
	        if person is None:
	            raise Exception(
	                "<strong>Failed</strong> Email or password incorrect!")
	        user = {
	            "id": person.id,
	            "email": person.email,
	            "name": person.name
	        }
	        context.set_cookie("current_user", user)
	        return user

	        
The Server:

.. code-block:: python

	import ProcessPoolExecutor
	import tornado.web
	from tornado.options import options, define
	
	from blueshed.micro.utils.config import load_config
	from blueshed.micro.orm import db_connection
	from blueshed.micro.utils.executor import pool_init_processes
	from blueshed.micro.utils.service import Service
	from blueshed.micro.web.rpc_websocket import RpcWebsocket
	from blueshed.micro.web.rpc_handler import RpcHandler
	
	from tests import actions
	from tests.actions.context import Context
	from tests.actions import model
	
	define('DEBUG', False, bool, help='run in debug mode')
	define('PORT', 8080, int, help='port to listen on')
	define("CLEARDB_DATABASE_URL",
       default='mysql://root:root@localhost:8889/test',
       help="database url")
	
	
	def make_app():
		return tornado.web.Application([
		        (r"/websocket", RpcWebsocket),
		        (r"/(.*)", RpcHandler)
		    ],
		    services=Service.describe(actions),
		    micro_context=Context,
		    cookie_name='<cookie-name>',
		    cookie_secret='<cookie-secret>',
		    allow_exception_messages=option.DEBUG,
		    debug=options.DEBUG)

	def main():
    	config.load_config(".env")
    	
	    db_url = heroku_db_url(options.CLEARDB_DATABASE_URL)
	    db_connection.db_init(db_url)
	    if options.DEBUG:
	        create_all(Base, db_connection._engine_)
	        
		pool_init_processes(2, options.DEBUG)
		
	    app = make_app()
	    app.listen(options.PORT)
	    logging.info('listening on port %s', options.PORT)
	    if options.DEBUG:
	        logging.info('running in debug mode')
	    tornado.ioloop.PeriodicCallback(
	        RpcWebsocket.keep_alive, 30000).start()
	    tornado.ioloop.IOLoop.current().start()
	
	
	if __name__ == '__main__':
	    main()
