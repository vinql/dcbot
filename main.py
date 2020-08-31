import os

import discord
from dotenv import load_dotenv

import psycopg2

# Loads the env variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
SCHEMA = os.getenv('DATABASE')


class DatabaseManager:

    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        self.cur = self.conn.cursor()

    def __del__(self):
        self.conn.close()

    # Initializes the database
    def init_database(self):
        sql = "CREATE TABLE IF NOT EXISTS atividades ( id SERIAL, titulo VARCHAR(255) NOT NULL , data_agendamento " \
              "DATE NOT NULL , materia VARCHAR(255) NOT NULL , PRIMARY KEY(id) ); "
        self.cur.execute(sql)

    # Save a activity to the database
    def save_activity(self, title: str, schedule_date: str, subject: str) -> bool:

        try:
            self.cur.execute(
                f"INSERT INTO atividades (id, titulo, data_agendamento, materia) VALUES (DEFAULT, '{title}', "
                f"'{schedule_date}', '{subject}')")

            # Consolidate the changes
            self.conn.commit()

            return True

        except psycopg2.Error:
            return False

    # Retrieve all activities
    def retrieve_activities(self):
        try:
            response = "__**Lista de atividades**__\n"
            response += "```\n"

            self.cur.execute("SELECT * from atividades ORDER BY data_agendamento;")
            records = self.cur.fetchall()

            for row in records:
                response += f"{str(row[2])} ({row[3]}) {row[1]}\n"


            return response + "```"

        except psycopg2.Error:
            return False


# Deals with the messages from the users
class StringParser:

    def __init__(self):
        self.database = DatabaseManager()

    def decode_message(self, message: str) -> str:
        command = message.split(" ")[0].lower()

        # Forward the message to the adequate function
        if command == "atividade":
            return self.new_activity(message)

        elif command == "ls" or command == "atividades":
            return self.all_activities()

        elif command == "prova":
            return self.new_avaliation(message)

        return command.lower()

    def all_activities(self):
        return self.database.retrieve_activities()

    def new_activity(self, message: str):
        # atividade -t alguma coisa -d 10/01/2020 -m SO
        aux = message.split("-t ")
        title = False if len(aux) < 2 else (aux[1].split(" -")[0])

        aux = message.split("-d ")
        schedule = False if len(aux) < 2 else (aux[1].split(" -")[0])

        aux = message.split("-m ")
        subject = False if len(aux) < 2 else (aux[1].split(" -")[0])

        response = ""
        if not title:
            response += "Por favor, informe o **título** da atividade usando `-t titulo da atividade`\n"

        if not schedule:
            response += "Por favor, informe a **data de entrega** da atividade usando `-d dd/mm/aaaa`\n"

        if not subject:
            response += "Por favor, informe a **matéria** da atividade usando `-m AED1`\n"

        if title and schedule and subject:
            self.database.save_activity(title, schedule, subject)
            return "Matéria salva no banco de dados 😎🎲"
        else:
            return response

    @staticmethod
    def new_avaliation(message: str):
        return f"Avaliação {message}"


class DcUfscarBot(discord.Client):

    def __init__(self, **options):
        super().__init__(**options)
        self.parser = StringParser()

    @staticmethod
    async def on_ready():
        print(f'{client.user} has connected to Discord!')
        vi = client.guilds[0]

        print(vi)

        for member in vi.members:
            print(member)

    async def on_message(self, message):
        if message.author.id != client.user.id:
            await message.channel.send(self.parser.decode_message(message.content))


# Initializes the database
manager = DatabaseManager()
manager.init_database()

# Runs the bot
client = DcUfscarBot()
client.run(TOKEN)
