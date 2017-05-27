import json
import requests
import time

from collections import defaultdict

client_id = 5256758
scope = 'offline'
version = 5.64

access_url = 'https://oauth.vk.com/authorize?client_id=%s&scope=%s&response_type=token&v=%s' % (client_id, scope, version)
print(access_url)

access_token = '31186c2298272546525393cb91ce86d299002419fb7a97f691b7863f5e4c9f42401635fffa42cc2686396'

API_REQUEST = 'https://api.vk.com/method/%s?%s' + ('&access_token=%s&v=%s' % (access_token, version))
LIMIT = 100

domain = 'oldlentach'
group_wall = API_REQUEST % ('wall.get', 'domain=%s&offset=%s&filter=all&count=' + str(LIMIT))
post_comment = API_REQUEST % ('wall.getComments', 'owner_id=%s&post_id=%s&offset=%s&sort=asc&count=' + str(LIMIT))
user_fields = ['sex', 'bdate', 'has_photo', 'education']
user_info = API_REQUEST % ('users.get', 'user_ids=%s&fields=' + ','.join(user_fields))

data = defaultdict(list)
user_data = {}

# retrieve user ids with their posts
post_offset = 0
while True:
    time.sleep(.1)
    post_res = requests.get(group_wall % (domain, post_offset)).json()

    if 'error' in post_res:
        print(post_res['error']['error_msg'])
        time.sleep(1)
        continue

    if not post_res['response']['items']:
        print("Finished post processing")
        break

    print("Post offset %s out of %s" % (post_offset, post_res['response']['count']))
    for p in post_res['response']['items']:
        comment_offset = 0

        while True:
            time.sleep(.1)
            comment_res = requests.get(post_comment % (p['owner_id'], p['id'], comment_offset)).json()

            if 'error' in comment_res:
                print(comment_res['error']['error_msg'])
                time.sleep(1)
                continue

            if not comment_res['response']['items']:
                break

            for c in comment_res['response']['items']:
                if c['from_id'] > 0:
                    data[c['from_id']].append(c['text'])

            comment_offset += LIMIT

    post_offset += LIMIT

# retrieve users data
user_offset = 0
user_ids = sorted(data.keys())
while user_offset < len(user_ids):
    time.sleep(.1)
    user_res = requests.get(user_info % ','.join([str(_id) for _id in user_ids[user_offset:user_offset + LIMIT]])).json()

    if 'error' in user_res:
        print(user_res['error']['error_msg'])
        time.sleep(1)
        continue

    print("User offset %s out of %s" % (user_offset, len(user_ids)))
    for u in user_res['response']:
        user_data[u['id']] = u

    user_offset += LIMIT

print("Finished user processing. Saving data.")
# save data
with open('data_%s.json' % domain, mode='w') as out_json:
    json.dump({'users': user_data, 'data': data}, out_json)
print("Data saved.")
