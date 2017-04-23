import argparse
import bs4 as bs
import numpy as np
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from random import choice

EOS = ['.', '?', '!']

def main(args):
    if args.mode in ['LEARN','WIKI']:
        yar_learn(args)
    elif args.mode in ['OUTPUT']:
        yar_output(args)

def yar_learn(args):
    '''
    I am learning. I need a URL to learn on, and a file to save to.
    '''
    filename = args.filename
    url = args.url
    if filename is None or url is None:
        print("Learn mode requires a filename and url")
        return
    #setup the chain
    try:
        chain = np.load(filename).item()
    except FileNotFoundError:
        chain = {}
    #start training
    
    training_links = []
    if args.mode == 'WIKI':
        if args.starts is None:
            print("Wiki mode requires starts.")
        training_links = get_training_links(url, args.starts)
    else:
        training_links.append(url)

    for index, link in enumerate(training_links):
        if args.v:
            print("Learning on {} of {} links.".format(index, len(training_links)))
        chain = train_on_link(link, chain)

    np.save(filename, chain)
    return

def yar_output(args):
    '''
    I am outputting. I need a chain.
    '''
    filename = args.filename
    if filename is None:
        print("Output mode requires a filename")
        return
    try:
        chain = np.load(filename).item()
    except FileNotFoundError:
        print("Output mode requires a valid chain file.")
    else:
        if False:
            #File many output
            attempts = 50
            comments = []
            while len(comments) < attempts:
                comment = build_comment(chain)
                if len(comment) <= 140 and len(comment) > 100:
                    print("{} out of {} Comments".format(len(comments), attempts))
                    comments.append(comment)
                    
            with open("Output.txt","w") as file:
                file.write('\n'.join(comments))
        else:
            #CLI single output
            while True:
                comment = build_comment(chain)
                if len(comment) <= 140 and len(comment) > 100:
                    print(len(comment))
                    print(comment + ".")
                    break
        
    return

##Helper Functions##
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
                if href.startswith(starts_with):
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
            if "I am a bot" in f.text:
                continue
            else:
                comments.append(f.text)
    return comments



if __name__ == '__main__':
    '''
    There should be two modes, train-mode and output-mode. This will be controlled
    by if you pass a .npy chain or not.
    --url <url>: passes url. used in learning
    --chain <filename>: loads filename.
    --mode <LEARN|OUTPUT> default will be learn. Learn requires URL. Output requires chain.
    --learn-link : will run train_on_link with url
    --learn-wiki <starts_with> : will run get_training_links and then train_on_link
    -v : verbose mode
    '''
    parser = argparse.ArgumentParser(description='Just an average redditor.')
    parser.add_argument('-v', help='verbose', action="store_true")
    parser.add_argument('--url', dest='url', help='The url used for learning.')
    parser.add_argument('--mode', dest='mode',
                        help='Which mode to run in. (Default: LEARN)',
                        default = 'LEARN', choices = ['LEARN', 'WIKI', 'OUTPUT'])
    parser.add_argument('--chain', dest='filename',
                        help='Filename of the markov chain.')
    parser.add_argument('--starts', dest='starts', help='Used in wiki learning.')
    args = parser.parse_args()
    print(args)
    main(args)
