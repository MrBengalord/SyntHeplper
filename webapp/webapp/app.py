import sys, json
from flask import Flask, render_template, send_file
from flask_flatpages import FlatPages, pygments_style_defs
from flask_frozen import Freezer
from flask import request
import pandas as pd
import numpy as np
from openai import OpenAI
import builtins
import runpy
import os
import shutil
from collections.abc import Mapping

DEBUG = True
FLATPAGES_AUTO_RELOAD = DEBUG
FLATPAGES_EXTENSION = '.md'
FLATPAGES_ROOT = 'content'
POST_DIR = 'posts'
PORT_DIR = 'result1'
DIR_RESULT = 'result'
DIR_RESULT_1 = 'result_1'
DIR_RESULT4 = 'result4'

app = Flask(__name__)
flatpages = FlatPages(app)
freezer = Freezer(app)
app.config.from_object(__name__)


def run_script(script_path, **kwargs):
    # 1. Установим параметры в builtins для доступа в скрипте
    for key, value in kwargs.items():
        setattr(builtins, key, value)
    
    # 2. Выполним скрипт
    runpy.run_path(script_path)

    # 3. Получим результат из builtins
    result = getattr(builtins, 'result', None)
    
    # 4. Чистка builtins
    for key in kwargs.keys():
        delattr(builtins, key)
    if result is not None:
        delattr(builtins, 'result')
    
    return result

def clear_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

def get_latest_file(directory):
    # Получаем список файлов в указанной директории
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    
    if not files:  # Если файлов нет, возвращаем None
        return None

    # Находим путь к файлу с максимальным временем изменения
    latest_file = max(files, key=os.path.getmtime)
    return latest_file


@app.route("/")
def index():
    posts = [p for p in flatpages if p.path.startswith(POST_DIR)]
    posts.sort(key=lambda item: item['date'], reverse=True)
    cards = [p for p in flatpages if p.path.startswith(PORT_DIR)]
    cards.sort(key=lambda item: item['title'])

    with open('settings.txt', encoding='utf8') as config:
        data = config.read()
        settings = json.loads(data)
    tags = set()
    for p in flatpages:
        t = p.meta.get('tag')
        if t:
            tags.add(t.lower())

    return render_template('index.html', posts=posts, cards=cards, bigheader=True, **settings, tags=tags)

@app.route('/posts/<name>/')
def post(name):
    path = '{}/{}'.format(POST_DIR, name)
    post = flatpages.get_or_404(path)
    return render_template('post.html', post=post)

@app.route('/result/')
def result(name):
    path = '{}/{}'.format(DIR_RESULT, name)
    result = flatpages.get_or_404(path)

    return render_template('result.html', result=result)

@app.route('/result1/')
def result1(name):
    path = '{}/{}'.format(PORT_DIR, name)
    result1 = flatpages.get_or_404(path)
    return render_template('result1.html', card=result1)

@app.route('/result4/')
def result4(name):
    path = '{}/{}'.format(DIR_RESULT4, name)
    result4 = flatpages.get_or_404(path)
    return render_template('result4.html', card=result4)


@app.route('/pygments.css')
def pygments_css():
    return pygments_style_defs('monokai'), 200, {'Content-Type': 'text/css'}



@app.route('/static/processing/ai_integration', methods=['POST'])
def ai_integration():
    from static.processing.ai_integration import analyze_w_file
    from static.processing.ai_integration import analyze_wo_file

    file = request.files.get('file')

    upload_folder = 'uploads'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    else:
        clear_folder(upload_folder)  # Очистить папку, но не удалять её

    if file and file.filename != '':
        file_path = os.path.join(upload_folder, file.filename)
        
        # Сохранение файла на сервере
        file.save(file_path)
        print(f"file из эпп: {file_path}")
        print("Привет я тут вывожу строку 1 раз, значит ai_integration отрабатывает первый раз")
        words = analyze_w_file(request.form, file_path)  # Вызов функции analyze_w_file из модуля
        print(words)
    else:
        words = analyze_wo_file(request.form)  # Вызов функции analyze из модуля
        print(words)

    # Очистка папки загрузок после выполнения анализа
    clear_folder(upload_folder)

    print("Привет я тут вывожу строку 2 раз, значит ai_integration отработала")
    return render_template('reports/result.html', words=words)

@app.route('/static/processing/WordCount', methods=['POST'])
def WordCount():
    import static.processing.WordCount 
    from static.processing.WordCount import main_function
    import logging
        # Настройка логирования
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    text_g = request.form.get('text')
    file = request.files.get('file')

        # Журналируем входные данные
    logging.info("Получен текст: %s", text_g)
    if file:
        logging.info("Получен файл: %s", file.filename)

    if text_g is None:
        return render_template('reports/result_1.html', result="Текст не введен")
    
    print(f"Text: {text_g}")
    print(f"File: {file.filename}")

    if file:
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
    else:
        return render_template('reports/result_1.html', result="Файл не выбран")

    user_list = text_g.split(',')
    result, relative_image_path, excel_file_path = main_function(file_path, user_list)
    result_table = result.replace('<th>', '<th style="text-align: left;">')
    #clear_folder(file_path)
    return render_template('reports/result_1.html', result=result_table, image_path=relative_image_path, excel_file_path=excel_file_path)


@app.route('/download/latest')
def download_latest():
    # Относительный путь к директории, где хранятся файлы
    download_folder = 'downloads'
    
    latest_file = get_latest_file(download_folder)
    if latest_file:
        return send_file(latest_file, as_attachment=True)
    else:
        return "No files found in the directory", 404

def get_latest_file(directory):
    abs_directory = os.path.abspath(directory)
    
    files = [os.path.join(abs_directory, f) for f in os.listdir(abs_directory) if os.path.isfile(os.path.join(abs_directory, f))]
    
    if not files:
        return None
    
    latest_file = max(files, key=os.path.getmtime)
    return latest_file


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        freezer.freeze()
    else:
        app.run(host='0.0.0.0', port=5006, debug=True)

