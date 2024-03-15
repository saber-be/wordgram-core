from kafka import KafkaProducer, KafkaConsumer
# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = 'kafka:9092'
KAFKA_TOPIC = 'test_topic'

class KafkaService:
    def __init__(self):
        pass
    def kafka_producer(self):
        return KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    def kafka_consumer(self, group_id):
        return KafkaConsumer(KAFKA_TOPIC,
                             group_id=group_id,
                             bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                             auto_offset_reset='earliest')