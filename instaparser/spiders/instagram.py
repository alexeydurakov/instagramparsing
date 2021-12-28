import json
import re

import scrapy
from scrapy.http import HtmlResponse
from urllib.parse import urlencode
from copy import deepcopy
from instaparser.items import InstaparserItem


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com/']
    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    inst_login = 'alexeydurakov'
    inst_pwd = '****************'
    user_parse = ['bukagad', 'sweet_cakes_tortberry']
    inst_graphql_link = 'https://i.instagram.com/api/v1/friendships'
    posts_hash = '8c2a529969ee035a5063f2fc8602a0fd'

    def parse(self, response: HtmlResponse):
        csrf = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(
            self.inst_login_link,
            method='POST',
            callback=self.login,
            formdata={'username': self.inst_login,
                      'enc_password': self.inst_pwd},
            headers={'x-csrftoken': csrf}

        )

    def login(self, response: HtmlResponse):
        j_data = response.json()
        if j_data.get('authenticated'):
            for user in self.user_parse:
                yield response.follow(
                    f'/{user}',
                    callback=self.user_parsing,
                    cb_kwargs={'username': user}
                )

    # первый запрос
    def user_parsing(self, response: HtmlResponse, username):
        user_id = self.fetch_user_id(response.text, username)
        variables = {'first': 12,
                     'max_id': 0,
                     'search_surface': 'follow_list_page'}
        follow_vars = ['followers', 'following']
        for follow in follow_vars:
            posts_url = f'{self.inst_graphql_link}/{user_id}/{follow}/?&{urlencode(variables)}'

            yield response.follow(posts_url,
                                  method='GET',
                                  callback=self.user_post_parse,
                                  headers={'User-Agent': 'Instagram 155.0.0.37.107'},
                                  cb_kwargs={'username': username,
                                             'user_id': user_id,
                                             'follow': follow,
                                             'variables': deepcopy(variables)}
                                  )

    def user_post_parse(self, response: HtmlResponse, username, user_id, follow, variables):
        j_data = response.json()
        users = j_data.get('users')
        for user in users:
            item = InstaparserItem(
                user_id=user.get('pk'),
                username=user.get('username'),
                photo=user.get('profile_pic_url'),
                follow=follow,
                friend=username
            )
            yield item

        if j_data.get('big_list'):
            variables['max_id'] += 12
            posts_url = f'{self.inst_graphql_link}/{user_id}/{follow}/?&{urlencode(variables)}'
            yield scrapy.Request(posts_url,
                                 method='GET',
                                 callback=self.user_post_parse,
                                 headers={'User-Agent': 'Instagram 155.0.0.37.107'},
                                 cb_kwargs={'username': username,
                                            'user_id': user_id,
                                            'follow': follow,
                                            'variables': deepcopy(variables)}
                                 )

    def fetch_csrf_token(self, text):
        ''' Get csrf-token for auth '''
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    def fetch_user_id(self, text, username):
        matched = re.search(
            '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
        ).group()
        return json.loads(matched).get('id')
