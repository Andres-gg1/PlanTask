#PYTHON IMAGE
FROM python:3.11-slim

#SYSTEM DEPENDENCIES
RUN apt-get update && apt-get install -y gcc libpq-dev

#WORKING DIRECTORY
WORKDIR /app

#COPIES THE PROYECT CONTENT
COPY . /app

#INSTALL DEPENDENCIES
RUN pip install --upgrade pip
RUN pip install -e .[dev]

#EXPOSES THE PORT
EXPOSE 6543

#STARTS THE SERVER
CMD ["pserve", "production.ini"]
