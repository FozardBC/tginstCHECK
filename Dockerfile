# Этап сборки (исправлено: единообразное написание 'as')
FROM python:3.9-slim AS builder

WORKDIR /app
COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

# Финальный этап
FROM python:3.9-slim

WORKDIR /app

# Копируем установленные зависимости из builder
COPY --from=builder /root/.local /root/.local
COPY bot.py .

# Создаем директорию для загрузок
RUN mkdir -p downloads

# Убедимся, что скрипты в .local доступны
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV DOWNLOAD_DIR=/app/downloads


# Запускаем бота
CMD ["python", "bot.py", "7851957608:AAHasR95vqt_Vg7_ZZKQEXq4Nl6D8tq6Wlc"]