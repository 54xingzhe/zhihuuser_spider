# -*- coding: utf-8 -*-
import scrapy
from scrapy import spider, Request
import json
from ..items import UserItem


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    start_user = 'cnaafhvk'

    # 用户信息api接口
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    # include 参数
    user_query = 'allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,' \
                 'follower_count,articles_count,gender,badge[?(type=best_answerer)].topics'

    follows_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}' \
                  '&offset={offset}&limit={limit}'
    follows_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,' \
                    'is_following,badge[?(type=best_answerer)].topics'


    followers_url = 'https://www.zhihu.com/api/v4/members/{user}/followers?include={include}' \
                    '&offset={offset}&limit={limit}'
    followers_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,' \
                      'is_following,badge[?(type=best_answerer)].topics'

    # 初始请求的实现。此方法必须返回可迭代对象
    def start_requests(self):
        # 关注和粉丝信息接口调用
        # url = 'https://www.zhihu.com/api/v4/members/himoti?include=allow_message%2Cis_followed%2Cis_following%2Cis_org%2Cis_blocking%2Cemployments%2Canswer_count%2Cfollower_count%2Carticles_count%2Cgender%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics'
        # url = 'https://www.zhihu.com/api/v4/members/cnaafhvk/followers?include=data%5B*%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset=40&limit=20'
        yield Request(self.user_url.format(user=self.start_user, include=self.user_query), self.parse_user)
        yield Request(self.follows_url.format(user=self.start_user, include=self.follows_query, offset=0, limit=20),
                      callback=self.parse_follows)
        yield Request(self.followers_url.format(user=self.start_user, include=self.followers_query, offset=0, limit=20),
                      callback=self.parse_followers)

    #此方法必须返回一个包含Request,dict或Item的可迭代对象
    def parse_user(self, response):
        # print(response.text)  # 打印网页源代码
        result = json.loads(response.text)  # 利用loads方法声明json对象
        item = UserItem()  # 先声明item引用，然后对它进行赋值
        for field in item.fields:  # item的fields属性，fields输出item所有名称，以一个集合的形式返回
            if field in result.keys():  # 如果是键名之一，就对它进行赋值
                item[field] = result.get(field)
        yield item  # 用yield将item返回

        # 关注的人的列表
        yield Request(self.follows_url.format(user=result.get('url_token'), include=self.follows_query,
                                              offset=0, limit=20), self.parse_follows)
        # 粉丝列表
        yield Request(self.followers_url.format(user=result.get('url_token'), include=self.followers_query,
                                                offset=0, limit=20), self.parse_followers)

    # 关注列表
    def parse_follows(self, response):
        # print(response.text)
        results = json.loads(response.text)

        if 'data' in results.keys():
            for result in results.get('data'):
                # 用url_token构造新的请求
                yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),
                              self.parse_user)
        # 分页的判断。如果没有到最后一页，就获取下页链接，继续解析下一页
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield Request(next_page, self.parse_follows)  # 同样是处理关注列表，所以回调自己

    # 粉丝列表
    def parse_followers(self, response):
        # print(response.text)
        results = json.loads(response.text)

        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get('url_token'), include=self.user_query),
                              self.parse_user)
        # 没有到最后一页，继续解析下一页
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield Request(next_page, self.parse_followers)
