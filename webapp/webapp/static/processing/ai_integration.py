from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import openai
import os
import time
from openai import OpenAI

app = Flask(__name__)
client = OpenAI(api_key="sk-proj-")
value_assistant = "asst_"

text1 = request.form.get('text1', '')  # Получение данных из первого текстового поля
text2 = request.form.get('text2', '')  # Получение данных из второго текстового поля
file = request.files.get('file')  # Получение загруженного файла

final_input = text1 + ". " + text2  # Объединение данных из полей ввода


def check_thread_status(thread_id, run_id_PEREMEN):
    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id_PEREMEN)
        thread_status = run.status
        print("Статус треда:", thread_status)

        if thread_status == 'completed':
            return run

        time.sleep(2)  # Ждем 2 секунды перед следующей проверкой

# Функция для загрузки файла
def file_upload(file_content):
    try:
        with open(file_content, "rb") as file:
            response = client.files.create(
                file=file,
                purpose="assistants"
            )
        file_id = response.id
        print(f"Файл успешно загружен с ID: {file_id}")
        return file_id
    except FileNotFoundError:
        print("Файл не найден. Пожалуйста, укажите корректный путь к файлу.")

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

def create_empty_thread(final_input):
    empty_thread = client.beta.threads.create()
    thread_id = empty_thread.id
    print("Параметры запущенного треда:", thread_id)
    thread_message = client.beta.threads.messages.create(thread_id, role="user", content=final_input)
    return thread_id

def create_empty_thread_with_file(final_input, file_content):
    empty_thread = client.beta.threads.create()
    thread_id = empty_thread.id
    print("Параметры запущенного треда:", thread_id)
    thread_message = client.beta.threads.messages.create(
        thread_id,
        role="user",
        content=final_input,
        attachments=[{"file_id": file_content, "tools": [{"type": "file_search"}]}]
    )
    return thread_id

def delete_file(file_id):
    # """ Удаление файла по ID через API """
    try:
        client.files.delete(file_id)
        print(f"Файл {file_id} успешно удален")
    except Exception as e:
        print(f"Ошибка при удалении файла {file_id}: {e}")

def start_thread_run(thread_id, value_assistant):
    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=value_assistant)
    run_id_PEREMEN = run.id
    thread_id = run.thread_id
    thread_status = run.status
    print("Статус обработки треда:", thread_status)
    return run_id_PEREMEN

def analyze_w_file(form, file_path):
    try:
        final_input = form.get('text1', '') + ". " + form.get('text2', '')
        print(f"text1: {form.get('text1', '')}")
        print(f"text2: {form.get('text2', '')}")
        print(f"file до конвертации: {file_path}")
        
        txt_file_path = convert_to_txt(file_path)
        if not txt_file_path:
            raise ValueError("Файл не был конвертирован.")

        file_id = file_upload(txt_file_path)
        if not file_id:
            raise ValueError("Файл не был загружен на сервер.")

        print(f"Файл после конвертации: {txt_file_path}")
        print(f"file id: {file_id}")

        thread_id = create_empty_thread_with_file(final_input, file_id)
        run_id_PEREMEN = start_thread_run(thread_id, value_assistant)
        run_result = check_thread_status(thread_id, run_id_PEREMEN)

        thread_messages = client.beta.threads.messages.list(thread_id)
        if thread_messages.data:
            last_message = thread_messages.data[0]
            result = last_message.content[0].text.value
        else:
            result = "Нет сообщений в треде"
        #print(file_id)
        delete_file(file_id)

        print("Привет из analyze_w_file")
        return result

    except Exception as e:
        print(f"Ошибка в analyze_w_file: {e}")
        return str(e)

def analyze_wo_file(form):

    # Проверяем, что данные корректно извлечены
    print(f"text1: {text1}")  
    print(f"text2: {text2}")  
    

    # Объединение данных из полей ввода
    final_input = form.get('text1', '') + ". " + form.get('text2', '')
    print("Я вылезаю без фалйа из функции")
    thread_id = create_empty_thread(final_input)

    # Запуск выполнения и проверка статуса
    run_id_PEREMEN = start_thread_run(thread_id, value_assistant)
    run_result = check_thread_status(thread_id, run_id_PEREMEN)

    # Получение сообщений из потока
    thread_messages = client.beta.threads.messages.list(thread_id)

    if thread_messages.data:
        last_message = thread_messages.data[0]
        result = last_message.content[0].text.value  # Получение результата анализа
    else:
        result = "Нет сообщений в треде"
        
    print("Привет из analyze_wo_file")
    return result
