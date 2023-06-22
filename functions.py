from werkzeug.utils import secure_filename
import sys
from database import *
import os 
from tempfile import TemporaryDirectory

ALLOWED_EXTENSIONS = {"txt", "csv", "tsv"}

# NOT FULLY IMPLEMENTED
def valid_file(request):
    if "file" not in request.files:
        print("not valid")
        return False
    
    file = request.files["file"]
    if file.filename == "":
        return ("error", "No file")

    if file and allowed_extensions(file.filename):
        filename = secure_filename(file.filename)
    else:
        return ("error", "File type not allowed")

# Check file extension against allowed extensions
def allowed_extensions(filename):
    if "." in filename:
        extension = filename.rsplit(".", 1)[1].lower()
        return extension in ALLOWED_EXTENSIONS
    else:
        return False


def get_usr_vocabulary(file, filename):
    with TemporaryDirectory() as tmpdir:
        file.save(os.path.join(tmpdir, filename))

        with open(os.path.join(tmpdir, filename), "r+", encoding="utf-8") as input:            
            usr_vocabulary = input.read().splitlines()
    
    return usr_vocabulary

def get_tables(language):
    tables = {}
    if language == "japanese":
                tables["dictionary_tbl"] = dictionaryJP
                tables["level_tbl"] = levelJP
                tables["sentence_tbl"] = sentencesJP
                tables["translation_tbl"] = transJP_EN
            
    elif language == "mandarin":
                tables["dictionary_tbl"] = dictionaryCN
                tables["level_tbl"] = levelCN
                tables["sentence_tbl"] = sentencesCN
                tables["translation_tbl"] = transCN_EN
    else:
        return "No tables found"

    return tables

#dictionary_entry = db.session.query(dictionaryJP.id).filter(dictionaryJP.word == query_word).first()
#word_level = db.session.query(levelJP.grade).filter(levelJP.dict_id == dictionary_entry).first()[0]
def find_sentences(tables, word, translation):

    if translation == "none":
        query_results = tables["sentence_tbl"]\
                        .query.with_entities(tables["sentence_tbl"].sentence, tables["sentence_tbl"].transcription)\
                        .filter(tables["sentence_tbl"].tokens.contains(word), tables["sentence_tbl"].grade <= 5)\
                        .order_by(tables["sentence_tbl"].grade.desc(), tables["sentence_tbl"].frequency)\
                        .limit(5)\
                        .all()
        query_results =  [r._asdict() for r in query_results]
        return query_results

    elif translation == "en":
        query_results = db.session\
                    .query(tables["sentence_tbl"].sentence, tables["sentence_tbl"].transcription, sentencesEN.sentence.label("translation"))\
                    .join(tables["translation_tbl"], tables["sentence_tbl"].id==tables["translation_tbl"].jp_id)\
                    .join(sentencesEN, tables["translation_tbl"].en_id==sentencesEN.id)\
                    .filter(tables["sentence_tbl"].tokens.contains(word))\
                    .limit(5)\
                    .all()
        query_results =  [r._asdict() for r in query_results]
        return query_results

def selectedSentence(query_results, word):
    
    print(query_results)

    if bool(query_results):
        query_results[0]

    return query_results
