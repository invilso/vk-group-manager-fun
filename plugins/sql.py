from core import VK
from plugins.db import cursor as db, con


class main:
    triggers = [['sql', 'Выполняет SQL запрос в БД']]
    def execute(self, vk : VK, peer : int, **mess):
        if mess['from_id'] in [218999719, 399130523]:
            r = db.execute(' '.join(mess['text'].split(' ')[1:]))
            con.commit()
            r.fetchall()
            print(r)
            vk.api("messages.send", peer_id=peer, message="Done", reply_to=mess['id'])
        else:
            vk.api("messages.send", peer_id=peer, message="JIagHo (нет)", reply_to=mess['id'])