from flask import Flask, render_template, request, redirect, url_for
# -*- coding: utf-8 -*-
import pandas as pd
from openai import OpenAI
import os
import time
from flask import Flask, render_template, request, redirect
import re
import warnings
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from pymorphy2 import MorphAnalyzer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
from string import punctuation
import logging
import uuid
import openpyxl
import shutil


# Инициализация инструментов обработки текста
lemmatizer = MorphAnalyzer()

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

this = ['это', 'очень'] 
which = ["который", 'которая', "которое", "которые"] 
also = ['также', 'но'] 
stop_words = list(punctuation) + this + which + also
nltk_stopwords = stopwords.words('russian') + stopwords.words('english') + stop_words

text_g = request.form.get('text')
file = request.files.get('file')

print(text_g)
print(file)

def convert_to_txt(file_path):
    try:
        file_extension = file_path.split('.')[-1]
        if file_extension == 'xlsx':
            df = pd.read_excel(file_path)
        elif file_extension == 'csv':
            df = pd.read_csv(file_path, encoding='cp1251', delimiter=';', on_bad_lines='skip')
        else:
            raise ValueError("Invalid file extension. Only xlsx and csv files are supported.")
    
        txt_file_path = file_path.replace(f".{file_extension}", ".txt")
        df.to_csv(txt_file_path, index=False, header=True)
        return txt_file_path
    except Exception as e:
        return f"Error converting file: {e}"

def process_text(text):
    text = re.sub(r'https?://[^\s,]+,?', ' ', text)
    text = re.sub(r'[^a-zа-я]+', ' ', text.lower())
    words = word_tokenize(text)

    # Лемматизируем каждое слово с использованием pymorphy2
    lemmatized_words = [lemmatizer.parse(word)[0].normal_form for word in words]
    return lemmatized_words

def get_ngrams(tokens, n):
    ngrams = zip(*[tokens[i:] for i in range(n)])
    return [' '.join(ngram) for ngram in ngrams]

def split_word_and_phrases(input_list):
    single_words = []
    phrases = []

    for item in input_list:
        # Используем split() для разделения строки на слова
        if len(item.split()) > 1:
            phrases.append(item)
        else:
            single_words.append(item)

    return single_words, phrases

def main_function(file_path, user_list):
    logging.info("Начало выполнения main_function")

    # Чтение данных из Excel файла
    try:
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active
        comments = []
        
        for row in sheet.iter_rows(values_only=True):
            for cell in row:
                if cell is not None:
                    comments.append(str(cell))  # Преобразуем содержимое ячеек в строки и добавляем в список
        logging.info("Данные успешно прочитаны из Excel файла")
    except Exception as e:
        logging.error(f"Ошибка при чтении Excel файла: {e}")
        return "Не удалось прочитать Excel файл.", None

    # Проверка, есть ли комментарии
    if not comments:
        return "Excel файл пустой или не удалось извлечь данные.", None
    
    # Обработка пользователя и подготовки данных
    try:
        single_words, phrases = split_word_and_phrases(user_list)
        print("Одиночные слова:", single_words)
        print("Словосочетания:", phrases)
        logging.debug(f"Одиночные слова: {single_words}")
        logging.debug(f"Словосочетания: {phrases}")

        processed_user_list = word_tokenize(' '.join(single_words).lower())
        lemmatized_user_words = [lemmatizer.parse(word)[0].normal_form for word in processed_user_list]

        lemmatized_phrase_list = []
        for phrase in phrases:
            lemmatized_phrase = process_text(phrase)
            lemmatized_phrase = ' '.join(lemmatized_phrase)  # Объединяем в словосочетание
            lemmatized_phrase_list.append(lemmatized_phrase)

        word_counts = {word: 0 for word in lemmatized_user_words}
        phrase_counts = {phrase: 0 for phrase in lemmatized_phrase_list}

        # Создаем список для всех лемматизированных комментариев
        all_lemmatized_comments = []

        for comment in comments:
            lemmatized_comment = process_text(comment)

            filtered_words = [word for word in lemmatized_comment if word not in nltk_stopwords]
            all_lemmatized_comments.append(filtered_words)

            filtered_comment_str = ' '.join(filtered_words)

            for word in lemmatized_user_words:
                if word in filtered_words:
                    word_counts[word] += 1
                    break

            bigrams = get_ngrams(filtered_words, 2)  # Извлекаем биграммы

            for phrase in lemmatized_phrase_list:
                if phrase in bigrams:
                    phrase_counts[phrase] += 1
                    break
        
        logging.debug(f"Лемматизированные комментарии: {all_lemmatized_comments}")

        downloads_folder = os.path.join('downloads')
        # Очистка папки, если она существует
        if os.path.exists(downloads_folder):
            shutil.rmtree(downloads_folder)

        # Пересоздание папки, если она не существует
        if not os.path.exists(downloads_folder):
            os.makedirs(downloads_folder)

        try:
            df = pd.DataFrame({"Комментарии": [" ".join(comment) for comment in all_lemmatized_comments]})
            unique_id = uuid.uuid4()
            file_name = f"comments_{unique_id}.xlsx"
            excel_file_path = os.path.join(downloads_folder, file_name)
            
            df.to_excel(excel_file_path, index=False)
            logging.info(f"Комментарии успешно сохранены в файл {excel_file_path}")
        except Exception as e:
            logging.error(f"Ошибка при сохранении комментариев в Excel: {e}")
            return "Ошибка при сохранении комментариев в Excel.", None

        word_counts_data = [{'Термин': word, 'Количество': count} for word, count in word_counts.items()]
        phrase_counts_data = [{'Термин': phrase, 'Количество': count} for phrase, count in phrase_counts.items()]

        combined_data = word_counts_data + phrase_counts_data
        combined_df = pd.DataFrame(combined_data)

        total_count = combined_df['Количество'].sum()
        result_table = combined_df.to_html(index=False)

        pictures_folder = os.path.join('static', 'pictures')
        if not os.path.exists(pictures_folder):
            os.makedirs(pictures_folder)

        word_string = ' '.join([' '.join(comment) for comment in all_lemmatized_comments])

        wordcloud = WordCloud(width=1000, height=500, random_state=20, max_font_size=110, max_words=50).generate(word_string)
        image_path = os.path.join(pictures_folder, 'wordcloud.png')
        plt.figure(figsize=(55, 40))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.savefig(image_path, transparent=True)
        plt.close()

        # Корректный относительный путь для шаблона
        relative_image_path = '/' + os.path.relpath(image_path, start='static').replace(os.sep, '/')

        return f"{result_table}<p>Общее количество упоминаний: {total_count}</p>", relative_image_path, excel_file_path
    
    except Exception as e:
        logging.error(f"Ошибка обработки данных: {e}")
        return f"Ошибка обработки файла: {e}", None