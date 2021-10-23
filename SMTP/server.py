import smtpd
import email

from .database import db
from .logging import logging

import asyncore
import threading

from datetime import datetime

class Server(smtpd.SMTPServer):

    def __init__(self, localaddr, remoteaddr):
        smtpd.SMTPServer.__init__(self, localaddr, remoteaddr)
        
    def process_message(self, peer, mailfrom, rcpttos, data, mail_options=None, rcpt_options=None):
        try:
            prased = email.message_from_string(data.decode())
        except Exception:
            prased = email.message_from_string(data)

        if prased.is_multipart():
            for part in prased.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get("Content-Disposition"))

                if ctype == "text/plain" and "attachment" not in cdispo:
                    payload = part.get_payload(decode=True)
                    break
        else:
            payload = prased.get_payload()

        temp_data = {
            "to": prased["to"],
            "from": prased["from"],
            "subject": prased["subject"]
        }

        try:
            temp_data["payload"] = payload.decode()
        except Exception:
            temp_data["payload"] = payload

        if "<" in temp_data["to"]:
            temp_data["to"] = temp_data["to"].split("<")[1].split(">")[0]

        if "<" in temp_data["from"]:
            temp_data["from"] = temp_data["from"].split("<")[1].split(">")[0]

        db.update_one({
            "username": temp_data["to"].split("@")[0]
        },
        {
            "$push": {
                "emails": {
                    "from": temp_data["from"],
                    "to": temp_data["to"],
                    "content_type": prased.get_content_type(),
                    "subject": prased["subject"],
                    "body": temp_data["payload"],
                    "original": data,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        })

        logging.info("Received data from %s" % (data["from"]))

def run(host = "0.0.0.0", port = 25):
    server = Server((host, port), None)
    threading.Thread(target=asyncore.loop, daemon=True).start()
    logging.info("The smtp server has started!")
