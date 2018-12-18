# coding:utf-8
""" 消息处理 """
import xml.etree.ElementTree as ET
from functions import logger
import time


class MsgHandle(object):
    """ 处理消息 """
    def __init__(self, xml_data):
        # 数据解析
        self.data = self._parse_xml(xml_data)
        logger.info('[wechat] receive msg_data :%s' % str(self.data))
        # 消息类型
        self.type = self.data.find('FromUserName').text
        # 转换为消息对象
        self.msg_obj = self._to_msg()

    def run(self):
        """ 消息处理，返回结果 """
        # 处理相应的消息
        self.msg_obj.handle()
        # 回复消息
        return self.msg_obj.reply()

    def _parse_xml(self, xml_data):
        """ 解析xml """
        if len(xml_data) == 0:
            raise ValueError('[wechat] xml_data is None')
        return ET.fromstring(xml_data)

    def _to_msg(self):
        """ 转换消息 """
        if self.type == 'text':
            msg_obj = TextMsg(self.data)
        elif self.type == 'image':
            msg_obj = ImageMsg(self.data)
        elif self.type == 'voice':
            msg_obj = VoiceMsg(self.data)
        elif self.type == 'link':
            msg_obj = LinkMsg(self.data)
        else:
            msg_obj = Msg(self.data)

        return msg_obj


class Msg(object):
    """ 消息父类 """
    def __init__(self, data):
        """ 获取公共参数 """
        self.ToUserName = data.find('ToUserName').text
        self.FromUserName = data.find('FromUserName').text
        self.CreateTime = data.find('CreateTime').text
        self.MsgType = data.find('MsgType').text
        self.MsgId = data.find('MsgId').text

    def handle(self):
        """ 处理消息 """
        pass

    def reply(self):
        """ 回复消息 """
        return "success"


class TextMsg(Msg):
    """ 文本消息 """
    def __init__(self, data):
        super().__init__(data)
        self.Content = data.find('Content').text.encode('utf-8')

    def handle(self):
        self.msg_data = {}
        self.msg_data['ToUserName'] = self.FromUserName
        self.msg_data['FromUserName'] = self.ToUserName
        self.msg_data['CreateTime'] = int(time.time())
        self.msg_data['Content'] = self.ai(self.Content)

    def reply(self):
        xml_form = """
        <xml>
        <ToUserName><![CDATA[{ToUserName}]]></ToUserName>
        <FromUserName><![CDATA[{FromUserName}]]></FromUserName>
        <CreateTime>{CreateTime}</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[{Content}]]></Content>
        </xml>
        """
        logger.info('[wechat] reply msg_data: %s' % str(xml_form))
        return xml_form.format(**self.msg_data)

    def ai(self, content):
        return content.split(',')[-1].split('，')[-1].replace('吗', "").replace('?', '!').replace('？', '!')


class ImageMsg(Msg):
    """ 图片消息 """
    def __init__(self, data):
        super().__init__(data)
        self.PicUrl = data.find('PicUrl').text
        self.MediaId = data.find('MediaId').text


class VoiceMsg(Msg):
    """ 语音消息 """
    def __init__(self, data):
        super().__init__(data)
        self.Format = data.find('Format').text
        self.MediaId = data.find('MediaId').text
        try:
            # 语音识别结果
            self.Recognition = data.find('Recognition').text
        except Exception:
            self.Recognition = None

    def handle(self):
        pass


class LinkMsg(Msg):
    """ 链接消息 """
    def __init__(self, data):
        super().__init__(data)
        self.Title = data.find('Title').text
        self.Description = data.find('Description').text
        self.Url = data.find('Url').text
