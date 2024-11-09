FROM python:3.8

# copy the requirements file into the image
COPY ./requirements.txt /app/requirements.txt
# switch working directory
WORKDIR /app
# install the dependencies and packages in the requirements file
RUN pip install python-dateutil
RUN pip install numpy scipy pandas
RUN pip install -r requirements.txt
RUN pip install nltk
RUN pip install inspect2
RUN pip install --upgrade nltk

RUN python3 -m nltk.downloader punkt
RUN python3 -m nltk.downloader wordnet
RUN python3 -m nltk.downloader stopwords
RUN python3 -m nltk.downloader all
#RUN nltk.download('all')
# copy every content from the local file to the image
COPY . /app
# configure the container to run in an executed manner
ENTRYPOINT ["python"]
CMD ["app.py"]