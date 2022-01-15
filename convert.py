import json
import os
from datetime import datetime
from distutils.dir_util import copy_tree
from collections import defaultdict

import typer
from typing import List, Optional
app = typer.Typer()


def escape(text, hashtag_whitelist):
    # I want to escape multiple special markdown characters and also the special characters of the Obsidian-flavored markdown, such as tilde and dollar signs
    special_signs = '*', '_', '~', '=', '$', '%'
    for sign in special_signs:
        text = text.replace(sign, f'\\{sign}')
    # also escape wikilinks-style character combinations
    text = text.replace('[[', f'\\[\\[')
    text = text.replace(']]', f'\\]\\]')
    text = text.replace('((', f'\\(\\(')
    text = text.replace('))', f'\\)\\)')
    
    hash_locations = [i for i, letter in enumerate(text) if letter == '#']
    for hash_loc in reversed(hash_locations):
        to_escape = True
        for term in hashtag_whitelist:
            if text[hash_loc+1 : hash_loc+1+len(term)] == term \
            and (hash_loc+1+len(term) >= len(text) or \
                     text[hash_loc+1+len(term)].isspace()):
                to_escape = False
                break
        if to_escape:
            # if a hashtag is not in the whitelist, escape the hash sign
            text = text[:hash_loc] + '\\' + text[hash_loc:]

    return text

def get_journal_entry(msg, inner_assets_dir, hashtag_whitelist):
    """Convert a particular message into a part of a journal dated with the date of the message.
    """
    journal_entry = '- '
    
    if 'file' in msg:
        file_dir = msg['file']
        filename = file_dir.split('/')[-1]
        # not using os.path.join for consistency with the existing path format
        s = f'[{filename}]({inner_assets_dir + "/" + file_dir.replace(" ", "%20")})'  # insert a file link
        journal_entry += s + ' '

    if 'photo' in msg:
        file_dir = msg['photo']
        filename = file_dir.split('/')[-1]
        # not using os.path.join for consistency with the existing path format
        s = f'![{filename}]({inner_assets_dir + "/" + file_dir.replace(" ", "%20")})'  # embed a photo
        journal_entry += s + ' '
    
    if 'text' in msg:
        if type(msg['text']) == str:
            journal_entry += escape(msg['text'], hashtag_whitelist)
            if journal_entry[-1:] != '\n':
                journal_entry += ' '
        elif type(msg['text']) == list:
            for entry in msg['text']:
                if type(entry) == str:
                    journal_entry += escape(entry, hashtag_whitelist)
                elif type(entry) == dict:
                    if entry['type'] in ['phone', 'bank_card', 'email', 'mention', 'underline']:
                        journal_entry += entry['text']
                    elif entry['type'] == 'link':
                        journal_entry += entry['text'].replace(' ', '%20')
                    elif entry['type'] == 'italic':
                        journal_entry += '*' + escape(entry['text'], hashtag_whitelist) + '*'
                    elif entry['type'] in ['code', 'cashtag', 'pre']:
                        journal_entry += '`' + escape(entry['text'], hashtag_whitelist) + '`'
                    elif entry['type'] == 'bold':
                        journal_entry += '**' + escape(entry['text'], hashtag_whitelist) + '**'
                    elif entry['type'] == 'text_link':
                        journal_entry += escape(entry['text'], hashtag_whitelist) + ' ' + entry['href'].replace(' ', '%20')
                    elif entry['type'] == 'hashtag':
                        journal_entry += escape(entry['text'], hashtag_whitelist)
                else:
                    raise Exception
                if journal_entry[-1:] != '\n':
                    journal_entry += ' '
        else:
            raise Exception
            
    journal_entry = journal_entry.replace('\n', '\n\t')
    if len(journal_entry) > 0:
        journal_entry = journal_entry[:-1]  # remove the last added whitespace
        
    return journal_entry

def get_journal(chat, inner_assets_dir, hashtag_whitelist):
    journal = ''
    for i, msg in enumerate(chat):
        if msg['type'] != 'message':
            continue
        new_entry = get_journal_entry(msg, inner_assets_dir, hashtag_whitelist)
        journal += new_entry
        if i != len(chat)-1:
            journal += '\n'
    return journal

@app.command()
def convert(input_dir : str, output_dir : str,
            hashtag_whitelist: Optional[List[str]] = typer.Argument(None)):
    with open(os.path.join(input_dir, 'result.json'), encoding='utf8') as handle:
        data = json.load(handle)
    
    # get the "Saved messages" chat
    chats_list = data['chats']['list']
    saved_messages_chats = [chat for chat in chats_list if chat['type'] == 'saved_messages']
    assert len(saved_messages_chats) == 1
    chat = saved_messages_chats[0]['messages']
    
    journals_dir = os.path.join(output_dir, 'journals')
    inner_assets_dir = f'tg_import_{datetime.today().strftime("%Y-%m-%d")}'
    assets_dir = os.path.join(output_dir, 'assets', inner_assets_dir)
    
    # create the file structure of a new markdown vault
    os.makedirs(journals_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)
    res = copy_tree(os.path.join(input_dir, 'chats'), os.path.join(assets_dir, 'chats'))
    
    # create a dict mapping a date to indices of messages on that date
    date_to_indices = defaultdict(list)
    for i, msg in enumerate(chat):
        cur_date = msg['date'][:10]
        date_to_indices[cur_date].append(i)
    
    dates_and_ranges = [(key, min(val), max(val)+1) for key, val in date_to_indices.items()]
    
    for date, msg_i_start, msg_i_end in dates_and_ranges:
        # journal means all messages for one day, formatted in markdown
        journal = get_journal(chat[msg_i_start : msg_i_end],
                              inner_assets_dir,
                              hashtag_whitelist)
        journal_path = os.path.join(journals_dir, f'{date}.md')
        if len(journal) > 0:
            with open(journal_path, 'w', encoding='utf8') as f:
                f.write(journal)
                
if __name__ == "__main__":
    app()