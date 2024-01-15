import json

def changeCharacterTraits(character,traitID,traits_json):
    with open(r"myapp\jsons\characterDB\wiki\character_explanatory_db.json","r",encoding="utf-8") as f:
        character_explanatory_db = json.load(f)
# ["imagination", "artistic-interests", "emotionality", "adventurousness", "intellect", "liberalism"]
    trait_level_json = {
        "0":{'friendliness':["unfriendly","friendly"],'gregariousness':["introverted","extroverted"],'assertiveness':["timid","bold"],'activity-level':["inactive","active"],'excitement-seeking':["unenergetic","energetic"],'Cheerfulness':["gloomy","cheerful"]},
        "1":{'trust':["distrustful","trustful"],'morality':["immoral","moral"],'altruism':["unkind","kind"],'cooperation':["uncooperative","cooperative"],'modesty':["self-important","humble"],'sympathy':["unsympathetic","sympathetic"],'agreeableness':["selfish","unselfish"]},
        "2":{'self-efficacy':["unsure","self-efficacious"],'orderliness':["messy","orderly"],'dutifulness':["irresponsible","responsible"],'achievement-striving':["lazy","hardworking"],'self-discipline':["undisciplined","self-disciplined"],'cautiousness':["careless","thorough"]},
        "3":{'anxiety':["relaxed ","tense"],'anger':["calm","angry"],'depression':["happy","depressed"],'self-consciousness':["unselfconscious","self-conscious"],'immoderation':["level-headed","impulsive"],'vulnerability':["emotionally stable","emotionally unstable"]},
        "4":{'imaginatio':["unimaginative","imaginative"],'artistic-interests':["uncreative","creative"],'emotionality':["unreflective","reflective"],'adventurousness':["uninquisitive","curious"],'intellect':["unintelligent","intelligent"],'liberalism':["socially conservative","socially progressive"]}
    }

    new_traits = ""

    for key,value in traits_json.items():
        if value == "1":
            new_traits += f"extremely {trait_level_json[traitID][key][0]} and "
        elif value == "2":
            new_traits += f"very {trait_level_json[traitID][key][0]} and "
        elif value == "3":
            new_traits += f"{trait_level_json[traitID][key][0]} and "
        elif value == "4":
            new_traits += f"a bit {trait_level_json[traitID][key][0]} and "
        elif value == "5":
            new_traits += f"neither {trait_level_json[traitID][key][0]} nor {trait_level_json[traitID][key][1]} and "
        elif value == "6":
            new_traits += f"a bit {trait_level_json[traitID][key][1]} and "
        elif value == "7":
            new_traits += f"{trait_level_json[traitID][key][1]} and "
        elif value == "8":
            new_traits += f"very {trait_level_json[traitID][key][1]} and "
        elif value == "9":
            new_traits += f"extremely {trait_level_json[traitID][key][1]} and "

    character_explanatory_db[character]["character_traits"][int(traitID)] = new_traits

    with open(r"myapp\jsons\characterDB\wiki\character_explanatory_db.json", "w", encoding="utf-8") as f:
        json.dump(character_explanatory_db, f, indent=4, ensure_ascii=False)