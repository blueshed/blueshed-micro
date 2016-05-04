from blueshed.micro.queue.pika_tool import PikaTool
import logging

LOGGER = logging.getLogger(__name__)


class PikaTopic(PikaTool):
    '''
        A simple broadcast and subscribe message pattern
        in AMQP using a fanout exchange type
    '''

    def __init__(self, amqp_url, broadcast_func, exchange, routing_key=''):
        PikaTool.__init__(self, amqp_url)
        self.EXCHANGE_TYPE = "fanout"
        self.EXCHANGE = exchange
        self.ROUTING_KEY = routing_key
        self._broadcast_func = broadcast_func

    def setup_queue(self, queue_name):
        logging.info('Declaring queue %s', queue_name)
        self._channel.queue_declare(self.on_queue_declareok, exclusive=True)

    def on_queue_declareok(self, method_frame):
        '''
            QUEUE get set to method_frame.method.queue
            our own personal queue
        '''
        self.QUEUE = method_frame.method.queue
        PikaTool.on_queue_declareok(self, method_frame)

    def on_message(self, unused_channel, basic_deliver, properties, body):
        '''
            handle message from topic
        '''
        logging.info('Received message # %s from %s: %s',
                     basic_deliver.delivery_tag, properties.app_id, body)
        if self._broadcast_func:
            self._broadcast_func(body)
        self.acknowledge_message(basic_deliver.delivery_tag)

    def post(self, msg):
        '''
            Submit message to topic
        '''
        if self._channel:
            self._channel.basic_publish(self.EXCHANGE,
                                        routing_key=self.ROUTING_KEY,
                                        body=msg)

    def connect(self):
        self._connection = super().connect()
