JO_RI_bot
======================
## JO_RI_botとは ##
JO_RI_botとは[JO_RI](https://twitter.com/#!/JO_RI)の真似をする
Twitter bot(Twitterへの自動投稿プログラム)です。本人の発言をクロールし、
マルコフ連鎖を用いて本人っぽい発言を生成します。

詳しくは[wiki](https://github.com/shogo82148/JO_RI_bot/wiki)を参照してください。

## インストール方法 ##
JO_RI_botはPython2.6以降で動作します。
残念ながら自動セットアップツールは用意していないので、
依存しているライブラリを自分でインストールする必要があります。
次のライブラリを easy_install や pip を使ってインストールしてください。

* tweepy
* jcconv
* bottlenose
* croniter
* MeCab

次にツイッターアカウントなどの設定を行います。
config.py.example を config.py へコピーし、中身を書き換えてください。
Twitterアカウント、Googleアカウント、Amazonアクセスキー、BingAPIキーなどが必要です。

必要な設定が完了したら

    python JO_RI_bot.py

で起動します。

## License ##
----------
Copyright &copy; 2012 Shogo Ichinose
Distributed under the [MIT License][mit].
 
[MIT]: http://www.opensource.org/licenses/mit-license.php
