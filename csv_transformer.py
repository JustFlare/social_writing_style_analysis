import csv
import json
import os

CSV_DIR = 'csv'
AVG = False
PREFIX = 'avg_' if AVG else ''

with open('%spreprocessed_data.json' % PREFIX) as data_json:
    total_data = json.load(data_json)
    print('Total: %s' % len(total_data))

with open(os.path.join(CSV_DIR, '%scsv_data.csv' % PREFIX), mode='w') as out:
    i = 0
    while i < len(total_data):
        if not i % 100000:
            print('Offset %s out of %s' % (i, len(total_data)))

        user, feat = total_data[i]

        csv_row = dict()
        csv_row['u_id'] = user['id']
        csv_row['u_sex'] = user.get('sex', 0)
        csv_row['u_photo'] = user.get('has_photo', 0)
        csv_row['u_uni'] = 1 if user.get('university') else 0
        csv_row['u_year'] = user['year']

        for k, v in feat.items():
            if k in ['char_cnt', 'word_cnt', 'sent_cnt', 'punct_cnt']:
                continue
            csv_row['f_' + k] = v

        if not i:
            writer = csv.DictWriter(out, csv_row.keys())
            writer.writeheader()

        writer.writerow(csv_row)
        i += 1

    print('Finished')
