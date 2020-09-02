def delete_by_identifier(identifier: str) -> str:
    return f"DELETE FROM atividades WHERE id = {identifier}"


def insert(title: str, schedule: str, subject: str) -> str:
    return f"INSERT INTO atividades (id, titulo, data_agendamento, materia) " \
           f"VALUES (DEFAULT, '{title}', '{schedule}', '{subject}') "


create_table = "CREATE TABLE IF NOT EXISTS atividades ( id SERIAL, titulo VARCHAR(255) NOT NULL , data_agendamento " \
               "DATE NOT NULL , materia VARCHAR(255) NOT NULL , PRIMARY KEY(id) ); "

select_all = "SELECT * from atividades ORDER BY data_agendamento, materia, titulo;"
