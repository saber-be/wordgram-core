from kafka import KafkaProducer, KafkaConsumer
# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = 'kafka:9092'
KAFKA_TOPIC = 'test_topic'
TOPIC_FETCH_FROM_INSTAGRAM = 'fetch_from_instagram'


class KafkaService:
    def __init__(self):
        pass
    def kafka_producer(self):
        return KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    def kafka_consumer(self,topic:str, group_id = None):
        return KafkaConsumer(topic,
                             group_id = ( group_id if group_id else topic ),
                             bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                             auto_offset_reset='earliest')