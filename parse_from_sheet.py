#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import pandas as pd
import numpy as np

#################################### Google API ####################################
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1dUn7uqnB2Ro6E5DU7LYEyITVDhJAYknUFAX6HGS4viE'
SAMPLE_RANGE_NAME = 'A1:T'

creds = None
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API
sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                            range=SAMPLE_RANGE_NAME).execute()
values = result.get('values', [])

####################################  End API  ####################################

values = [line for line in values if line]
data = np.array([xi+[None]*(len(values[0])-len(xi)) for xi in values[1:]])
df = pd.DataFrame(data=data, columns=values[0])
for i in range(2, 6):
    df[df.columns[i]] = df[df.columns[i]].astype(int)
departs = sorted(list(set(df.iloc[:, 1])))


def lstrip_to_letter(s):
    s = ' '.join([i for i in s.split() if len(i) > 0])
    for i in range(len(s)):
        if s[i].isalpha():
            return s[i:]
    return s


def get_answers(df, title):
    tmp_str = f'\n## {title}\n'
    found = False
    for c in df.columns:
        answers = [lstrip_to_letter(ans)
                   for ans in df[c].dropna() if len(ans) > 1]
        if answers:
            found = True
            tmp_str += f'\n### {c}\n'
            tmp_str += '\n'.join([f'{ind + 1}. {ans}' for ind,
                                 ans in enumerate(answers)])
    if found:
        return tmp_str
    return ''


info_str = ''
for d in departs:
    d_info = df.loc[df[df.columns[1]] == d]
    d_numbers = d_info.iloc[:, 3:6].mean().round(2)
    d_numbers = pd.DataFrame(
        {'Вопрос': d_numbers.index, 'Оценка (среднее по 5-бальной шкале)': d_numbers.values})
    info_str += f'\n# {d}\n'
    info_str += f'\n## Количественные вопросы.\n'
    info_str += f'\n{d_numbers.to_markdown(index=False)}\n'
    info_str += get_answers(d_info.iloc[:,
                            list(range(6, 13))+[19]], '\n## Общие вопросы.\n')
    info_str += get_answers(d_info.iloc[:, 13:15], '\n## Про науку.\n')
    info_str += get_answers(d_info.iloc[:, 15:17], '\n## Индустрия.\n')
    info_str += get_answers(d_info.iloc[:, 17:19], '\n## Другое.\n')


with open('README.md', 'w') as f:
    f.write(info_str + '\n')
