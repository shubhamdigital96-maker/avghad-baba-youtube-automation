import os, sys; sys.path.insert(0, os.getcwd())
from modules.database import init_db, record_publication, is_topic_used

def test_duplicate_prevention():
    init_db()
    sample_topic = "कैलाश संहिता परीक्षण विषय 101"
    record_publication(sample_topic, "short", "Test Title", "vid123", "private")
    assert is_topic_used(sample_topic) is True
