# wikiから情報取得
from llama_index.text_splitter import SentenceSplitter
from llama_index.node_parser import SimpleNodeParser
import wikipedia
import json
import re
import uuid
import os
import openai
from llama_index.schema import MetadataMode
import json
from llama_index import SimpleDirectoryReader

# 環境変数の設定
os.environ["OPENAI_API_KEY"] = "-------伏字-------"
openai.api_key = os.environ["OPENAI_API_KEY"]

big5 = [["unfriendly","friendly","introverted","extroverted","timid","bold",'activity-level',"inactive","active","unenergetic","energetic","gloomy","cheerful"],
        ["distrustful","trustful","immoral","moral","unkind","kind","uncooperative","cooperative","self-important","humble","unsympathetic","sympathetic","selfish","unselfish"],
        ["unsure","self-efficacious","messy","orderly","irresponsible","responsible","lazy","hardworking","undisciplined","self-disciplined","careless","thorough"],
        ["relaxed ","tense","calm","angry","happy","depressed","unselfconscious","self-conscious","level-headed","impulsive","emotionally stable","emotionally unstable"],
        ["unimaginative","imaginative","uncreative","creative","unreflective","reflective","uninquisitive","curious","unintelligent","intelligent","socially conservative","socially progressive"]
    ]

adjective = ["外向性","協調性","誠実性","神経症傾向","経験への開放性"]

def research_wiki(name):
    wikipedia.set_lang("ja")
    res = wikipedia.search(name)
    title = res[0]

    wp = wikipedia.page(title)
    wp_content = wp.content

    wp_content_list = wp_content.split("\n\n\n")

    wp_content_list_after_scrutiny = []

    for content in wp_content_list:
        wp_content_list_after_scrutiny.append(content)

    summary = wp_content_list_after_scrutiny[0]

    corpus = extract_hierarchy(wp_content_list_after_scrutiny)
    character_traits = create_character_trait(name,summary)

    # コーパスの保存
    with open(fr"myapp\jsons\characterDB\wiki\{name}_hierarchy_corpus.json", "w",encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False)

    with open(r"myapp\jsons\characterDB\wiki\character_explanatory_db.json","r",encoding="utf-8") as f:
        character_explanatory_db = json.load(f)

    character_explanatory_db[name] = {"explanatory":summary,"character_traits":character_traits}

    with open(r"myapp\jsons\characterDB\wiki\character_explanatory_db.json", "w", encoding="utf-8") as f:
        json.dump(character_explanatory_db, f, indent=4, ensure_ascii=False)
    
    return None



# 取得したwikiページ内データを保存
# with open(fr"data\{name}_plane.txt","w") as f:
#     f.write(wp_content)


# weki内のテキストを構造化したjsonに変換する関数
def extract_hierarchy(texts):
    hierarchy = {}
    current_parent = None
    ng_list = ["脚注","参考文献","関連項目","外部リンク"]

    for text in texts:
        parent_match = re.search(r'^==\s(.*?)\s==', text)
        subsec_match = re.search(r'^===\s(.*?)\s===', text)

        # ノードパーサーの準備
        text_splitter = SentenceSplitter(
            chunk_overlap = 20,
            paragraph_separator="\n",
        )
        node_parser = SimpleNodeParser.from_defaults(
            text_splitter=text_splitter
        )


        if parent_match:
            # 親コンテンツを処理
            current_parent = parent_match.group(1)
            if (current_parent not in ng_list and len(text) -len(current_parent) > 20 ):
                splited_text = text.split("\n\n")
                # print([text[7+len(current_parent):]])

                for i in range(len(splited_text)):
                    if (len(splited_text[i]) > 100):
                        with open("test.txt","w") as f:
                            f.write(splited_text[i])
                        documents = SimpleDirectoryReader(
                            input_files=["test.txt"]
                        ).load_data()
                        nodes = node_parser.get_nodes_from_documents(documents)
                        for node in nodes:
                            # print(len(node.get_content(metadata_mode=MetadataMode.NONE)))
                            hierarchy[str(uuid.uuid4())] = node.get_content(metadata_mode=MetadataMode.NONE)
                    elif i != len(splited_text) -1 and len(splited_text[i]) <= 20:
                        splited_text[i+1] += splited_text[i]


        elif subsec_match and current_parent:
            # サブコンテンツを処理
            if (current_parent not in ng_list and len(text) -len(current_parent) > 20):
                splited_text = text.split("\n\n")
                # print([text[7+len(current_parent):]])

                for i in range(len(splited_text)):
                    if (len(splited_text[i]) > 100):
                        with open("test.txt","w") as f:
                            f.write(splited_text[i])
                        documents = SimpleDirectoryReader(
                            input_files=["test.txt"]
                        ).load_data()
                        nodes = node_parser.get_nodes_from_documents(documents)
                        for node in nodes:
                            # print(len(node.get_content(metadata_mode=MetadataMode.NONE)))
                            hierarchy[str(uuid.uuid4())] = node.get_content(metadata_mode=MetadataMode.NONE)
                    elif i != len(splited_text) -1 and len(splited_text[i]) <= 20:
                        splited_text[i+1] += splited_text[i]

    return hierarchy

def create_character_trait(text,character):
    responses = []

    for i in range(5):
        prompt = f"""
{text}

上の文章を読み、{character}の人格特性を決定してください。
人格特性の決め方として、まず{character}の{adjective[i]}を示す形容詞を以下から選んでください。
出力は、選ばれた形容詞群を,で区切る用にしてください。
説明は書かないでください。ただ選ばれた形容詞のみ出力してください。
例){big5[i][0]},{big5[i][3]}

{big5[i]} 
"""
        messages = [{"role": "system", "content": prompt}]
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",messages=messages)
        row = completion.choices[0].message['content'].split(",")
        character_traits = ""
        for i in range(len(row)):
            character_traits += row[i].strip("' \t") + " and "

        responses.append(character_traits)

    return responses

research_wiki("三島由紀夫")