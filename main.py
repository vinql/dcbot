import os

import discord
from dotenv import load_dotenv
from datetime import date

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
        try:
            self.cur.execute(sql)
            self.conn.commit()
            return True

        except psycopg2.Error:
            return False

    # Save an activity into the database
    def save_activity(self, title: str, schedule_date: str, subject: str) -> bool:

        try:
            self.cur.execute(
                f"INSERT INTO atividades (id, titulo, data_agendamento, materia) VALUES (DEFAULT, '{title}', "
                f"'{schedule_date}', '{subject}')")

            # Consolidate the changes
            self.conn.commit()

            return True

        except psycopg2.Error as err:
            print(f"Something went bad when trying to save to the database. This is what we got: \n{err}")
            return False

    # Retrieve all activities
    def retrieve_activities(self):
        try:
            response = "__**Lista de atividades**__\n"
            response += "```\n"

            self.cur.execute("SELECT * from atividades ORDER BY data_agendamento, materia, titulo;")
            records = self.cur.fetchall()

            if len(records) == 0:
                response = "__Não há nada agendado__"
                return response

            for row in records:
                response += f"{str(row[2])}  {row[3].ljust(8).upper()} {row[1]}\n"

            return response + "```"

        except psycopg2.Error as err:
            return f"**Ocorreu um erro ao acessar o banco de dados** :cry:\n\n```\n{err}```"


# Deals with the messages from the users
class StringParser:

    def __init__(self):
        self.database = DatabaseManager()

    def decode_message(self, message: str) -> str:
        command = message.split(" ")[0].lower()

        # Forward the message to the adequate function
        if command == "atividade" or command == "adicionar" or command == "add":
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

        # Schedule is expected to be as dd/mm/yyyy or dd/mm
        # Either way, it must be converted to SQL format yyyy-mm-dd
        if schedule:
            aux = schedule.split("/")
            day = aux[0].rjust(2, '0')
            month = aux[1].rjust(2, '0')

            if len(aux) == 3 and len(aux[2]) >= 2:
                year = aux[2]
            else:
                # Infer the year. The current or the next one
                today = date.today()

                passed = int(month) < today.month or (int(month) == today.month and int(day) < today.day)
                year = str(today.year + 1) if passed else str(today.year)

            schedule = f"{year}-{month}-{day}"

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
            if self.database.save_activity(title, schedule, subject):
                # I am fully aware that this is a cursed way to insert emojis
                return f"Matéria salva no banco de dados 😎🎲\n" \
                       f"Dia {schedule}, ({subject}) {title}"
            else:
                return "*Ocorreu um erro ao salvar a matéria no banco de dados* :cry:"
        else:
            return response

    @staticmethod
    def new_avaliation(message: str):
        return f"Avaliação {message}"


class DcUfscarBot(discord.Client):

    def __init__(self, **options):
        super().__init__(**options)
        self.parser = StringParser()
        self.database = DatabaseManager()

    async def on_ready(self):
        self.database.init_database()
        self.database.__del__()

        print(f'{self.user} has connected to Discord!')
        vi = self.guilds[0]

        print(vi)

        for member in vi.members:
            print(member)

    async def on_message(self, message):
        if message.author.id != self.user.id:
            await message.channel.send(self.parser.decode_message(message.content))


# Runs the bot
client = DcUfscarBot()
client.run(TOKEN)
