from core import VK
from plugins.db import cursor as db, con
import config, datetime, time

def date(unixtime, format = '%d.%m.%Y %H:%M:%S'):
    d = datetime.datetime.fromtimestamp(unixtime)
    return d.strftime(format)

def getDayCase(num):
    if str(num)[-1] == "1": return "день"
    elif int(str(num)[:1]) in range(5,10) or str(num)[-1] == "0": return "дней"
    else: return "дня"

def findModer(moders, id):
    for moder in moders:
        if moder[0] == id:
            return moder
    return None

class main:
    triggers = [['daycount', 'Позволяет запустить подсчет, в случае, если автоматический не сработал']]
    
    def count(self, vk : VK, peer, test = False):
        '''Подсчёт'''
        moders = db.execute("SELECT * FROM moders").fetchall()
        dbvac = db.execute("SELECT * FROM vacation").fetchall()
        vac = [id[0] for id in dbvac]
        moders_days = {}
        for moder in moders:#Заполняем кто сколько дней не постил. Инфа из базы
            moders_days[moder[0]] = moder[2]

        posts = vk.api("wall.get", count=50, owner_id=0-config.GROUP_ID)

        ts = int(time.time())-24*60*60

        noauthor = 0
        creators = {}
        count = 0
        for post in posts['items']:
            if post['date'] > ts:
                count += 1
                if 'created_by' not in post:
                    noauthor += 1
                    continue
                if post['created_by'] not in creators:
                    creators[post['created_by']] = 1
                else:
                    creators[post['created_by']] += 1
        
        for moder in moders_days:
            if moder not in creators and moder not in vac:
                moders_days[moder] += 1
                if not test:
                    db.execute(f"UPDATE moders SET days_without_posts = {moders_days[moder]} WHERE vk_id = {moder}")
            else:
                moders_days[moder] = 0
                if not test:
                    db.execute(f"UPDATE moders SET days_without_posts = 0 WHERE vk_id = {moder}")

        for creator in creators:
            if not test:
                db.execute("INSERT OR IGNORE INTO counter(vk_id) VALUES(?)", (creator,))
                db.execute("UPDATE counter SET posts = posts + "+str(creators[creator])+" WHERE vk_id = ?", (creator,))
        
        mydate = date(time.time()-500, "%d.%m.%Y")
        result = "╔══════"+mydate+"══════\n"
        if test: result += "-------->TEST MODE<---------\n"
        result += f"║ > Всего опубликовано постов [{count}]:\n"
        result +=  "║*********************************\n"

        names = vk.api("users.get", user_ids=','.join(map(str, creators)))
        for name in names:
            result += f"║{name['first_name']} {name['last_name']} - {creators[name['id']]}\n"
        result +=  "║*********************************\n"
                
        result += "║ > Не было постов от: \n"
        result +=  "║*********************************\n"


        not_post_ids = []
        for moder in moders_days:
            if moders_days[moder] != 0:
                not_post_ids.append(moder)

        not_post_names = vk.api("users.get", user_ids=','.join(map(str, not_post_ids)), name_case="gen")
        for name in not_post_names:
            result += f"║{name['first_name']} {name['last_name']} - {moders_days[name['id']]} {getDayCase(moders_days[name['id']])}\n"

        result +=  "║*********************************\n"
        result +=  "║ > Статистика модераторов:\n"
        result +=  "║*********************************\n"
        result += f"║Всего модераторов: {len(moders_days)}\n"
        result += f"║Не рабочих: {len(not_post_ids)}\n"
        result += f"║Сегодня делали посты: {len(creators)}\n"
        result += f"║В отпуске: {len(vac)}\n"
        result +=  "║*********************************\n"
        if len(vac) > 0:
            result +=  "║ > Модераторы в отпуске:\n"
            result +=  "║*********************************\n"

            vac_end = []
            for u in dbvac:
                print(u)
                if u[2] == mydate:
                    vac_end.append(u[0])
            try: 
                vac_names = vk.api("users.get", user_ids=','.join(map(str, vac)))
                for name in vac_names:
                    if name['id'] in vac_end:
                        result += f"║{name['first_name']} {name['last_name']} [id{name['id']}|ВЫПИСАН ИЗ ОТПУСКА]\n"
                    else:
                        result += f"║{name['first_name']} {name['last_name']}\n"
            except TypeError:
                pass
                
            if len(vac_end) > 0:
                for id in vac_end:
                    db.execute("DELETE FROM vacation WHERE vk_id = ?", (id,))

        result += "╚══════════════════"

        con.commit()
        vk.api("messages.send", peer_id=peer, message=result)

    def execute(self, vk : VK, peer, **mess):
        userinfo = db.execute("SELECT * FROM admins WHERE vk_id = ?", (mess['from_id'],))
        if len(userinfo.fetchall()) == 1:
            if len(mess['text'].split(' ')) > 1 and mess['text'].split(' ')[1] == "test":
                self.count(vk, config.PEER_ADD_NUM + config.CONVERSATIONS['flood'], True)
            else:
                self.count(vk, config.PEER_ADD_NUM + config.CONVERSATIONS['new'])
        else:
            vk.api("messages.send", peer_id=peer, reply_to=mess['id'], message="[BOT]\nВы не можете использовать эту команду")

if __name__ == "__main__":
    main.count(VK(config.TOKEN), config.PEER_ADD_NUM + config.CONVERSATIONS['new'])