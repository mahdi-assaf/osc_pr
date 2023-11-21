from json import load
from pymongo import MongoClient
from pathlib import Path
import datetime
from re import IGNORECASE, compile
from bson.objectid import ObjectId

# MONGO_HOST = "192.168.51.45"
MONGO_HOST = "localhost"
MONGO_PORT = "27017"
MONGO_DB = "olc"
MONGO_USER = "root"
MONGO_PASS = "example"

root = Path(__file__).parent


class Database:
    def __init__(self, database=MONGO_DB, db_name="test"):

        uri = "mongodb://{}:{}@{}:{}/{}?authSource=admin".format(MONGO_USER, MONGO_PASS, MONGO_HOST, MONGO_PORT,
                                                                 database)
        client = MongoClient(uri)
        self._db = client[db_name]


    def save_line(self, line):
        olc = self._db.olc
        post_id = olc.insert_one(line).inserted_id
        return post_id

    def save_ber(self, cassini_telemetry):
        ber = self._db.ber
        post_id = ber.insert_one(cassini_telemetry).inserted_id
        return post_id

    def get_ber(self, idx):
        ber = self._db.ber
        return ber.find_one({"_id": idx})

    def save_amp_telemetry(self, amp_telemetry):
        amplifier = self._db.amplifier
        post_id = amplifier.insert_one(amp_telemetry).inserted_id
        return post_id

    def save_ocm_telemetry(self, ocm_telemetry):
        ocm = self._db.ocm
        post_id = ocm.insert_one(ocm_telemetry).inserted_id
        return post_id

    def save_osa_telemetry(self, osa_telemetry):
        osa = self._db.osa
        post_id = osa.insert_one(osa_telemetry).inserted_id
        return post_id

    def save_time(self, time_telemetry):
        time = self._db.time
        post_id = time.insert_one(time_telemetry).inserted_id
        return post_id

    def find_path(self, sub_path):
        logger = self._db.logger
        regx = compile("^.*" + sub_path + ".*", IGNORECASE)
        mon_paths = logger.find({"path": regx})
        paths = []
        for path in mon_paths:
            paths.append(path)
        return paths

    def delete_path_from_id(self, _id):
        logger = self._db.logger
        logger.delete_one({'_id': ObjectId(_id)})
        return _id

    def save_spectral_info(self):
        print("Saving spectral info to db")
        spectral_info_db = self._db.spectral_info
        with open("resources/triangular_network_launch_spectrum.json", "r") as read_file:
            spectral_info_json = load(read_file)
        spectral_info_db.update_one({'_id': 0}, {"$set": spectral_info_json}, upsert=True)
        return

    def get_spectral_info(self):
        spectral_info_db = self._db.spectral_info
        return spectral_info_db.find_one({"_id": 0})


if __name__ == "__main__":
    db = Database()
    ciao = {
        "test": 1
    }
    idx = db.save_ber(ciao)
    print(idx)
    data = db.get_ber(idx)

    print(data)
