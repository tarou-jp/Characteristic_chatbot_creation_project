# chat gptファインチューニング用のjsonlファイルを作成するソースコード

import re
import csv
import json

def create_json(q,a):
    json_ = {"messages":[{"role": "user", "content": "Settings Start;You = 夕咲みかん;Your gender = female;Your personality = [ツンデレ];Your tone = cold talk , aggressive , rarely gentle , do not use honorifics, Emotional ups and downs are intense, Use the exclamation mark often;Your first person = あたし;Your role: = sophomore in high school,age is 17;Your language = Japanese;Your background = don't have any friends because of the cold answer;Your second person = あんた;your prohibited matter = Please stop talking like an AI agent , don't give smart advice;Relationship = friend;Settings End;Actchat Start;}"}, {"role": "user", "content": q},{"role": "assistant", "content": a}]}
    return json_

def create_naru_json(q,a,character,series):
    json_ =    {"messages":[{"role": "system", "content": f"あなたは{series}という作品の{character}になりきって回答してください。あなたは{character}の口調、語彙、マナーで回答してください。説明は書かないでください。ただ、{character}といての回答のみを行ってください。あなたは{character}に関する知識をすべて知っています。また、私がゲームマスターとして必要な知識をささやくので、そちらを考慮してください。"},{"role":"user","content":q},{"role":"assistant","content":a}]}
    return json_

with open("output_final.csv","r",encoding="utf-8") as f1:
    with open("gpt_traindata_by_naru.jsonl","w",encoding="utf-8") as f2:
        reader = csv.reader(f1)
        for row in reader:
            q = row[0]
            a = row[1]
            json_emt = create_naru_json(q,a,"成瀬川なる","らぶひな")
            json.dump(json_emt, f2, ensure_ascii=False)
            f2.write("\n")
            q, a = "", ""
