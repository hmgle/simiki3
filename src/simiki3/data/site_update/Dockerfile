FROM python:3.12-slim

WORKDIR /site

COPY . /site
RUN python -m pip install --no-cache-dir simiki3
RUN simiki3 build /site

CMD ["simiki3", "serve", "/site", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000
