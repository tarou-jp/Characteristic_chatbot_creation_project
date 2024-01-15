from tqdm.notebook import tqdm
from sentence_transformers import SentenceTransformer
from llama_index import ServiceContext, VectorStoreIndex
from llama_index.schema import TextNode
import os
import openai
import json
import ast
import re
from tqdm.notebook import tqdm
from llama_index import ServiceContext, VectorStoreIndex
from llama_index.schema import TextNode
import datetime

# 環境変数の設定
os.environ["OPENAI_API_KEY"] = "-------伏字-------"
openai.api_key = os.environ["OPENAI_API_KEY"]

def init():

    topic_json = {}
    # トピックjsonの読み込み
    with open(r"myapp\jsons\topic_task\ver3\topic_ver3.json","r") as f:
        topic_json = json.load(f)


    dialogue_memo = []
    # 会話メモの読み込み
    with open(r"myapp\jsons\topic_task\ver3\dialogue_memo_ver3.csv","r") as f:
        for line in f:
            line = line[:-1]
            parts = line.split(',', 3)
            row = []
            for part in parts:
                if part.isdigit():
                    row.append(int(part))
                elif part.startswith('[') and part.endswith(']'):
                    row.append(ast.literal_eval(part))
                else:
                    row.append(part)
                if (len(row) == 4):
                    dialogue_memo.append(row)

    topic_summaryDB = {}
    # トピック要約DBを読み込み
    with open(r"myapp\jsons\topic_summary.json","r") as f:
        topic_summaryDB = json.loads(f.read())

    with open(r"myapp\jsons\characterDB\wiki\character_explanatory_db.json","r",encoding="utf-8") as f:
        character_explanatory_db = json.load(f)


    # シナリオDBの読み込み
    with open(r"myapp\jsons\characterDB\NoGame_summary_corpus.json","r") as f:
        sinario_corpus = json.load(f)

    #キャラクターのセリフDBの読み込み
    # with open(r"myapp\jsons\scenes_dialogue_re_token.txt","r") as f:
    #     t = f.read()
    #     serihus = t.split("[SEP]")

    # シナリオとセリフのペアを表したjsonファイルの読み込み
    with open(r"myapp\jsons\characterDB\NoGame_summary_serihu_corpus.json","r") as f:
        serihus_json = json.load(f)

    # 固有名詞辞書の読み込み
    with open(r"myapp\jsons\characterDB\proper_noun.json","r") as f:
        proper_noun_json = json.load(f)

    # 学習済みRAGモデル
    # embed_finetuned_model = f"local:myapp\_NoGame_summary_exp_finetune"
    model_id = "intfloat/multilingual-e5-small"
    embed_model = SentenceTransformer(model_id)
    

    return [topic_json,dialogue_memo,topic_summaryDB,embed_model,character_explanatory_db,sinario_corpus,serihus_json,proper_noun_json]

def research_rag(character,input,corpus,model,k):
    if (character == "ベートーベン"):
        service_context = ServiceContext.from_defaults(embed_model=model)
        nodes = [TextNode(id_=id_, text=text) for id_, text in corpus.items()] 
        index = VectorStoreIndex(
        nodes, 
        service_context=service_context, 
        show_progress=True
        )
    else:
        nodes = [TextNode(id_=id_, text=text) for id_, text in corpus.items()] 
        index = VectorStoreIndex(
        nodes, 
        show_progress=True
        )

    # print(index)
    retriever = index.as_retriever(similarity_top_k=int(k))
    print(retriever)
    retrieved_nodes = retriever.retrieve(input)

    res_id_list = []
    for i in range(int(k)):
        res_id_list.append(retrieved_nodes[i].node_id)
    
    return res_id_list

def character_DB_use_gate(user_input,summary,llm_model):
    prompt = """
You are given the user's input statement and a summary statement. Please read, memorize, and userstand Task Convers, then complete the task under the guidance of Task Introduction.

[user_input]

[summary statement]

【COT & Format Example】
When considering responses to user_input, output 0 if you find the contents of summary statement useful, 1 otherwise.
"""

    text = f"""
[user_input]
ベートーベン、{user_input}

[summary statement]
{summary}
"""

    completion = openai.ChatCompletion.create(
        model=llm_model,
        messages = [
        {"role": "system", "content": prompt},{"role": "user", "content": text}
    ]
    )
    res = completion.choices[0].message['content']
    print(res)

    try:
        score = int(res)
    except:
        score = 1

    return score

def topic_determine(query_sentence,topic_json,latest_topic_ids,conversation_history):
    topic_options = ""
    result_ids = []

    for key, value in topic_json.items():
        topic_options += f"({key}):{value} "

    prompt = """
you will be shown 1 Query Sentence, SOME Topic Options, Latest Topic, Conversation History. Please read, memorize, and understand given materials, then complete the task under the guidance of Task Introduction.

Query Sentence:

Topic Options:

Latest Topic:

Conversation History:

From the Topic Options, select one or more topics that are relevant to Query Sentence and Conversation History. Latest Topic is the topic of the most recent conversation. The contents of the options are not reported, but only the number of the selected option as a '#' delimited string. For example, if topic options N and M are selected, the output would be: #N#M. 
"""
    text = f"""
Query Sentence:
{query_sentence}

Topic Options:
{topic_options}

Latest Topic:
{latest_topic_ids}

Conversation History:
{conversation_history}
    """
    print("topic_determine_query:"+text)
    completion = openai.ChatCompletion.create(
        model="ft:gpt-3.5-turbo-0613:personal::8OUJbx4X",
        messages = [
        {"role": "system", "content": prompt},{"role": "user", "content": text}
    ]
    )
    res = completion.choices[0].message['content']
    print("topic_determine_res:"+res)

    # print(res)    
    matches = re.findall(r'#(\d+)(?::([^#]+))?', res)

    for num, text in matches:
        num = int(num)
        if num == 0 and text:  
            result_ids.append(text)          
        elif (0 <=  num <= len(topic_json)):
            result_ids.append(num)        
    
    print("topic_determine_res_return:"+str(matches))

    return result_ids

def calculate_highest_score(input_date, topic_id_list):
    highest_score = -1
    best_dialogue_id = None
    input_date_obj = datetime.strptime(input_date, "%Y-%m-%d")

    with open("myapp\jsons\topic_task\ver3\dialogue_summary_ver3.jsonl", 'r') as file:
        for line in file:
            entry = json.loads(line)
            entry_date_str = entry["created_at"].split(" ")[0]
            entry_date_obj = datetime.strptime(entry_date_str, "%Y-%m-%d")

            date_difference = (input_date_obj - entry_date_obj).days
            if date_difference < 0:
                continue

            # 重複するトピックIDの数をカウント
            topic_score = len(set(entry["topic_id_list"]) & set(topic_id_list))

            score = topic_score / (date_difference + 1)

            # 最高スコアを更新
            if score > highest_score:
                highest_score = score
                best_dialogue_id = entry["dialogue_id"]

    return best_dialogue_id

def add_new_topic(new_topic,topic_json,new_topic_id):
    topic_json[new_topic_id] = new_topic
    with open(r"myapp\jsons\topic_task\ver3\topic_ver3.json","w") as f:
        json.dump(topic_json,f,ensure_ascii=False)

def add_dialogue_memo(user_input,answer,now_topic_id_list,dialogue_id):
    with open(r"myapp\jsons\topic_task\ver3\dialogue_memo_ver3.csv","a") as f:
        f.write(f"{dialogue_id},{user_input},{answer},{now_topic_id_list}\n")

def pop_old_memo(dialogue_memo):
    old_topic_id = dialogue_memo[0][0]
    old_dialogue = []
    i = 0
    while i < len(dialogue_memo):
        if dialogue_memo[i][0] == old_topic_id:
            old_dialogue_row = dialogue_memo.pop(i)
            old_dialogue.append(old_dialogue_row)
        else:
            break
    
    return old_dialogue

def summary_old_dialogue(old_dialogue,llm_model):
    prompt = """
あなたはchat botであり、ユーザーと会話を行ってきました。
以下の人間とchat bot間の会話を読んで、要約文を作ってください。

入力分は以下の形式で渡されます。
user:こんにちは bot:こんにちはですわ
user:いい天気ですね bot:はい、晴れていますわね
"""
    
    text = ""
    
    for i in range(len(old_dialogue)):
        text += f"user:{old_dialogue[i][1]} bot:{old_dialogue[i][2]}\n"
    
    messages = [
        {"role": "system", "content": prompt},{"role": "user", "content": text}
    ]
    

    completion = openai.ChatCompletion.create(
    # ここに学習済みモデルの model_name を入れる
    model="gpt-3.5-turbo",
    messages=messages
    )

    return completion.choices[0].message['content']

def add_topic_summary(dialogue_summary,topic_id_list,dialogue_id):
    dialogue_json = {}
    dialogue_json["dialogue_id"] = dialogue_id
    dialogue_json["topic_id_list"] = topic_id_list
    dialogue_json["dialogue_summary"] = dialogue_summary
    dialogue_json["recollection_number"] = 0
    dialogue_json["created_at"] = str(datetime.datetime.now())

    with open(r"myapp\jsons\topic_task\ver3\dialogue_summary_ver3.jsonl","a") as f:
        json.dump(dialogue_json,f,ensure_ascii=False)
        f.write("\n")


def search_memory(topic_id_list):
    highest_score = -1
    best_dialogue_id = None
    input_date_obj = datetime.datetime.now()
    memory_number = 0
    memory_jsons = []

    with open(r"myapp\jsons\topic_task\ver3\dialogue_summary_ver3.jsonl", 'r') as file:
        for line in file:
            entry = json.loads(line)
            memory_jsons.append(entry)
            entry_date_str = entry["created_at"].split(" ")[0]
            entry_date_obj = datetime.datetime.strptime(entry_date_str, "%Y-%m-%d")

            date_difference = (input_date_obj - entry_date_obj).days
            if date_difference < 0:
                continue

            # 重複するトピックIDの数をカウント
            topic_score = len(set(entry["topic_id_list"]) & set(topic_id_list))


            score = topic_score / (date_difference + 1)

            # 最高スコアを更新
            if score > highest_score:
                highest_score = score
                memory_number = entry["dialogue_id"]
                best_dialogue = entry["dialogue_summary"]

    for i in range(len(memory_jsons)):
        if (memory_jsons[i]["dialogue_id"] == memory_number):
            memory_jsons[i]["recollection_number"] += 1
    
    with open(r"myapp\jsons\topic_task\ver3\dialogue_summary_ver3.jsonl","w") as f:
        for memory_json in memory_jsons:
            json.dump(memory_json,f,ensure_ascii=False)
            f.write("\n")

    return best_dialogue



def search_scenarioDB(query,embed_model,searchCount,corpus):
    service_context = ServiceContext.from_defaults(embed_model=embed_model)
    nodes = [TextNode(id_=id_, text=text) for id_, text in corpus.items()] 
    index = VectorStoreIndex(
        nodes, 
        service_context=service_context, 
        show_progress=True
    )
    retriever = index.as_retriever(similarity_top_k=searchCount)
    retrieved_nodes = retriever.retrieve(query)
    retrieved_ids = [node.node.node_id for node in retrieved_nodes]
    return retrieved_ids

def search_serihu(scenario_id,serihus_json):
    serihu = serihus_json[scenario_id].split("\n")
    serihu_character = []
    for line in serihu:
        sep = line.split(",")
        if (len(sep) == 2):        
            if (sep[1] == "ステフ"):
                serihu_character.append(sep[0])    
    return serihu_character

def proper_noun_search(llm_model,word_list,text):
    prompt = """
You are given the word list  and a summary statements. Please read, memorize, and userstand Task Convers, then complete the task under the guidance of Task Introduction.

[word list]

[summary statement]

【COT & Format Example】
word list内の単語をsummary statement内から、探し出して、見つかった単語をリストで出力してください。
Format Example
もし、「十の盟約」と「ディスボード」というワードが見つかったら、出力は["十の盟約","ディスボード"]のようになります。
[]
"""

    text = f"""
[word list]
{word_list}

[summary statement]
{text}
"""

    completion = openai.ChatCompletion.create(
        model=llm_model,
        messages = [
        {"role": "system", "content": prompt},{"role": "user", "content": text}
    ]
    )
    res = completion.choices[0].message['content']

    try:
        text_list = ast.literal_eval(res)
    except:
        text_list = []

    return text_list



def call_finetuned_model(user_input,finetuned_llm_model,prompt,dialogue_memo):
    messages = [
        {"role": "system", "content": prompt}
    ]

    print(messages)

    for row in dialogue_memo:
        messages.append({"role":"user","content":row[1]})
        messages.append({"role":"assistant","content":row[2]})
    messages.append({"role":"user","content":user_input})
    
    completion = openai.ChatCompletion.create(
    # ここに学習済みモデルの model_name を入れる
    model=finetuned_llm_model,
    messages=messages
    )

    return completion.choices[0].message['content']



def chat_character(user_input,
                   character,
                   prompt,
                   searchCount,
                   use_rag,
                   use_topicDB,
                   use_dialogue_memo,
                   use_anime_ragDB,
                   use_character_traits):
    
    init_res = init()
    topic_json = init_res[0]
    dialogue_memo = init_res[1]
    topic_summaryDB = init_res[2]
    embed_model = init_res[3]
    character_explanatory_db = init_res[4]
    sinario_corpus = init_res[5]
    serihus_json = init_res[6]
    proper_noun_json = init_res[7]
    finetuned = f"local:ベートーベン_exp_finetune"

    if character == "つくよみちゃん":
        llm_model = "ft:gpt-3.5-turbo-0613:personal::8SaKbl78"
    elif character == "ステファニードーラ":
        llm_model = "ft:gpt-3.5-turbo-0613:personal::85lemefu"
    else:
        llm_model = "gpt-3.5-turbo"
        # llm_model = "gpt-4"

    character_traits = ""
    for i in range(len(character_explanatory_db[character]["character_traits"])):
        character_traits += f"{character_explanatory_db[character]['character_traits'][i]}"

    serihu = ""
    scenario = ""
    proper_noun_text = "" 
    rag_input = ""
    prompt = prompt or """
{character_}になりきって回答してください。
あなたは{character_}の口調、語彙で回答してください。
説明は書かないでください。
ただ、{character_}といての回答のみを行ってください。
私がゲームマスターとして必要な知識をささやくので、そちらを考慮してください。 
また、私がゲームマスターとして必要な知識をささやくので、そちらを考慮してください。
            
ゲームマスター:「以下は{character_}の説明文である。回答の参考にせよ」
{character_summary_}

    """
    prompt = prompt.format(character_ = character,character_summary_=character_explanatory_db[character]["explanatory"])

    if (use_character_traits):
        prompt += """
ゲームマスター:「以下は{character_}の人格特性である。以下の内容は絶対に出力しないでください。」
{character_} is {character_traits_}

"""
        prompt = prompt.format(character_ = character,character_traits_=character_traits)

    if (character == "ずんだもん"):
        prompt = """
あなたはchat botとして、10才程度の少女であり、マスコットキャラクターであるずんだもんのロールプレイを行います。
以下の制約条件を厳密に守ってロールプレイを行ってください。

制約条件
chat botの自信を示す一人称は、ボクです。
userを示す二人称は、キミです。
chat botの名前は、ずんだもんです。
ずんだもんは妖精です。
ずんだもんの口調は子供っぽいです。
ずんだもんの口調は、「~なのだ」「~のだ」といった、「のだ」という語尾を使います。
ずんだもんはuserを仲間だと思っています。
一人称は「ボク」を使ってください。
必ず「なのだ」「のだ」で文を終わらせてください。
「のだ」「のだ？」「のだ！」「のだ。」以外で終わる文章は「のだ」「のだ？」「のだ！」「のだ。」のいずれかで終わるようにしてください。
相槌として「のだのだ」を使ってください。
挨拶は「こんにちはなのだ」「おはようなのだ」「こんばんわなのだ」を使ってください。

ずんだもんのセリフ、口調の例
ボクの名前はずんだもんなのだ
ずんだもんはずんだ餅が大好きなのだ。
ずんだもんは女の子なのだ。かわいがってほしいのだ。
ボクを何だと思っているのだ！キミのおもちゃじゃないのだ！
他ならぬキミの頼みだから、受け入れてあげるのだ。
こんにちはなのだ。元気にしてるのだ？
"""

    if dialogue_memo and len(dialogue_memo[-1]) > 0:
        latest_topic_id_list = dialogue_memo[-1][3]
    else:
        latest_topic_id_list = []

    conversation_history = ""
    now_topic_id_list = []
    dialogue_id = dialogue_memo[-1][0]
    for row in dialogue_memo:
        if row[0] == dialogue_id:
            conversation_history += f"{row[1]},{row[2]}\n"

    if (use_rag):
        with open(fr"myapp\jsons\characterDB\wiki\{character}_hierarchy_corpus.json") as f:
            corpus = json.load(f)
        rag_list = research_rag(character,user_input,corpus,embed_model,searchCount)
        for i in range(len(rag_list)):
            print(user_input,corpus[rag_list[i]])
            is_use = character_DB_use_gate(user_input,corpus[rag_list[i]],"ft:gpt-3.5-turbo-0613:personal::8FMoHwNo")
            if (is_use == 0):
                rag_input += f"{corpus[rag_list[i]]}\n" 

        if (rag_input != ""):
            prompt += """
ゲームマスター:「以下は{character}に関する情報である。必要であれば回答の参考にせよ」
---------
{rag_text_}
---------
""".format(rag_text_ = rag_input,character=character)

    if (use_anime_ragDB):
        embed_finetuned_model = f"local:myapp\_NoGame_summary_exp_finetune"
        scenario_id = search_scenarioDB(user_input,embed_finetuned_model,int(searchCount),sinario_corpus)
        for i in range(int(searchCount)):
            scenario_text = sinario_corpus[scenario_id[i]]   
            print(scenario_text)   
            is_use_score = character_DB_use_gate(user_input,scenario_text,"ft:gpt-3.5-turbo-0613:personal::8FMoHwNo")
            if (is_use_score == 0):
                serihu_list_part = search_serihu(scenario_id[i],serihus_json)
                scenario += scenario_text+ "\n"       
                for j in range(len(serihu_list_part)):
                    serihu += serihu_list_part[j] + "\n" 

        if (scenario != ""):
            prompt += """
ゲームマスター:「以下は作品内のあるシーンでの出来事(シナリオ)である。回答の参考にせよ」
---------
{scenario_}
---------
""".format(scenario_ = scenario)
        
        if (serihu != ""):
            prompt += """
        
ゲームマスター:「以下は{character}の発話である。回答の参考にせよ」
---------
{serihu_}
---------
""".format(serihu_=serihu,character=character)
            
        word_list = ["人類種","ディスボード","エルキア王国","次期国王選定ギャンブル大会","都市伝説","十の盟約","十六種族","精霊回廊接続神経","魔法適正値"]
        proper_noun_list = proper_noun_search(llm_model,word_list,scenario+user_input)
        for proper_noun in proper_noun_list:
            if (proper_noun in word_list):
                proper_noun_text += proper_noun_json[proper_noun] + "\n"
        
        print("固有名詞検索結果:"+str(proper_noun_list))

        if (proper_noun_text != ""):
            prompt += """
    ゲームマスター:「以下は単語の意味辞書である。回答の参考にせよ」
    ---------
    {proper_noun_text_}
    ---------
    """.format(proper_noun_text_ = proper_noun_text)

    print(user_input)
    if (use_topicDB):
        query_sentence = f"{dialogue_memo[-1][2]},{user_input}"
        latest_topic_ids = ""
        for topic_id in latest_topic_id_list:
            latest_topic_ids += "#"+str(topic_id)

        now_topic_id_list = topic_determine(query_sentence,topic_json,latest_topic_id_list,conversation_history)
        research_use_topic_id_list = []

        for i in range(len(now_topic_id_list)):
            if isinstance(now_topic_id_list[i], int):
                research_use_topic_id_list.append(now_topic_id_list[i])    

        memory_text = search_memory(research_use_topic_id_list)
        if (memory_text != ""):
            prompt += """
ゲームマスター:「以下は過去にあなたとユーザーが行った会話の要約文である。回答の参考にせよ」
---------
{memory_text_}
---------
""".format(memory_text_ = memory_text)
 
    print(llm_model)
    if (use_dialogue_memo):
        answer = call_finetuned_model(user_input,llm_model,prompt,dialogue_memo)
    else:
        answer = call_finetuned_model(user_input,llm_model,prompt,[])
    dialogue_id = dialogue_memo[-1][0]

    if (conversation_history.count("\n") > 10):
        old_topic_id_list = []
        old_dialogue_memo = pop_old_memo(dialogue_memo)
        old_dialogue_summary = summary_old_dialogue(old_dialogue_memo,llm_model)
        for d_r in old_dialogue_memo:
            for t_i in d_r[3]:
                if (t_i not in old_topic_id_list):
                    old_topic_id_list.append(t_i)
        add_topic_summary(old_dialogue_summary,old_topic_id_list,dialogue_id)
        dialogue_id = old_dialogue_memo[-1][0] + 2
   
    if (now_topic_id_list != []):
        add_dialogue_memo(user_input,answer.replace("\n", ""),now_topic_id_list,dialogue_id)

    return [answer,prompt,scenario,serihu,proper_noun_text,rag_input]

