class TestUser:
    def __init__(self):
        self.twitter_base_url = 'http://api.twitter.com/1.1'
        self.twitter_base_url_v2 = 'https://api.twitter.com/2'
        self.pinned = '1323049466837032961'
        self.pleroma_date = '2020-10-15 21:21:00'
        self.twitter_token = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' \
                             'XXXXXXXXXXXXXXXXXXXXXXXXX'
        self.pleroma_token = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        self.twitter_base_url_v2 = self.twitter_base_url_v2
        self.nitter = True
        self.replace_str = "{{ twitter_url }}"
