import os

import discord
import psycopg2
import queries as queries
from dotenv import load_dotenv
from datetime import date

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
        sql = queries.create_table
        try:
            self.cur.execute(sql)
            self.conn.commit()
            return True

        except psycopg2.Error:
            return False

    # Save an activity into the database
    def save_activity(self, title: str, schedule_date: str, subject: str) -> bool:

        try:
            self.cur.execute(queries.insert(title, schedule_date, subject))

            # Consolidate the changes
            self.conn.commit()

            print("This happened")
            return True

        except psycopg2.Error as err:
            print(f"Something went bad when trying to save to the database. This is what we got: \n{err}")
            return False

    def delete_activity(self, identifier: str):
        try:
            self.cur.execute(queries.delete_by_identifier(identifier))

            # Consolidate the changes
            self.conn.commit()

            return True

        except psycopg2.Error as err:
            print(f"Something went bad when trying to save to the database. This is what we got: \n{err}")
            return False

    # Retrieve all activities
    def retrieve_activities(self, full_result: bool = False):
        try:
            response = "__**Lista de atividades**__\n"
            response += "```\n"

            self.cur.execute(queries.select_all)
            records = self.cur.fetchall()

            if len(records) == 0:
                response = "__Não há nada agendado__"
                return response

            for row in records:
                if full_result:
                    response += f"[{row[0]}] "
                response += f"{str(row[2])}  {row[3].ljust(8).upper()} {row[1]}\n"

            return response + "```"

        except psycopg2.Error as err:
            return f"**Ocorreu um erro ao acessar o banco de dados** :cry:\n\n```\n{err}```"


# Deals with the messages from the users
class CommandParser:

    def __init__(self):
        self.database = DatabaseManager()

    def decode_message(self, message: str):
        command = message.split(" ")[0].lower()

        # Forward the message to the adequate function
        if command == "atividade" or command == "adicionar" or command == "add":
            return self.new_activity(message)

        elif command == "ls" or command == "atividades":
            return self.database.retrieve_activities(full_result=True) if "-a" in message \
                else self.database.retrieve_activities()

        elif command == "del" or command == "deletar":
            return self.delete_activity(message)

        elif command == "prova":
            return self.new_avaliation(message)

        return False

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

            # User did inform the year
            if len(aux) == 3 and len(aux[2]) >= 2:
                year = aux[2]
            # User did not inform the year
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

    def delete_activity(self, message: str):
        aux = message.split()
        row_id = False if len(aux) != 2 else aux[1]

        return True if row_id and self.database.delete_activity(row_id) else False

    @staticmethod
    def new_avaliation(message: str):
        return f"Avaliação {message}"


class DcUfscarBot(discord.Client):

    def __init__(self, **options):
        super().__init__(**options)
        self.parser = CommandParser()
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
            response = self.parser.decode_message(message.content)

            if response:
                await message.channel.send(response)


# Runs the bot
client = DcUfscarBot()
client.run(TOKEN)
