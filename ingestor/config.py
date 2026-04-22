from pipeline.config import KafkaSettings, SnapshotSettings

KAFKA_SETTINGS = KafkaSettings.from_env()
SNAPSHOT_SETTINGS = SnapshotSettings.from_env()

KAFKA_BOOTSTRAP_SERVERS = KAFKA_SETTINGS.bootstrap_servers
KAFKA_USERNAME = KAFKA_SETTINGS.username
KAFKA_PASSWORD = KAFKA_SETTINGS.password
TEAM = KAFKA_SETTINGS.team
SNAPSHOT_BASE_PATH = SNAPSHOT_SETTINGS.base_path
