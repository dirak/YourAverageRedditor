# -*- coding: utf-8 -*-
import argparse
import bs4 as bs
import numpy as np
import sys
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from random import choice

EOS = ['.', '?', '!']

def main(args):
    if args.subreddit is None:
        print("A subreddit is required. Try yar.py --help for more information.")
        return
    if args.i is False and args.o is False:
        print("You must specify at least one of input or output. Try yar.py --help for more information.")
    if args.i:
        yar_input(args)
    if args.o:
        yar_output(args)

def yar_input(args):
    '''
    I am learning on a particular subreddit.
    '''
    
    chain_filename = args.subreddit + "-sr"
    subreddit_link = "https://np.reddit.com/r/"+args.subreddit
    comment_link = subreddit_link + "/comments"
    training_links = []
    number_of_pages = int(args.pages)
    current_page = 0
    current_link = subreddit_link
    
    try:
        chain = np.load(chain_filename).item()
    except FileNotFoundError:
        chain = {}

    #Traverse subreddit
    while True:
        next_link = get_next_link(current_link)
        current_page += 1
        if next_link is None or current_page > number_of_pages:
            break
        if args.v:
            print("Scraping on page {} [{} of {}]".format(current_link, current_page, number_of_pages))
        training_links += get_training_links(current_link, comment_link)
        current_link = next_link

    for index, link in enumerate(training_links):
        if args.v:
            print("Learning on {} of {} links.".format(index, len(training_links)))
        chain = train_on_link(link, chain)
        np.save(chain_filename, chain)#naive way to save progress
    return

def yar_output(args):
    chain_filename = args.subreddit + "-sr"
    number_of_comments = args.comments
    comments = []
    try:
        chain = np.load(chain_filename+".npy").item()
    except FileNotFoundError:
        print("Output mode requires a subreddit to have been scraped. Try yar.py --help for more information.")
    else:
        while True:
            if len(comments) >= number_of_comments:
                break
            comment = build_comment(chain)
            if len(comment) <= 140 and len(comment) > 60:
                comments.append(comment)
    
    for comment in comments:
        #CLI
        print(comment)

##Helper Functions##
def get_next_link(url):
    header = {'User-Agent':'Mozilla'}
    try:        
        req = Request(url, headers=header)
        source = urlopen(req)
        source = source.read().decode('utf-8')
        soup = bs.BeautifulSoup(source, 'lxml')
    except HTTPError as e:
        print(e)
    else:
        for next_span in soup.select('span[class="next-button"]'):
            return next_span.a.get('href')

def get_training_links(url, starts_with):
    #get all urls from url that starts with starts_with
    header = {'User-Agent':'Mozilla'}
    links = []
    try:        
        req = Request(url, headers=header)
        source = urlopen(req)
        source = source.read()
        soup = bs.BeautifulSoup(source, 'lxml')
    except HTTPError as e:
        print(e)
    else:
        for link in soup.find_all('a'):
            href = link.get('href')
            if href is not None:
                if href.lower().startswith(starts_with.lower()):
                    links.append(href)
        
    return links

def train_on_link(url, chain={}):
    header = {'User-Agent':'Mozilla'}
    comments = []   
    try:        
        req = Request(url, headers=header)
        source = urlopen(req)
        source = source.read()
        soup = bs.BeautifulSoup(source, 'lxml')
    except HTTPError as e:
        print(e)
    except UnicodeEncodeError:
        print("URL is unreachable due to encoding.")
    else:
        comments = get_comments(soup)

    for comment in comments:
        chain = build_chain(comment, chain)

    return chain

def build_chain(input_sentence, chain):
    #TODO: Allow for variable key depth
    words = input_sentence.split()
    new_chain = chain
    for i, word in enumerate(words):
        try:
            first, second, third = words[i], words[i+1], words[i+2]
        except IndexError:
            break
        key = (first, second)
        if key not in new_chain:
            new_chain[key] = []
        #not checking for dupes makes a rudimentary weight system
        new_chain[key].append(third)
    return new_chain

def build_comment(chain):
    start = [key for key in chain.keys() if key[0][0].isupper()]
    key = choice(start)

    sentence = []
    first, second = key
    sentence.append(first)
    sentence.append(second)

    while True:
        try:
            third = choice(chain[key])
        except KeyError:
            break
        sentence.append(third)
        if third[-1] in EOS:
            break
        key = (second, third)
        first, second = key
    return ' '.join(sentence)

def get_comments(soup):
    entries = soup.select('div[class*=entry]')
    comments = []
    for entry in entries:
        form = entry.find_all('form')
        for f in form:
            if "I am a bot" in f.text:#bot comments are not representative of the subreddit
                continue
            else:
                comments.append(f.text)
    return comments



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Just an average redditor.')
    parser.add_argument('-v', help='verbose', action='store_true')
    parser.add_argument('-i', help='input', action='store_true')
    parser.add_argument('-o', help='output', action='store_true')
    parser.add_argument('--subreddit', help='The subreddit you want to learn on.')
    parser.add_argument('--pages', help='Number of pages to traverse. Default is 10', default=10)
    parser.add_argument('--comments', help='Number of comments to generate. Default is 1', default=1)
    args = parser.parse_args()
    print(args)
    try:
        main(args)
    except KeyboardInterrupt:
        sys.exit()
