'''
This script requests a list of the videos that are associated with the keyword 'tradwife'
from the Youtube API and writes this list in a .csv-file.

'''
import csv

from googleapiclient.discovery import build

api_key = 'AIzaSyBpEbgOwfw8Vi_k7sbse-PPjWVOUbgVReY'

service = build('youtube','v3', developerKey=api_key)

nextPageToken = None

with open('tradwife.csv', 'w') as results:
    csvwrite = csv.writer(results)
    csvwrite.writerow(['Video ID', 'Title', 'Channel', 'Published At'])
    while True:
        request = service.search().list(
            q='tradwife',
            part='snippet',
            type='video',
            maxResults=50,
            pageToken=nextPageToken
        )
        response = request.execute()
        items = response.get('items',[])
        for each_item in items:
            video_id = each_item['id']['videoId']
            title = each_item['snippet']['title']
            channel = each_item['snippet']['channelTitle']
            published = each_item['snippet']['publishedAt']
            csvwrite.writerow([video_id, title, channel, published])
        nextPageToken = response.get('nextPageToken')
        if not nextPageToken:
            break;


'''
With the .csv-file the items can be divided into the year they were published by
'published'.
'''