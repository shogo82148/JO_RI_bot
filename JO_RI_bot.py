#!/usr/bin/env python
# -*- coding:utf-8 -*-

import re
import config
import TwitterBot
import TwitterBot.AdminFunctions as AdminFunctions
import datetime
import random
import logging
import urllib

from TwitterBot.modules import friendship
from TwitterBot.modules import fizzbuzz
from TwitterBot.modules import unicodehook
from TwitterBot.modules.unya import Unya
from TwitterBot.modules import reflexa
from TwitterBot.modules import gakushoku
from TwitterBot.modules.amazon import Amazon
from TwitterBot.modules.CloneBot import CloneBot
from TwitterBot.modules.dokusho import Dokusho
from TwitterBot.modules import busNUT
from TwitterBot.modules.Translator import Translator
from TwitterBot.modules import DayOfTheWeek
from TwitterBot.modules.wolframalpha import WolframAlpha
from TwitterBot.modules import ukeru
import TwitterBot.modules.DateTimeHooks as DateTimeHooks
import tweepy
import TwitterBot.modules.atnd as atnd

logger = logging.getLogger("Bot.JO_RI")

class GlobalCloneBot(CloneBot):
    def __init__(self, crawl_user, mecab=None, log_file='crawl.tsv', db_file='bigram.db', crawler_api=None):
        super(GlobalCloneBot, self).__init__(crawl_user, mecab, log_file, db_file, crawler_api)
        self.translator = Translator(config.BING_APP_KEY, 'ja', 'en').translator

    def reply_hook(self, bot, status):
        """適当にリプライを返してあげる"""
        text = self.get_text()
        if status:
            bot.reply_to(text, status)
        else:
            bot.update_status(text)
            #時々英訳
            if random.random()<0.2:
                text = self.translator.translate(text)
                bot.update_status(u'[Translated] '+text)
                #時々再翻訳
                if random.random()<0.5:
                    text = self.translator.translate(text, 'en', 'ja')
                    bot.update_status(u'[再翻訳] ' + text)
        return True

class JO_RI_bot(TwitterBot.BaseBot):
    def __init__(self):
        super(JO_RI_bot, self).__init__(config.CONSUMER_KEY,
                                        config.CONSUMER_SECRET,
                                        config.ACCESS_KEY,
                                        config.ACCESS_SECRET)

    def on_start(self):
        self.append_reply_hook(AdminFunctions.shutdown_hook(
                allowed_users = config.ADMIN_USER,
                command = set([u'バルス', u'シャットダウン', u'shutdown', u'halt', u':q!', u'c-x c-c'])),
            priority=TwitterBot.PRIORITY_ADMIN)
        self.append_reply_hook(AdminFunctions.delete_hook(
                allowed_users = config.ADMIN_USER,
                command = set([u'削除', u'デリート', u'delete']),
                no_in_reply = u'in_reply_to入ってないよ！'),
            priority=TwitterBot.PRIORITY_ADMIN)
        self.append_reply_hook(AdminFunctions.history_hook(
                reply_limit = 2,
                reset_cycle = 20*60,
                allowed_users = config.BOT_USER))
        self.append_reply_hook(AdminFunctions.history_hook(
                reply_limit = config.REPLY_LIMIT1,
                reset_cycle = config.RESET_CYCLE1,
                limit_msg = [u'今、ちょっと取り込んでまして・・・'
                              u'またのご利用をお待ちしております！',
                             u'もっと時間を有意義に使いませんか？']))
        self.append_reply_hook(AdminFunctions.history_hook(
                reply_limit = config.REPLY_LIMIT2,
                reset_cycle = config.RESET_CYCLE2,
                limit_msg = [u'今、ちょっと取り込んでまして・・・'
                              u'またのご利用をお待ちしております！',
                             u'もっと時間を有意義に使いませんか？']))
        self.append_reply_hook(JO_RI_bot.limit_hook)
        self.append_reply_hook(JO_RI_bot.hire_me)

        self.translator = Translator(config.BING_APP_KEY)
        self.append_reply_hook(self.translator.hook)

        dokusho = Dokusho(
            config.CRAWL_USER,
            config.DOKUSHO_USER,
            config.AMAZON_ACCESS_KEY_ID,
            config.AMAZON_SECRET_ACCESS_KEY)
        self.append_reply_hook(dokusho.hook)
        self.append_cron('0 0 * * mon', dokusho.crawl)

        amazon = Amazon(
            config.CRAWL_USER,
            config.DOKUSHO_USER,
            config.AMAZON_ACCESS_KEY_ID,
            config.AMAZON_SECRET_ACCESS_KEY,
            config.AMAZON_ASSOCIATE_TAG)
        self.append_reply_hook(amazon.hook)

        self._gakushoku = gakushoku.GakuShoku(
                config.MENU_EMAIL, config.MENU_PASSWORD,
                config.MENU_ID, config.MENU_SHEET)
        self.append_reply_hook(self._gakushoku.hook)
        self.append_cron('00 11 * * *',
                         self._gakushoku.tweet_menu,
                         name = u'Gakushoku Menu(noon)',
                         args = (False,))
        self.append_cron('00 16 * * *',
                         self._gakushoku.tweet_menu,
                         name = u'Gakushoku Menu(afternoon)',
                         args = (True,))

        self.append_reply_hook(busNUT.Bus().hook)
        self.append_reply_hook(DayOfTheWeek.hook)
        self.append_reply_hook(DateTimeHooks.hook)
        self.append_reply_hook(atnd.hook)
        self.append_reply_hook(Unya().hook)
        self.append_reply_hook(unicodehook.hook)

        self.wolfram = WolframAlpha(config.WOLFRAM_ALPHA_APP_ID, self.translator.translator)
        self.append_reply_hook(self.wolfram.hook)
        self.append_reply_hook(reflexa.hook)
        self.append_reply_hook(JO_RI_bot.typical_response)
        self.append_reply_hook(friendship.breaker)
        self.append_reply_hook(fizzbuzz.hook)

        crawler_auth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
        crawler_auth.set_access_token(config.CRAWLER_ACCESS_KEY, config.CRAWLER_ACCESS_SECRET)
        crawler_api = tweepy.API(crawler_auth, retry_count=10, retry_delay=1)
        self.clone_bot = GlobalCloneBot(config.CRAWL_USER, crawler_api = crawler_api)
        self.append_reply_hook(ukeru.hook)
        self.append_reply_hook(self.clone_bot.reply_hook)
        self.append_cron('30 */2 * * *',
                         self.clone_bot.crawl,
                         name=u'Cron Crawling')
        self.append_cron('00 7-23 * * *',
                         self.clone_bot.update_status,
                         name=u'Cron Update Status')
        self.append_cron('30 11 * * *',
                         self.bot_attack,
                         name=u'Cron Bot Attack')

        self.clone_bot.crawl(self)
        self.update_status(random.choice([
                    u'【お知らせ】アプリボワゼ！颯爽登場！銀河美少年タウバーン！ [%s]',
                    u'【お知らせ】（<ゝω・）綺羅星☆[%s]',
                    u'【お知らせ】ほろーん[%s]',
                    u'【お知らせ】起動なう[%s]',
                    ]) % self.get_timestamp())

    def bot_attack(self, bot):
        name = random.choice(['aokcub_bot', 'FUCOROID', 'aokcub_bot', 'FUCOROID', 'JO_RI'])
        bot.update_status('@%s %s' % (name, self.clone_bot.get_text()))

    def on_shutdown(self):
        self.update_status(random.choice([
                    u'【お知らせ】目がぁぁぁ、目がぁぁぁぁ[%s]',
                    u'【お知らせ】ボットは滅びぬ、何度でも蘇るさ[%s]',
                    u'【お知らせ】シャットダウンなう[%s]',
                    ]) % self.get_timestamp())

    def limit_hook(self, status):
        text = status.text.lower()
        if text.find(u'api')<0:
            return False
        if text.find(u'残')<0:
            return False
        if text.find(u'報告')<0 and text.find(u'教')<0 and text.find(u'レポート')<0:
            return False
        limit = self.api.rate_limit_status()
        self.reply_to(u'API残数: %(remaining_hits)d/%(hourly_limit)d,'
                      u'リセット予定:%(reset_time)s (' % limit + self.get_timestamp()+')',
                      status)
        return True

    re_use = re.compile(u'(採用|雇用)(して|しろ|しなさい)|雇(って|え|いなさい|うがいい)|(就職|転職|入社)(したい|させろ)|(仕事|職|内定)[をが]?(ください|欲しい|くれ|ちょーだい|ちょうだい|頂戴)|働かせて')
    def hire_me(self, status):
        """採用・不採用"""
        # http://twitter.com/#!/2kkr/status/72250317244334080
        if not self.re_use.search(status.text):
            return False

        r = random.random()
        if r<0.4:
            def hook(bot, s):
                """ 千と千尋の神隠し風 """
                if s.author.id != status.author.id:
                    return False
                msg = random.choice(
                    [
                        u"ずいぶん生意気な口を利くね。いつからそんなに偉くなったんだい？",
                        u"無駄口をきくな。私のことは、じょり様と呼べ。"
                        ]
                    )
                bot.reply_to(u"{0} [{1}]".format(msg, bot.get_timestamp()), s)
                return True

            name = status.author.name[:15]
            """ http://www.aozora.gr.jp/kanji_table/ よりリスト取得"""
            joyo = u'亜哀愛悪握圧扱安暗案以位依偉囲委威尉意慰易為異移維緯胃衣違遺医井域育一壱逸稲芋印員因姻引飲院陰隠韻右宇羽雨渦浦運雲営影映栄永泳英衛詠鋭液疫益駅悦謁越閲円園宴延援沿演炎煙猿縁遠鉛塩汚凹央奥往応押横欧殴王翁黄沖億屋憶乙卸恩温穏音下化仮何価佳加可夏嫁家寡科暇果架歌河火禍稼箇花荷華菓課貨過蚊我画芽賀雅餓介会解回塊壊快怪悔懐戒拐改械海灰界皆絵開階貝劾外害慨概涯街該垣嚇各拡格核殻獲確穫覚角較郭閣隔革学岳楽額掛潟割喝括活渇滑褐轄且株刈乾冠寒刊勘勧巻喚堪完官寛干幹患感慣憾換敢棺款歓汗漢環甘監看管簡緩缶肝艦観貫還鑑間閑関陥館丸含岸眼岩頑顔願企危喜器基奇寄岐希幾忌揮机旗既期棋棄機帰気汽祈季紀規記貴起軌輝飢騎鬼偽儀宜戯技擬欺犠疑義議菊吉喫詰却客脚虐逆丘久休及吸宮弓急救朽求泣球究窮級糾給旧牛去居巨拒拠挙虚許距漁魚享京供競共凶協叫境峡強恐恭挟教橋況狂狭矯胸脅興郷鏡響驚仰凝暁業局曲極玉勤均斤琴禁筋緊菌襟謹近金吟銀九句区苦駆具愚虞空偶遇隅屈掘靴繰桑勲君薫訓群軍郡係傾刑兄啓型契形径恵慶憩掲携敬景渓系経継茎蛍計警軽鶏芸迎鯨劇撃激傑欠決潔穴結血月件倹健兼券剣圏堅嫌建憲懸検権犬献研絹県肩見謙賢軒遣険顕験元原厳幻弦減源玄現言限個古呼固孤己庫弧戸故枯湖誇雇顧鼓五互午呉娯後御悟碁語誤護交侯候光公功効厚口向后坑好孔孝工巧幸広康恒慌抗拘控攻更校構江洪港溝甲皇硬稿紅絞綱耕考肯航荒行衡講貢購郊酵鉱鋼降項香高剛号合拷豪克刻告国穀酷黒獄腰骨込今困墾婚恨懇昆根混紺魂佐唆左差査砂詐鎖座債催再最妻宰彩才採栽歳済災砕祭斎細菜裁載際剤在材罪財坂咲崎作削搾昨策索錯桜冊刷察撮擦札殺雑皿三傘参山惨散桟産算蚕賛酸暫残仕伺使刺司史嗣四士始姉姿子市師志思指支施旨枝止死氏祉私糸紙紫肢脂至視詞詩試誌諮資賜雌飼歯事似侍児字寺慈持時次滋治璽磁示耳自辞式識軸七執失室湿漆疾質実芝舎写射捨赦斜煮社者謝車遮蛇邪借勺尺爵酌釈若寂弱主取守手朱殊狩珠種趣酒首儒受寿授樹需囚収周宗就州修愁拾秀秋終習臭舟衆襲週酬集醜住充十従柔汁渋獣縦重銃叔宿淑祝縮粛塾熟出術述俊春瞬准循旬殉準潤盾純巡遵順処初所暑庶緒署書諸助叙女序徐除傷償勝匠升召商唱奨宵将小少尚床彰承抄招掌昇昭晶松沼消渉焼焦照症省硝礁祥称章笑粧紹肖衝訟証詔詳象賞鐘障上丈乗冗剰城場壌嬢常情条浄状畳蒸譲醸錠嘱飾植殖織職色触食辱伸信侵唇娠寝審心慎振新森浸深申真神紳臣薪親診身辛進針震人仁刃尋甚尽迅陣酢図吹垂帥推水炊睡粋衰遂酔錘随髄崇数枢据杉澄寸世瀬畝是制勢姓征性成政整星晴正清牲生盛精聖声製西誠誓請逝青静斉税隻席惜斥昔析石積籍績責赤跡切拙接摂折設窃節説雪絶舌仙先千占宣専川戦扇栓泉浅洗染潜旋線繊船薦践選遷銭銑鮮前善漸然全禅繕塑措疎礎祖租粗素組訴阻僧創双倉喪壮奏層想捜掃挿操早曹巣槽燥争相窓総草荘葬藻装走送遭霜騒像増憎臓蔵贈造促側則即息束測足速俗属賊族続卒存孫尊損村他多太堕妥惰打駄体対耐帯待怠態替泰滞胎袋貸退逮隊代台大第題滝卓宅択拓沢濯託濁諾但達奪脱棚谷丹単嘆担探淡炭短端胆誕鍛団壇弾断暖段男談値知地恥池痴稚置致遅築畜竹蓄逐秩窒茶嫡着中仲宙忠抽昼柱注虫衷鋳駐著貯丁兆帳庁弔張彫徴懲挑朝潮町眺聴脹腸調超跳長頂鳥勅直朕沈珍賃鎮陳津墜追痛通塚漬坪釣亭低停偵貞呈堤定帝底庭廷弟抵提程締艇訂逓邸泥摘敵滴的笛適哲徹撤迭鉄典天展店添転点伝殿田電吐塗徒斗渡登途都努度土奴怒倒党冬凍刀唐塔島悼投搭東桃棟盗湯灯当痘等答筒糖統到討謄豆踏逃透陶頭騰闘働動同堂導洞童胴道銅峠匿得徳特督篤毒独読凸突届屯豚曇鈍内縄南軟難二尼弐肉日乳入如尿任妊忍認寧猫熱年念燃粘悩濃納能脳農把覇波派破婆馬俳廃拝排敗杯背肺輩配倍培媒梅買売賠陪伯博拍泊白舶薄迫漠爆縛麦箱肌畑八鉢発髪伐罰抜閥伴判半反帆搬板版犯班畔繁般藩販範煩頒飯晩番盤蛮卑否妃彼悲扉批披比泌疲皮碑秘罷肥被費避非飛備尾微美鼻匹必筆姫百俵標氷漂票表評描病秒苗品浜貧賓頻敏瓶不付夫婦富布府怖扶敷普浮父符腐膚譜負賦赴附侮武舞部封風伏副復幅服福腹複覆払沸仏物分噴墳憤奮粉紛雰文聞丙併兵塀幣平弊柄並閉陛米壁癖別偏変片編辺返遍便勉弁保舗捕歩補穂募墓慕暮母簿倣俸包報奉宝峰崩抱放方法泡砲縫胞芳褒訪豊邦飽乏亡傍剖坊妨帽忘忙房暴望某棒冒紡肪膨謀貿防北僕墨撲朴牧没堀奔本翻凡盆摩磨魔麻埋妹枚毎幕膜又抹末繭万慢満漫味未魅岬密脈妙民眠務夢無矛霧婿娘名命明盟迷銘鳴滅免綿面模茂妄毛猛盲網耗木黙目戻問紋門匁夜野矢厄役約薬訳躍柳愉油癒諭輸唯優勇友幽悠憂有猶由裕誘遊郵雄融夕予余与誉預幼容庸揚揺擁曜様洋溶用窯羊葉要謡踊陽養抑欲浴翌翼羅裸来頼雷絡落酪乱卵欄濫覧利吏履理痢裏里離陸律率立略流留硫粒隆竜慮旅虜了僚両寮料涼猟療糧良量陵領力緑倫厘林臨輪隣塁涙累類令例冷励礼鈴隷零霊麗齢暦歴列劣烈裂廉恋練連錬炉路露労廊朗楼浪漏老郎六録論和話賄惑枠湾腕'
            jimmei = u'丑丞乃之也亘亥亦亨亮伊伍伎伶伽佑侃侑倖倭偲允冴冶凌凜凪凱勁匡卯叡只叶吾呂哉唄啄喬嘉圭尭奈奎媛嬉孟宏宥寅峻崚嵐嵩嵯嶺巌巳巴巽庄弘弥彗彦彪彬怜恕悌惇惟惣慧憧拳捷捺敦斐於旦旭旺昂昌昴晃晋晏晟晨智暉暢曙朋朔李杏杜柊柚柾栗栞桂桐梓梢梧梨椋椎椰椿楊楓楠榛槙槻樺橘檀欣欽毅毬汀汐汰沙洲洵洸浩淳渚渥湧滉漱澪熙熊燎燦燿爽爾猪玖玲琉琢琳瑚瑛瑞瑠瑶瑳璃甫皐皓眉眸睦瞭瞳矩碧碩磯祐禄禎秦稀稔稜穣竣笙笹紗紘紬絃絢綜綸綺綾緋翔翠耀耶聡肇胡胤脩舜艶芙芹苑茉茄茅茜莉莞菖菫萌萩葵蒔蒼蓉蓮蔦蕉蕗藍藤蘭虎虹蝶衿袈裟詢誼諄諒赳輔辰迪遥遼邑那郁酉醇采錦鎌阿隼雛霞靖鞠須頌颯馨駒駿魁鮎鯉鯛鳩鳳鴻鵬鶴鷹鹿麟麿黎黛亀'
            new_name = random.choice(joyo+jimmei)
            url = 'http://ja.wiktionary.org/wiki/' + urllib.quote(new_name.encode('utf-8'))
            new_status = bot.reply_to(
                u"フン。{0}というのかい？"
                u"贅沢な名だねぇ。今からおまえの名前は{1}だ。"
                u"いいかい、{1}だよ。分かったら返事をするんだ、{1}！！ {2} [{3}]"
                .format(name, new_name, url, bot.get_timestamp()), status)
            self.append_reply_hook(hook, name='hire-%d' % new_status.id, in_reply_to=new_status.id, time_out=60*60)
        elif r<0.7:
            bot.reply_to(u"採用 ＼( 'ω')／ [%s]" % bot.get_timestamp(), status)
        else:
            bot.reply_to(u"不採用 (乂'ω') [%s] "  % bot.get_timestamp(), status)
        return True

    def typical_response(self, status):
        """決まりきった応答"""

        #ぬるぽ→ｶﾞｯ
        if status.text.find(u'ぬるぽ')>=0 or status.text.find(u'ゑぬぽ')>=0:
            bot.reply_to(u'ｶﾞｯ [%s]' % bot.get_timestamp(), status)
            return True

        #アプリボワゼ
        if status.text.find(u'アプリボワゼ')>=0:
            bot.reply_to(u'颯爽登場！！銀河美少年タウバーン！ [%s]' % bot.get_timestamp(), status)
            return True

        #颯爽登場！
        if status.text.find(u'颯爽登場')>=0:
            bot.reply_to(u'銀河美少年！タウバーン！ [%s]' % bot.get_timestamp(), status)
            return True

        #綺羅星→綺羅星
        if status.text.find(u'綺羅星')>=0:
            bot.reply_to(u'（<ゝω・）綺羅星☆ [%s]' % bot.get_timestamp(), status)
            return True
        
        #生存！→戦略！
        if status.text.find(u'生存')>=0 or status.text.find(u'せいぞん')>=0:
            if status.text.find(u'戦略')>=0 or status.text.find(u'せんりゃく')>=0:
                bot.reply_to(u'生存戦略、しましょうか [%s]' % bot.get_timestamp(), status)
            else:
                bot.reply_to(u'せんりゃくうううう！！！ [%s]' % bot.get_timestamp(), status)
            return True

        #足の裏→わーお
        # https://twitter.com/s2_EV/status/227272548512051200
        if status.text.find(u'足の裏')>=0:
            bot.reply_to(u'わーお！ [%s]' % bot.get_timestamp(), status)
            return True

        #バルス
        if status.text.find(u'バルス')>=0:
            bot.reply_to(u'目がぁぁぁ、目がぁぁぁぁ・・・これで満足ですか？ [%s]' % bot.get_timestamp(), status)
            return True

        return False

    def is_spam(self, user):
        return user.screen_name=='JO_RI' or \
            user.statuses_count==0 or \
            user.followers_count*5<user.friends_count

    def on_follow(self, target, source):
        if source.screen_name==self._name:
            return
        if not source.protected and self.is_spam(source):
            text = u'@%s あなたは本当に人間ですか？JO_RI_botはボットからのフォローを受け付けておりません。' \
                u'人間だというなら1時間以内にこのツイートへ「ボットじゃないよ！」と返してもらえますか？ [%s]' \
                % (source.screen_name, self.get_timestamp())
            new_status = self.update_status(text)
            name = u'AreYouBot-%d' % new_status.id
            
            def hook(bot, status):
                if status.author.id!=source.id:
                    return
                if status.text.find(u'ボットじゃない')<0:
                    return
                self.reply_to(u'ボットじゃない・・・だと・・・ [%s]' % bot.get_timestamp(), status)
                self.delete_reply_hook(name)
                return True

            def timeout(bot):
                self.api.create_block(id=source.id)
                self.update_status(u'%sがスパムっぽいのでブロックしました [%s]'
                                   % (source.screen_name, self.get_timestamp()))

            self.append_reply_hook(hook, name=name,
                                   in_reply_to=new_status.id, time_out=60*60, on_time_out=timeout)
        else:
            text = u'@%s フォローありがとう！JO_RI_botは超高性能なボットです。' \
                u'説明書を読んでリプライを送ってみて！ ' \
                u'https://github.com/shogo82148/JO_RI_bot/wiki [%s]' \
                % (source.screen_name, self.get_timestamp())
            self.update_status(text)

            if source.protected:
                source.follow()

    re_follow_message = re.compile(ur'@(\w+)\s+フォローありがとう！')
    def on_favorite(self, target, source):
        m = self.re_follow_message.search(target.text)
        if not m:
            return
        if m.group(1)!=source.screen_name:
            return
        #self.api.create_friendship(source.id)

if __name__=='__main__':
    bot = JO_RI_bot()
    bot.main()
