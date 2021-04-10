FROM python:3.9.2
ENV TZ="Europe/Moscow"
COPY . .
WORKDIR /petbot/
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
EXPOSE 5432
CMD ["python", "pr_kotleta.py"]