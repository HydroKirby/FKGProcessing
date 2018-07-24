#!/usr/bin/python3
# coding: utf-8
import os, sys, re, requests

mainurl = "http://フラワーナイトガール.攻略wiki.com/index.php?"
charaList = ["サルビア","ホワイトパンジー","イエローパンジー","パープルパンジー","ツバキ","ブラックバッカラ","ロイヤルプリンセス","ノヴァーリス","アルストロメリア","オンシジューム","シンビジューム","デンドロビウム","カトレア","ハイビスカス","クレナイ","アジサイ","グラジオラス","キキョウ","ヒマワリ","レッドジンジャー","スイレン","アカバナスイレン","イブキトラノオ","ヒルガオ","ヨルガオ","アサガオ","カサブランカ","ヤマユリ","オトメユリ","アブラナ","セントポーリア","マーガレット","サボテン","スズラン","スミレ","イチゴ","ウメ","バラ","サクラ","ユキヤナギ","アマリリス","ヒノキ","レンゲソウ","ハクモクレン","コチョウラン","コスモス","マリーゴールド","シクラメン","ミント","ラベンダー","ブルーロータス","サザンカ","ワレモコウ","センニチコウ","シロツメクサ","キンモクセイ","ジャスミン","ホトトギス","ヘリコニア","エーデルワイス","タンポポ","ヤグルマギク","カーネーション","スノーフレーク","スイートピー","ライラック","クロユリ","レッドチューリップ","イエローチューリップ","パープルチューリップ","ホワイトチューリップ","ギンラン","レシュノルティア","ヒメユリ","タチバナ","モモ","ハナモモ","キルタンサス","アネモネ","ガーベラ","チョコレートコスモス","ストロベリーキャンドル","リューココリーネ","ハナミズキ","アイリス","アンスリウム","デージー","エノコログサ","ジャーマンアイリス","ゼラニウム","ヤマブキ","サクランボ","オトギリソウ","ルピナス","サザンクロス","チェリーセージ","ゲッカビジン","ハナショウブ","ナデシコ","カンナ","イオノシジウム","カタバミ","ダリア","ネリネ","サンゴバナ","クチナシ","カラー","ディプラデニア","オオオニバス","ツキミソウ","ナイトフロックス","オシロイバナ","ヒガンバナ","エピデンドラム","キンギョソウ","ギンリョウソウ","ツバキ(フォスの花嫁)","オンシジューム(フォスの花嫁)","サボテン(フォスの花嫁)","ハリエンジュ","サンカクサボテン","ススキ","ウサギノオ","ルナリア","キンレンカ","ローレンティア","ヘレニウム","ガイラルディア","ユーカリ","イチョウ","モミジ","スズランノキ","リュウゼツラン","フォックスフェイス","ランタナ","ペポ","リンドウ","ペンタス","エキナセア","ビオラ","ヤツデ","リンゴ","アイビー","ヤドリギ","サンダーソニア","モミノキ","ポインセチア","クリスマスローズ","ホーリー","センリョウ","ナンテン","ハボタン","マンリョウ","マツ","ボタン","ユリ","シャクヤク","フクジュソウ","アカシア","ヘリオトロープ","ポピー","レインリリー","ベロニカ","バルーンバイン","シャムサクララン","ラナンキュラス","ヒメシャラ","ベルゲニア","ニシキギ","プリムラ","ロウバイ","ゼフィランサス","トリカブト","デルフィニウム","ローズマリー","ミモザ","サイネリア","ホップ","ヘザー","アプリコット","ヨモギ","シンクライリアナ","ナナカマド","アスター","カラスウリ","サフラン","ラッセリア","アロエ","リリオペ","スノードロップ","サツキ","カイコウズ","シオン","リシアンサス","イベリス","ベラドンナ","ワスレナグサ","グリーンベル","アリウム","タチアオイ","アリッサム","オキザリス","イヌタデ","ハブランサス","フクシア","クフェア","マンリョウ(ジューンブライド)","ハナモモ(ジューンブライド)","オオオニバス(ジューンブライド)","ガザニア","ジャーマンアイリス(七夕)","カタバミ(七夕)","バンテイシ","ヒメリュウキンカ","ライオンゴロシ","カトレア(水着)","チョコレートコスモス(水着)","エピデンドラム(水着)","プルメリア","スイギョク","イカリソウ","エニシダ","シーマニア","サクラ(エプロン)","ハナミズキ(浴衣)","ウメ(浴衣)","ビオラ(浴衣)","クレマチス","キヌタソウ","ホオズキ","サオトメバナ","ハツユキソウ","ウキツリボク","ナイトメア(カタクリ)","アルストロメリア(未来への感謝)","アネモネ(世界花の巫女)","ナデシコ(世界花の巫女)","ヒガンバナ(世界花の巫女)","エウカリス","フジバカマ","ツキトジ","ハギ","ツユクサ","カルセオラリア","アカンサス","シロタエギク","ストレリチア","ランプランサス","ハゼ","コキア","シャボンソウ","メイゲツカエデ","ヒトリシズカ","ウサギノオ(ハロウィン)","ニゲラ","シャクヤク(ハロウィン)","ブルーエルフィン","キウイ","パイナップル","ビワ","ミカン","モミジ(クリスマス)","シャムサクララン(クリスマス)","ポーチュラカ","ワタチョロギ","アプリコット(クリスマス)","イオノシジウム(クリスマス)","クリスマスベゴニア","ヒメシャラ(クリスマス)","スキミア","オキザリス(新春)","ユズリハ","アイビー(新春)","オリーブ","ローダンセ","セリ","ユキノシタ","ゴギョウ","ハコベラ","アナベル","プロテア","オトメギキョウ","キリンソウ","リカステ","オニユリ","ハートカズラ","カカオ","ヨウラクボタン","カキツバタ","ザクロ","ハス","ラミウム","オナモミ","ベルゲニア(ゴシックメイド)","ハナイ","ニチニチソウ","フリージア","モルチアナ","アンリ(バイカカラマツ)","ピラカンサ","サンタンカ","クルクマ","イモーテル","リンデルニア","コデマリ","サラセニア","オジギソウ","エルダーフラワー","ピンポンマム","バルーンバイン(イースター)","リムナンテス","ヘレニウム(イースター)","マネッチア","エノコログサ(花祭り)","カカリア","ランタナ(花祭り)","スイートウィリアム","アキレア","ルドベキア","マロニエ","ニリンソウ","クモマグサ","パキラ","リシマキア","セルリア","コマチソウ","ネリネ(ジューンブライド)","ヨメナ","スイレン(ジューンブライド)","ブバルディア","サンデリアーナ","カレンデュラ","リンゴ(七夕)","ペンステモン","ハバネロ","ホトトギス(水着)","バイカモ","ススキ(水着)","ギンバイソウ","フェンネル","クレソン","クコ","モケ","ヘリオトロープ(浴衣)","ハゼラン","オミナエシ","エケベリア","トレニア","カウスリップ","コマクサ","ミスミソウ","ロベリア","アネモネ(光華の姫君)","シクラメン(光華の姫君)","カトレア(光華の姫君)","ミズバコパ","ワレモコウ(成長する軍師)","アカバナスイレン(成長する陰謀)","ミント(成長する美徳)","ホシクジャク","イフェイオン","エキナセア(温泉浴衣)","ホップ(温泉浴衣)","エノテラ","スズシロ","ワルナスビ","ラークスパー","ストレプトカーパス","メギ","ミツガシワ","ニワゼキショウ","アサザ","ヤクノヒナホシ","サンカクサボテン(ハロウィン)","アルテミシア","デージー(ハロウィン)","ヤマゴーヤ","スズナ","ネモフィラ","スパラキシス","タツナミソウ","ツツジ","ツツジ(新人)","ハツユキソウ(クリスマス)","イベリス(クリスマス)","センリョウ(クリスマス)","クラスペディア","サフラン(クリスマス)","サンゴバナ(クリスマス)","シロタエギク(クリスマス)","ヒギリ","ミルトニア","クロユリ(新春)","カンヒザクラ","エーデルワイス(新春)","カリン","バイケイソウ","レオノチス","ペペロミア","ストック","ビバーナム","ガジュマル","クローバー","シュウメイギク","コリウス","カラタチ","アロエ(バレンタイン)","キンギョソウ(バレンタイン)","ラベンダー(バレンタイン)","トウカ","レモン","シバザクラ","パフィオペディルム","ウルシ","ウィンターコスモス","エリンジウム","コムギ","キヌサヤ","デルフィニウム(競技会)","カガミ","ウキツリボク(競技会)","キンセンカ","アズキ","マルメロ","アグロステンマ","アデニウム","ツキミソウ(イースター)","ブプレウルム","コデマリ(イースター)","テッポウユリ","ミズアオイ","ホルデュウム","ヒツジグサ","アヤメ","ローレンティア(忍者)","ルドベキア(忍者)","ワビスケ","カカラ","カルミア","サワギキョウ","イキシア","レインボーローズ","ウェルウィッチア","プルメリア(ジューンブライド)","サクランボ(ジューンブライド)","ハス(ジューンブライド)","ミズヒキ","ヘナ","ヘリクリサム","トリトニア","ビンカ","チトニア","ホシクジャク(水着)","ホーリー(水着)","ペポ(水着)","チューベローズ"]

class GenerateSeasonalQuote(object):
	def __init__(my):
		my.eventQuoteSymbol = ["①","②","③","④"]
		my.limitedEventIndicator = "【期間限定】"
		my.moduleTextList = {}
		my.moduleWrapper = '--[[Category:Seasonal quote modules]]\n\nreturn {{\n{0}'
		my.quoteEntryTemplate = '  ["{0}"] = {{\n    jp="{1}",\n    en=""\n  }},\n'
		my.startYear = "2016年"
		my.seasonList = [
			{'modulename':'Tanabata', 'count':4, 'JPName':'七夕', 'voiceline':'tanabata'},
			{'modulename':'Summer', 'count':3, 'JPName':'夏', 'voiceline':'summer'},
			{'modulename':'Mid-Autumn', 'count':3, 'JPName':'お月見', 'voiceline':'tsukimi'},
			{'modulename':'Autumn', 'count':3, 'JPName':'秋', 'voiceline':'autumn'},
			{'modulename':'Halloween', 'count':3, 'JPName':'ハロウィン', 'voiceline':'halloween'},
			{'modulename':'Winter', 'count':3, 'JPName':'冬', 'voiceline':'winter'},
			{'modulename':'Christmas', 'count':3, 'JPName':'クリスマス', 'voiceline':'holychristmas', 'year':2016},
			{'modulename':'New_Year', 'count':3, 'JPName':'お正月', 'voiceline':'newyear'},
			{'modulename':'Valentine', 'count':3, 'JPName':'バレンタイン', 'voiceline':'valentine'},
			{'modulename':'White_Day', 'count':3, 'JPName':'ホワイトデー', 'voiceline':'whiteday'},
			{'modulename':'Spring', 'count':3, 'JPName':'春', 'voiceline':'spring'},
		]
		
		my.seasonList_unique = [
			{'modulename':'Christmas_2015', 'count':2, 'JPName':'クリスマス', 'voiceline':'christmas', 'year':2015}
		]
		
	def initModuleTextList(my):
		for season in my.seasonList + my.seasonList_unique:
			name  = season['modulename']
			count = season['count']
			my.moduleTextList[name] = [
				"[\"{0}{1}\"] = {{\n" \
				.format(season['voiceline'], str(i+1).zfill(3)) \
				for i in range(count)
			]
	
	def downloadText(my, charaName):
		notice = "Processing " + charaName
		dltext = requests.get(mainurl + charaName).text

		if dltext.find('<div class="ie5">') == -1 :
			redirect = charaName.replace("(","（").replace(")","）")
			dltext  = requests.get(mainurl + redirect).text
			notice  += ".redirected -> " + redirect
		textdata = dltext.partition("図鑑未収録ボイス</th></tr><tr>")[2].partition("</table>")[0]
				
		print(notice)
		return textdata.replace(' class="spacer" /','').replace(' class="style_td"','')

	def extractCharacterPage(my, charaName):
		rawText = my.downloadText(charaName)
		moduleCharacterEntry = ["[\""+charaName+"\"] = {\n  "]
		
		for season in my.seasonList_unique:
			thisyear = str(season['year']+0)
			nextyear = str(season['year']+1)
			rawText_limited = rawText.partition(thisyear)[2].partition(nextyear)[0]
			for i in range(season['count']):
				my.extractQuote(charaName, season, i, rawText_limited)

		for season in my.seasonList:
			if 'year' in season and rawText.find(str(season['year'])) != -1:
				rawText_process = rawText.partition(str(season['year']))[2]
			else:
				rawText_process = rawText
			for i in range(season['count']):
				my.extractQuote(charaName, season, i, rawText_process)
		
	def extractQuote(my, charaName, season, index, rawText):
		inputQuote = rawText.partition(season['JPName']+my.eventQuoteSymbol[index])[2] \
		.partition('<td>')[2].partition("</td>")[0] \
		.replace(' class="spacer" /','').replace('"','\\"')
		
		if inputQuote != '':
			my.moduleTextList[season['modulename']][index] += \
				my.quoteEntryTemplate.format(charaName,inputQuote)
				
	def printModules(my):
		for module in my.moduleTextList:
			textContent = '},\n'.join(my.moduleTextList[module])[:-1] + '\n}\n}'
			moduleText = my.moduleWrapper.format(textContent)
			moduleName = module+'.lua'
			
			output_template(moduleText,moduleName)
			
				
	def main(my):
		my.initModuleTextList()
		for flowerKnight in charaList:
			my.extractCharacterPage(flowerKnight)
		
		my.printModules()
		
	

def add_quotes(text):
	"""Puts pairs of double-quotes around strings."""
	if text.startswith('"') and text.endswith('"'):
		return text
	return '"' + text + '"'
		
def output_template(text, outfilename):
	with open(outfilename, 'w', encoding='UTF8') as outfile:
		outfile.write(text)
		
if __name__ == '__main__':
	GenerateSeasonalQuote = GenerateSeasonalQuote()
	GenerateSeasonalQuote.main()