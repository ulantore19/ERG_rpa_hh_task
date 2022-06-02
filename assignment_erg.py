from bs4 import BeautifulSoup
import requests
import sqlite3
import time
from random import choice


def get_soup(url, user_agent):
    # Добавление временных промежутков, чтобы не перегружать сервер
    time.sleep(2)
    headers = {"User-Agent": user_agent}
    time.sleep(2)
    page = requests.get(url, headers=headers).text
    time.sleep(2)
    sp = BeautifulSoup(page, "lxml")
    return sp


def get_skills(sp):
    '''Возвращает строку необходимых навыков для вакансии и вид трудоустройства из полученного 'супа'.  '''

    vacancy_description = sp.select(
        "div.main-content div[class='bloko-columns-row']")
    list_of_skills = list()

    for content in vacancy_description:
        try:
            key_skills = content.find("div", attrs={"class": "bloko-tag-list"})

            if key_skills is None:
                break  # Если массив навыков пуст, то переходим другому контенту

            for skill in key_skills:
                if skill not in list_of_skills:
                    # Добавляем только новые навыки в массив
                    list_of_skills.append(skill.text)
        except BaseException:
            pass

    # Возвращаем как сроку состоящий из навыков
    return ", ".join(list_of_skills)


def get_exp_and_employment_mode(sp):
    '''Возвращает фичи как опыт и вид трудоустройства из полученного 'супа'. '''

    vacancy_description = sp.select(
        "div.main-content div[class='vacancy-description']")
    exp_type = list()

    for content in vacancy_description:
        experience = content.find(
            "div", attrs={
                "class": "bloko-gap bloko-gap_bottom"}).span.text
        mode = content.find(
            "p", attrs={
                "data-qa": "vacancy-view-employment-mode"}).text

        return (experience, mode)  # Возвращаем только первые значения


def create_db(db_name):
    '''Функция создает базу данных с таблицей 'Jobs'. '''

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS JOBS")

    table = """CREATE TABLE JOBS (
    TITLE VARCHAR(255) NOT NULL,
    COMPANY VARCHAR(255) NOT NULL,
    SALARY VARCHAR(255),
    LOCATION VARCHAR(255),
    KEY_SKILLS VARCHAR(255),
    LINK VARCHAR(255),
    EXPERIENCE VARCHAR(128),
    MODE VARCHAR(255)
    );
    """
    cur.execute(table)

    conn.commit()
    conn.close()


def main(url, db_name, user_agent):
    conn = sqlite3.connect(db_name)  # Открываем дата базу
    cur = conn.cursor()

    soup = get_soup(url, user_agent=user_agent)
    jobs = soup.select(
        "div.vacancy-serp-content div[class='vacancy-serp-item']"
    )

    for job in jobs:
        vacancy = job.find(
            "div", class_='vacancy-serp-item-body')  # ячейка вакансии

        title = vacancy.h3.text
        link = vacancy.h3.find("a", href=True)['href']

        # Проверяем указано ли зарплата
        try:
            salary = vacancy.find(
                attrs={
                    'data-qa': 'vacancy-serp__vacancy-compensation'}).text
        except BaseException:
            salary = "З/п договорная"

        location = vacancy.find(
            attrs={'data-qa': "vacancy-serp__vacancy-address"}).text
        company = vacancy.find(
            "div", class_="vacancy-serp-item__meta-info-company").a.text

        # получаем доп. информацию о вакансии переходя по ссылке ячейки
        # получаем суп, где полная информация о вакансии
        soup_of_link = get_soup(link, user_agent=user_agent)
        key_skills = get_skills(soup_of_link)
        experience, emp_mode = get_exp_and_employment_mode(soup_of_link)

        # Вставляем полученные фичи в дата базу
        insert_query = """INSERT INTO JOBS (TITLE, COMPANY, SALARY, LOCATION, KEY_SKILLS, LINK, EXPERIENCE, MODE)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?);
        """
        cur.execute(
            insert_query,
            (title,
             company,
             salary,
             location,
             key_skills,
             link,
             experience,
             emp_mode
            )
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":

    # код будет рандомно выбирать пользовательский агент, чтобы выдержать проверку на бота
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "AppleWebKit/537.36 (KHTML, like Gecko)",
        "Chrome/101.0.0.0", "Safari/537.36", "Chrome/101.0.4951.67"
    ]
    agent = choice(user_agents)

    url = "https://hh.kz/search/vacancy?area=160&search_field=name&search_field=company_name&search_field=description" \
          "&text=python&from=suggest_post&hhtmFrom=vacancy_search_list" + "&items_per_page=40 "
    db_name = "ass_test.db"

    create_db(db_name)
    main(url, db_name, agent)
