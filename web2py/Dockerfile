FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install --yes apt-utils curl p7zip-full aria2 postgresql-client wget git

RUN groupadd --gid 1050 microservices && useradd --uid 1050 --gid microservices --create-home microservices

RUN python3 -m pip install --no-cache -e git+https://github.com/web2py/web2py@v2.27.1#egg=web2py

COPY requirements.txt /w2p/requirements.txt
RUN python3 -m pip install --no-cache -r /w2p/requirements.txt

# chdir to the directory where password and apps folder is, this is the base
# directory from which to start py4web.
WORKDIR  /src/web2py
RUN cp -r applications/admin applications/w2p_admin 
RUN chown microservices:microservices -R ./
RUN chmod 776 -R ./
# expose py4web on it's default port
EXPOSE 8000
# -K : run scheduled tasks for specified apps
# -X : run scheduler alongside webserver
# both are required...
USER microservices
CMD python3 web2py.py -a ${WEB2PY_PASSWORD|test} -i "0.0.0.0" -p 8000 -K init -X --min_threads 5 --max_threads=15
