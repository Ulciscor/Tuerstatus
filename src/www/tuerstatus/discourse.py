from urllib import request
from urllib import parse
import json

class Discourse:
    # Config
    HOST = 'http://127.0.0.1' # Host adress here
    API_KEY = '123abc' # API key here
    
    def setConfig(self, host, key):
        HOST = host
        API_KEY = key
    
    def createTopic(self, title, text, category='1'):
        data = {'title':title, 'raw':text, 'category':category}
        print(data)
        data = parse.urlencode(data)
        data = data.encode()
        print(self.HOST)
    #     req = request.Request(HOST + '/posts?api_key=' + API_KEY, data)
        print(self.HOST + '/posts?api_key=' + self.API_KEY)
        response = request.urlopen(self.HOST + '/posts?api_key=' + self.API_KEY, data).read()
        response = response.decode()
        response = json.loads(response)
        #self.changeCategory(response['topic_id'], category)
    #     print(response)
        return response['topic_id']
    
    def changeCategory(self, topic, category):
        data = {'topic_id':topic, 'category_id':category}
        data = parse.urlencode(data)
        data = data.encode()
        req = request.Request(self.HOST + '/t/'+ str(topic) +'?api_key=' + self.API_KEY, data=data)
        req.method = 'PUT'
        response = request.urlopen(req).read()
    #     print(response)
    
    def updateTitle(self, topic, title):
        data = {'topic_id':topic, 'title':title}
        data = parse.urlencode(data)
        data = data.encode()
        req = request.Request(self.HOST + '/t/'+ str(topic) +'?api_key=' + self.API_KEY, data=data)
        req.method = 'PUT'
        response = request.urlopen(req).read()
    #     print(response)
    
    def createPost(self, topic, text):
        data = {'topic_id':topic, 'raw':text}
        data = parse.urlencode(data)
        data = data.encode()
        response = request.urlopen(self.HOST + '/posts?api_key=' + self.API_KEY, data).read()
    #     print(response)
        
    def updatePost(self, post, text):
        data = {'raw':text}
        data = parse.urlencode(data)
        data = data.encode()
        req = request.Request(self.HOST + '/posts/'+ str(post) +'?api_key=' + self.API_KEY, data=data)
        req.method = 'PUT'
        response = request.urlopen(req).read()
        print(response)
