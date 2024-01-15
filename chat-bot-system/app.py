from flask import Flask, render_template, jsonify, request
import chat_bot_wiki as chat_bot
import rag_corpus_create
import change_character_traits
import json

app = Flask(__name__)

@app.route('/')
def index():
    with open('myapp\jsons\characterDB\wiki\character_explanatory_db.json', 'r', encoding='utf-8') as file:
        characters_db = json.load(file)
        characters = [key for key,value in characters_db.items()]
    return render_template('index.html', characters=characters)
    # return render_template('index.html')

@app.route('/get-response', methods=['POST'])
def get_response():
    user_message = request.json.get('message')
    setting = request.json.get("settings")
    character = request.json.get("character")
    prompt = setting["text"]
    ragDB = setting["db1"]
    dialogue_memo = setting["db2"]
    animeDB = setting["db5"]
    topicDB = setting["db4"]
    character_traits = setting["db3"]
    searchCount = request.json.get("searchCount")
    if (user_message == ""):
        return jsonify({'message': "文字を入力してください。","prompt": "文字を入力してください。","scenario": "文字を入力してください。","serihu":"文字を入力してください。","noun":"文字を入力してください。","topic":"文字を入力してください。"})
    else:
        res = chat_bot.chat_character(user_message,character,prompt,searchCount,ragDB,topicDB,dialogue_memo,animeDB,character_traits)
        message = res[0]
        prompt = res[1]
        scenario = res[2]
        serihu = res[3]
        noun = res[4]
        if (animeDB):
            rag_input = "---シナリオ検索結果---\n"+scenario.replace("[SEP]", "")+"\n"+"---セリフ検索結果---"+serihu
        else:
            rag_input = res[5]

        return jsonify({'message': message,"prompt": prompt,"scenario": scenario,"serihu":serihu,"noun":noun,"rag_input":rag_input})
    
@app.route('/create-character', methods=['POST'])
def create_character():
    character_name = request.json.get('name')
    rag_corpus_create.research_wiki(character_name)
    return jsonify({"message": "キャラクターが作成されました"}), 200

@app.route('/change-character-traits', methods=['POST'])
def change_traits():
    traitID = request.json.get('id')
    traits_json = request.json.get('traits_json')
    character = request.json.get('character')
    change_character_traits.changeCharacterTraits(character,traitID,traits_json)
    return jsonify({"message": "キャラクターが作成されました"}), 200

if __name__ == '__main__':
    app.run(debug=True)