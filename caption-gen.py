import requests
from rauth import OAuth2Service
from bs4 import BeautifulSoup
import pickle 

base_url = 'http://api.genius.com'
name='genius',
authorize_url='https://api.genius.com/oauth/authorize',
access_token_url='https://api.genius.com/oauth/token',
redirect_uri = 'https://example.com'
headers = {'Authorization': 'Bearer 3jz_OOtbzge3at7YILYONJ28G70EJ43pR7yL5KE9hqcDFMvegey-lgcRzvWPS23s'}

def get_model(artist_id):
    artist_id=str(artist_id)
    try:
        model = pickle.load(open(artist_id + ".pickle", "rb"))
    except Exception as e:
        model = {}
    return model

    

def save_model(artist_id, model):
    artist_id=str(artist_id)
    pickle.dump(model, open(artist_id + ".pickle", "wb"))

def lyrics_from_song_api_path(song_api_path):
  song_url = base_url + song_api_path
  response = requests.get(song_url, headers=headers)
  json = response.json()
  path = json['response']['song']['path']
  #gotta go regular html scraping... come on Genius
  page_url = 'http://genius.com' + path
  page = requests.get(page_url)
  html = BeautifulSoup(page.text, 'html.parser')
  #remove script tags that they put in the middle of the lyrics
  [h.extract() for h in html('script')]
  #at least Genius is nice and has a tag called 'lyrics'!
  lyrics = html.find('div', class_='lyrics').get_text() #updated css where the lyrics are based in HTML
  return lyrics

def artist_id_from_song_api_path(song_api_path):
    song_url = base_url + song_api_path
    response = requests.get(song_url, headers=headers)
    json = response.json()
    artist_id = json['response']['song']['album']['artist']['id']
    return artist_id

def scrape_search(search_term):
  search_url = base_url + '/search'
  data = {'q': search_term, 'per_page': 20} #20 is max number of pages that we can return
  response = requests.get(search_url, params=data, headers=headers)
  json = response.json()

  song_info = None
  print(len(json['response']['hits']))

  for hit in json['response']['hits']:
    try:
        song_info = hit
        song_api_path = song_info['result']['api_path']
        song = lyrics_from_song_api_path(song_api_path)
        artist_id = artist_id_from_song_api_path(song_api_path)
        song = song.replace('\n', ' __END__ __START__ ')
        song = song.split(' ')
        #print(song)
        disallowed = ['__END__','',' ']
        model = get_model(artist_id)
        skip_line_flag = False


        for index, token in enumerate(song):
            if index == 0:
                prev_token = '__START__'
            else:
                prev_token = song[index-1]

            curr_token = token

            if skip_line_flag:
                if prev_token == '__START__':
                    skip_line_flag = False
                else:
                    continue

            if '[' in curr_token:
                skip_line_flag = True
                continue

            if index == len(song)-1:
                break
            else:
                next_token = song[index+1]

            if curr_token in disallowed or prev_token in disallowed:
                continue

            else:
                array = []
                if (prev_token, curr_token) in model:
                    array = model[(prev_token, curr_token)]
                array.append(next_token)
                model[(prev_token, curr_token)] = array

        save_model(artist_id, model)

        print('processed song')
    except:
        print('failed processing song')
        print(hit)

    


if __name__ == '__main__':
        scrape_search('Young Thug')

  
