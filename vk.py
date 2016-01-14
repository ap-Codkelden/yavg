import  urllib.request, http.client, http.cookiejar, urllib.parse, getpass, datetime, sys, json, time, argparse, xml.etree.cElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlparse

__version__ = '0.2'

arg_parser = argparse.ArgumentParser()

arg_parser.add_argument('-uid', type=int, help='ID пользователя')
arg_parser.add_argument('-chatid', type=int, default=0, help='ID многопользовательского чата')
arg_parser.add_argument('-appid', default=4519325, type=int, help="ID приложения ВКонтакте")
arg_parser.add_argument('-authurl',  action="store_true", help="вывести URL запроса")
arg_parser.add_argument("-f", "--friends", action="store_true", help="только показать список друзей")
arg_parser.add_argument("-s", "--stat", action="store_true", help="Показывать количество сохраненных сообщений")
arg_parser.add_argument("-d", "--dialogs", action="store_true", help="сохранит информацию о последних 200 диалогах пользователя в файлы 'dialogs.txt' и 'dialogs.json'")
arg_parser.add_argument('-ascii',  action="store_true", help="При использовании опции -d сохранять JSON как файл ASCII")

class FormParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.params = {}
        self.url= None
        self.method = "GET"
        self.form_parsed = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs = dict((name.lower(), value) for name, value in attrs)
        if tag == "form":
            self.url = attrs["action"]
            if "method" in attrs:
                self.method = attrs["method"]
            
        elif tag == "input" and "type" in attrs and "name" in attrs:
            if attrs["type"] in ["hidden", "text", "password"]:
                self.params[attrs["name"]] = attrs["value"] if "value" in attrs else ""

    def handle_endtag(self, tag):
        if tag.lower() == "form":
            self.form_parsed = True

def GetToken(client_id, scope,  email, password):
    try:
        parser = FormParser()

        opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
                urllib.request.HTTPRedirectHandler())

        parser.feed(
            opener.open(
                "http://oauth.vk.com/oauth/authorize?" + \
                "redirect_uri=http://oauth.vk.com/blank.html&response_type=token&" + \
                "client_id=%s&scope=%s&display=wap" % (client_id, ",".join(scope))).read().decode()
            )
        
        parser.params['email'] = email
        parser.params['pass'] = password

        data = urllib.parse.urlencode(parser.params)
        bin_data = data.encode('ascii')
        response = opener.open(parser.url, bin_data)
        if args.authurl:
            print("\nURL получения прав/токена:\n", response.url)
        return dict(x.split('=') for x in response.url.split('#')[1].split('&'))
    except:
        raise

def CallVK(method_name, parameters, token):
    # https://api.vk.com/method/'''METHOD_NAME'''?'''PARAMETERS'''&access_token='''ACCESS_TOKEN'''
    time.sleep(0.78)
    parameters['access_token'] = token
    url = "https://api.vk.com/method/%s?%s" % (method_name, urllib.parse.urlencode(parameters)) 
    return json.loads(urllib.request.urlopen(url).read().decode())

def GetFriends(user_id):
    friends_list = CallVK('friends.get', {'user_id' : user_id, 'fields' : 'nickname'}, token)['response']
    return sorted(friends_list, key=lambda k: k['last_name'])

def ShowFriends(user_id):
    friends = GetFriends(user_id)
    for friend_info in friends:
        print(friend_info['uid'], friend_info['last_name'], friend_info['first_name'])

def GetMessages(uid, token, friends, chat):
    offset = 0
    history = []
    count = 1

    params = {'count': 200, 'rev': 1, 'offset': offset}
    if not chat:
        params['user_id'] = uid
    else:
        params['chat_id'] = chat

    while count>0:
        params['offset'] = offset
        time.sleep(0.5)
        h = CallVK('messages.getHistory', params, token)
        history.extend(h['response'][1:])
        count = len(h['response'][1:])
        offset+=200

    if not chat:
        uid=uid
        chat=False
    else:
        uid=history[0]['uid']
        chat=True
    GenerateXML(history, friends=friends, uid=uid, chat=chat,)


def GetUserById(uid, token):
    try:
        if uid > 0:
            vk_resp = CallVK('users.get', {'user_ids' : uid, 'fields' : 'sex'}, token)
            user = vk_resp['response'][0]
            return ''.join([ user['first_name'], ' ', user['last_name'] ])
        elif uid < 0:
            vk_resp = CallVK('groups.getById', {'group_ids' : abs(uid), 'fields' : 'city'}, token)
            group = vk_resp['response'][0]
            return ''.join([ 'Группа «', group['name'], '»' ])
        else:
            return 'Unknown obj.'
    except KeyError:
        if 'error' in vk_resp:
            print('\nОшибка ВКонтакте: ', vk_resp['error']['error_msg'])
            raise
        else:
            print('Ошибка обращения к элементу по ключу.')
            raise
    except:
        raise


def GetDialogs(ascii=ascii):
    dialogs_list = []
    count = -1
    offset = 0
    while len(dialogs_list)>count:
        d = CallVK('messages.getDialogs', {'preview_length' : 30, 'count' : 200, offset : offset}, token)
        count = len(d['response'])
        offset += 200
        dialogs_list.extend(d['response'][1:])
    dialogs_list = sorted(dialogs_list, key=lambda k: k['date'], reverse=True)
    with open('dialogs.json', 'w', encoding='utf-8') as outfile:
        json.dump(dialogs_list, outfile, ensure_ascii=ascii)
    u = ','.join([str(dialog['uid']) for dialog in dialogs_list])
    users_array = dict([ (user['uid'], ' '.join( [ user['last_name'], user['first_name']  ]) ) for user in CallVK('users.get', {'user_ids' : u}, token)['response'] ])
    try:
        with open('dialogs.txt','w',encoding='utf-8') as f:
            for dialog in dialogs_list:
                f.write(''.join(['\t'.join([users_array[dialog['uid']], str(dialog['uid']), UNIXTimeToString(dialog['date']), str(dialog['chat_id']) if 'chat_id' in dialog else '', dialog['body']]),'\n' ]))                
        print("Записано.")
    except:
        raise

def UNIXTimeToString(unixtime):
    return datetime.datetime.fromtimestamp(unixtime).strftime('%d-%m-%Y %H:%M:%S')

def Bytes2Kb(bytes):
    return ''.join(['~',str(round(bytes/1024, 2)), ' Кб'])

def GenerateXML(messages, friends, uid, chat=None,):
    # если это не чат, то будет использовано как имя 
    # собеседника, иначе будет использовано как имя создателя чата
    uname = GetUserById(uid, token)
    if chat:
        # словарь с участниками чата
        multi_user_chat_users = {}
        for message in messages:
            if message['uid'] not in multi_user_chat_users.keys():
                multi_user_chat_users[message['uid']] = GetUserById(message['uid'], token)
    counter = 0
    try:
        print('Генерируем XML...', end='')
        root = ET.Element("conversation")
        if args.stat:
            total_msg_cnt = len(messages)
        for message in messages:
            msg = ET.SubElement(root, "message")
            msg.set("datetime", UNIXTimeToString(message['date']))
            # 0 – полученное сообщение, 1 – отправленное сообщение, 2 - переслано
            msg.set("direction", '2' if (not 'out' in message) else str(message['out']))
            msg.set("author", ('Переслано' if (not 'out' in message) else ('Вы' if message['out'] == 1 else (uname if not chat else multi_user_chat_users[message['uid']]))))
            # print(message['body'].replace('<br>','\n'))
            msg.text =  message['body'].replace('<br>','\n')
            if 'attachment' in message:
                attachment_type = message['attachment']['type']
                attachment = ET.SubElement(msg, "attachment")
                attachment.set('type', attachment_type)
                if attachment_type == 'photo':
                    attachment.set('url',message['attachment']['photo']['src_big'])
                elif attachment_type == 'video':
                    attachment.text = message['attachment']['video']['title']
                    attachment.set('duration', str(message['attachment']['video']['duration']))
                    attachment.set('preview', message['attachment']['video']['image_big'])
                    desc = ET.SubElement(attachment, "description")
                    desc.text = (message['attachment']['video']['description'].replace('<br>','\n'))
                elif attachment_type == 'audio':
                    attachment.set('url', message['attachment']['audio']['url'])
                    attachment.set('performer', str(message['attachment']['audio']['performer']))
                    attachment.set('title', str(message['attachment']['audio']['title']))
                elif attachment_type == 'doc':
                    attachment.set('url', message['attachment']['doc']['url'])
                    attachment.set('size', Bytes2Kb(message['attachment']['doc']['size']))
                    attachment.set('ext', message['attachment']['doc']['ext'].upper())
                    attachment.text = message['attachment']['doc']['title']
                elif attachment_type == 'wall':
                    attachment.text = message['attachment']['wall']['text'].replace('<br>','\n')
                    attachment.set('from', GetUserById(message['attachment']['wall']['from_id'], token))
                    attachment.set('date', UNIXTimeToString(message['attachment']['wall']['date']))
                    if 'copy_owner_id' in message['attachment']['wall']:
                        attachment.set('owner', GetUserById(message['attachment']['wall']['copy_owner_id'], token))
                    if 'attachments' in message['attachment']['wall']:
                        atts = ET.SubElement(attachment, "attachments")
                        atts.set('type', message['attachment']['wall']['attachments'][0]['type'])
            tree = ET.ElementTree(root)
        root.set("friend",''.join(['пользователем ', uname]))
        history_type = 'chat_created_' if chat else 'conversation_'
        tree.write(''.join([history_type, uname.replace(' ', '_') ,'.xml']),encoding="UTF-8",xml_declaration=True)
        end_message = 'Записано {} сообщений.'.format(total_msg_cnt) if args.stat else 'Записано.'
        print(end_message)
    except AttributeError:
        print('Ошибка установки атрибута XML.')
        #raise
    except:
        raise

if __name__ == "__main__":
    args = arg_parser.parse_args()

    # client_id - ID приложения ВКонтакте
    client_id = args.appid
    scope = ['friends','messages']

    if len(sys.argv) > 1:
        # если надоело вводить, закомментить следующие две строки
        email = input("Email: ")
        password = getpass.getpass()
        # а эти две раскомментить
        # email = 'user@example.org'
        # password = 'your_password'
        try:
            print('Получение токена...', end='')
            vk_data = GetToken(client_id,scope, email, password)
            user_id = vk_data['user_id']
            token = vk_data['access_token']
            print('Успешно.')
        except:
            print('Ошибка.')
            raise
    if args.friends and not args.dialogs:
        ShowFriends(user_id)
    elif not args.friends and args.dialogs:
        GetDialogs()
    elif args.uid is not None:
        friends = GetFriends(user_id)
        chat = 0
        GetMessages(args.uid, token, friends, chat)
    elif args.chatid and args.uid is None:
        friends = GetFriends(user_id)
        chat = args.chatid
        GetMessages(args.uid, token, friends, chat)
    else:
        arg_parser.print_help()
