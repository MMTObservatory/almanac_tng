FROM continuumio/miniconda3

LABEL maintainer="te_pickering@gmail.com"

ARG USER_ID
ARG GROUP_ID

RUN apt update && apt -y upgrade

RUN apt -y install emacs procps
RUN conda update -y -n base -c defaults conda && conda update -y --all

RUN conda install -y astropy pandas seaborn matplotlib jupyterlab nodejs ipympl astroplan -c astropy

RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager jupyter-matplotlib

RUN conda clean -y --all

RUN pip install skyfield

RUN groupadd -f -g ${GROUP_ID} almanac && \
    useradd -l -u ${USER_ID} -g almanac almanac

RUN mkdir -p /home/almanac && chown -R almanac:almanac /home/almanac

EXPOSE 9919

USER almanac

ENV HOME /home/almanac

ENTRYPOINT ["jupyter", "lab", "--ip='*'", "--port=9919", "--no-browser"]
CMD ["--notebook-dir=/home/almanac/almanac/notebooks"]
