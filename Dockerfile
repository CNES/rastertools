FROM continuumio/miniconda3

ADD environment.yml /env/environment.yml
ADD env_update.yml /env/env_update.yml

RUN conda env update -f /env/environment.yml -n base
RUN conda env update -f /env/env_update.yml -n base

ADD . .

RUN pip install -e .

CMD ["rastertools", "--help"]
